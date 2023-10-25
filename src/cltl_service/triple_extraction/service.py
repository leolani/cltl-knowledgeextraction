import logging
from typing import List

from cltl.combot.event.emissor import ScenarioStarted, ScenarioStopped, ScenarioEvent, Agent, ConversationalAgent
from cltl.combot.infra.config import ConfigurationManager
from cltl.combot.infra.event import Event, EventBus
from cltl.combot.infra.groupby_processor import GroupProcessor, Group, GroupByProcessor
from cltl.combot.infra.resource import ResourceManager
from cltl.combot.infra.time_util import timestamp_now
from cltl.combot.infra.topic_worker import TopicWorker
from emissor.representation.scenario import TextSignal, Mention
from cltl_service.emissordata.client import EmissorDataClient

from cltl.triple_extraction.analyzer import Analyzer
from cltl.triple_extraction.api import Chat, DialogueAct

logger = logging.getLogger(__name__)


class UtteranceGroup(Group):
    def __init__(self, utterance_id: str, input_topics: List[str], dialogue_act_topic: str):
        super().__init__()
        self._input_topics = set(input_topics)
        self._dialogue_act_topic = dialogue_act_topic

        self._signal_id = utterance_id
        self._text_signal = None
        self._dialogue_acts = None

    @property
    def text_signal(self):
        return self._text_signal

    @property
    def dialogue_acts(self):
        return self._dialogue_acts

    @property
    def key(self) -> str:
        return self._signal_id

    @property
    def complete(self) -> bool:
        return self._text_signal is not None and self._dialogue_acts is not None

    def add(self, event: Event):
        if event.metadata.topic in self._input_topics:
            self._text_signal = event.payload.signal
        elif event.metadata.topic == self._dialogue_act_topic:
            self._set_dialogue_acts(event.payload.mentions)

    def _set_dialogue_acts(self, mentions: List[Mention]):
        has_dialogue_acts = len(mentions) == 1 and mentions[0].annotations and mentions[0].annotations[0].value
        logger.debug("Received %s dialog acts for utterance %s", "" if has_dialogue_acts else "no ", self._signal_id)

        if not has_dialogue_acts:
            self._dialogue_acts = []
        else:
            dialogue_acts = [mention.annotations[0] for mention in mentions]
            self._dialogue_acts = [self._extract_dialogue_act(act) for act in dialogue_acts]

    def _extract_dialogue_act(self, dialogue_act):
        if (dialogue_act.value.type.lower() == 'midas' and dialogue_act.value.value.lower().startswith('open_question')
            or dialogue_act.value.type.lower() == 'silicone' and dialogue_act.value.value.lower() == 'ask'):
            return  DialogueAct.QUESTION
        else:
            return  DialogueAct.STATEMENT


class TripleExtractionService(GroupProcessor):
    @classmethod
    def from_config(cls, extractor: Analyzer, emissor_client: EmissorDataClient, event_bus: EventBus, resource_manager: ResourceManager,
                    config_manager: ConfigurationManager):
        config = config_manager.get_config("cltl.triple_extraction")

        agent_topic = config.get("topic_agent") if "topic_agent" in config else None
        dialogue_act_topic = config.get("topic_dialogue_act") if "topic_dialogue_act" in config else None

        return cls(config.get("topic_input"), agent_topic, dialogue_act_topic, config.get("topic_output"),
                   config.get("topic_scenario"), config.get("topic_intention"), config.get("intentions", multi=True),
                   extractor, emissor_client, event_bus, resource_manager)

    def __init__(self, input_topic: str, agent_topic: str, dialogue_act_topic: str, output_topic: str, scenario_topic: str,
                 intention_topic: str, intentions: List[str], extractor: Analyzer,
                 emissor_client: EmissorDataClient, event_bus: EventBus, resource_manager: ResourceManager):
        self._extractor = extractor

        self._event_bus = event_bus
        self._resource_manager = resource_manager

        self._input_topic = input_topic
        self._dialogue_act_topic = dialogue_act_topic
        self._output_topic = output_topic
        self._agent_topic = agent_topic
        self._scenario_topic = scenario_topic

        self._intention_topic = intention_topic if intention_topic else None
        self._intentions = set(intentions) if intentions else {}
        self._active_intentions = set()

        self._topic_worker = None
        self._emissor_client = emissor_client
        self._chat = None
        self._speaker = Agent()
        self._agent = Agent()

        self._dialog_aware_processor = GroupByProcessor(self, max_size=4, buffer_size=16)

    @property
    def app(self):
        return None

    def start(self, timeout=30):
        topics = [self._input_topic, self._scenario_topic, self._intention_topic]
        if self._dialogue_act_topic:
            topics += [self._dialogue_act_topic]
        if self._agent_topic:
            topics += [self._agent_topic]

        self._topic_worker = TopicWorker(topics, self._event_bus, provides=[self._output_topic],
                                         resource_manager=self._resource_manager, processor=self._process,
                                         buffer_size=64,
                                         name=self.__class__.__name__)
        self._topic_worker.start().wait()

    def stop(self):
        if not self._topic_worker:
            pass

        self._topic_worker.stop()
        self._topic_worker.await_stop()
        self._topic_worker = None

    def _process(self, event: Event):
        if event.metadata.topic == self._intention_topic:
            self._active_intentions = set(event.payload.intentions)
            logger.info("Set active intentions to %s", self._active_intentions)
            return

        if event.metadata.topic == self._scenario_topic:
            self._update_chat(event)
            return

        if self._intentions and not (self._active_intentions.intersection(self._intentions)):
            logger.debug("Skipped event outside intention %s, active: %s (%s)",
                         self._intentions, self._active_intentions, event)
            return

        if not self._chat:
            logger.warning("Received utterance outside of a chat (%s)", event)
            return

        if self._dialogue_act_topic:
            self._dialog_aware_processor.process(event)
        else:
            self._process_last_utterance(event.payload.signal)

    def _process_last_utterance(self, text_signal: TextSignal, dialogue_act: DialogueAct = None):
        is_agent = any(self._get_name(annotation).lower() == ConversationalAgent.LEOLANI.name.lower()
                       for mention in text_signal.mentions
                       for annotation in mention.annotations
                       if annotation.type == ConversationalAgent.__name__)

        self._chat.add_utterance(text_signal.text, self._chat.agent if is_agent else self._chat.speaker, dialogue_act)

        if is_agent:
            # Add robot utterances to the chat without triple extraction
            return

        self._extractor.analyze_in_context(self._chat)
        response = self._utterance_to_capsules(self._extractor.utterance, text_signal)

        if response:
            # TODO: transform capsules into proper EMISSOR annotations
            self._event_bus.publish(self._output_topic, Event.for_payload(response))
            logger.debug("Published %s triples for signal %s (%s): %s",
                         len(response), text_signal.id, text_signal.text, response)
        else:
            logger.debug("No triples for signal %s (%s)", text_signal.id, text_signal.text)

        scenario_id = self._emissor_client.get_current_scenario_id()

        ### The next code gives feedback on processing the conversation.
        from random import choice
        from cltl.combot.infra.time_util import timestamp_now
        from cltl.combot.event.emissor import TextSignalEvent
        from emissor.representation.scenario import TextSignal
        if response:
            self._event_bus.publish(self._output_topic, Event.for_payload(response))
            logger.debug("Published %s triples for signal %s (%s): %s",
                         len(response), text_signal.id, text_signal.text, response)
            triple = ""
            for ch in response:
            	triple+= "("+ch['subject']['label']+", "+ch['predicate']['label']+", "+ch['object']['label']+') '
            I_SEE = ["I see. This is what I got from what you said: ", "I got it. So you are claiming: ", "Ok, so: ", "So interesting what you said. It boils down to: "]
            utterance =  f"{choice(I_SEE)} {triple}"
            signal = TextSignal.for_scenario(scenario_id, timestamp_now(), timestamp_now(), None, utterance)
            self._event_bus.publish("cltl.topic.text_out", Event.for_payload(TextSignalEvent.for_agent(signal)))
        else:
            logger.debug("No triples for signal %s (%s)", text_signal.id, text_signal.text)
            I_SEE = ["I see. Cannot make much of what you said.", "I hear you but it does not make sense to me.", "Ok, interesting but too much for me. What else?", "What are you trying to say? I am just a humble AI, please try again.", "Sorry, I did not get that."]
            utterance =  f"{choice(I_SEE)}"
            signal = TextSignal.for_scenario(scenario_id, timestamp_now(), timestamp_now(), None, utterance)
            self._event_bus.publish("cltl.topic.text_out", Event.for_payload(TextSignalEvent.for_agent(signal)))


    def get_key(self, event: Event):
        key = None
        if event.metadata.topic in [self._input_topic, self._agent_topic]:
            key = event.payload.signal.id
        elif event.metadata.topic == self._dialogue_act_topic:
            key = next(segment.container_id
                    for mention in event.payload.mentions
                    for segment in mention.segment)

        if not key:
            raise ValueError("Could not extract key from event: " + event.id)

        return key

    def new_group(self, key: str) -> Group:
        return UtteranceGroup(key, [self._input_topic, self._agent_topic], self._dialogue_act_topic)

    def process_group(self, group: UtteranceGroup):
        self._process_last_utterance(group.text_signal, group.dialogue_acts)

    def _get_name(self, agent_annotation):
        if isinstance(agent_annotation.value, str):
            return agent_annotation.value
        if isinstance(agent_annotation.value, ConversationalAgent):
            return agent_annotation.value.name

        raise ValueError("Cannot parse annotation value " + str(agent_annotation))

    def _update_chat(self, event):
        if event.payload.scenario.context.agent:
            self._agent = event.payload.scenario.context.agent
        if event.payload.scenario.context.speaker:
            self._speaker = event.payload.scenario.context.speaker

        if event.payload.type == ScenarioStarted.__name__:
            agent_name = self._agent.name if self._agent.name else "Leolani"
            speaker_name = self._speaker.name if self._speaker and self._speaker.name else "Stranger"
            self._chat = Chat(agent_name, speaker_name)
            logger.debug("Started chat with speaker %s, agent %s", self._chat.speaker, self._chat.agent)
        elif event.payload.type == ScenarioStopped.__name__:
            logger.debug("Stopping chat with %s, agent %s", self._chat.speaker, self._chat.agent)
            self._chat = None
            self._speaker = None
            self._agent = None
        elif event.payload.type == ScenarioEvent.__name__:
            if self._speaker.name and self._speaker.name != self._chat.speaker:
                self._chat.speaker = self._speaker.name
                logger.debug("Set speaker in chat to %s", self._chat.speaker)
            if self._agent.name and self._agent.name != self._chat.agent:
                self._chat.agent = self._agent.name
                logger.debug("Set agent in chat to %s", self._chat.agent)

    def _utterance_to_capsules(self, utterance, signal):
        capsules = []

        for triple in utterance.triples:
            self._add_uri_to_triple(triple)
            scenario_id = signal.time.container_id

            capsule = {"chat": scenario_id,
                       "turn": signal.id,
                       "author": self._get_author(),
                       "utterance": utterance.transcript,
                       "utterance_type": triple['utterance_type'],
                       "position": "0-" + str(len(utterance.transcript)),
                       ###
                       "subject": triple['subject'],
                       "predicate": triple['predicate'],
                       "object": triple['object'],
                       "perspective": triple["perspective"],
                       ###
                       "context_id": scenario_id,
                       "timestamp": timestamp_now()
                       }

            capsules.append(capsule)

        return capsules

    def _add_uri_to_triple(self, triple: dict):
        uri = {'uri':None}
        triple['subject'].update(uri)
        triple['predicate'].update(uri)
        triple['object'].update(uri)

    #@TODO check if this needs to be the TextSignal source
    def _get_author(self):
        return {
            "label": self._speaker.name if self._speaker and self._speaker.name else self._chat.speaker,
            "type": ["person"],
            "uri": self._speaker.uri if self._speaker else None
        }
