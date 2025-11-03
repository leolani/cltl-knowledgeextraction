import logging
from collections import defaultdict
from typing import List

from cltl.combot.event.emissor import ScenarioStarted, ScenarioStopped, ScenarioEvent, Agent, ConversationalAgent
from cltl.combot.infra.config import ConfigurationManager
from cltl.combot.infra.event import Event, EventBus
from cltl.combot.infra.event.util import extract_scenario_id
from cltl.combot.infra.groupby_processor import GroupProcessor, Group, GroupByProcessor
from cltl.combot.infra.resource import ResourceManager
from cltl.combot.infra.time_util import timestamp_now
from cltl.combot.infra.topic_worker import TopicWorker
from emissor.representation.scenario import TextSignal, Mention
from cltl_service.emissordata.client import EmissorDataClient
from cltl.commons.discrete import UtteranceType, Polarity, Certainty
from cltl.triple_extraction.analyzer import Analyzer
from cltl.triple_extraction.api import Chat, DialogueAct
## The next code gives feedback on processing the conversation.
from random import choice
from cltl.combot.infra.time_util import timestamp_now
from cltl.combot.event.emissor import TextSignalEvent

logger = logging.getLogger(__name__)

I_SEE = ["I see. This is what I got from what you said: ", "I got it. So you are claiming: ", "Ok, so: ",
         "So interesting what you said. It boils down to: "]
I_DONT_SEE = ["I see. Cannot make much of what you said.", "I hear you but it does not make sense to me.",
              "Ok, interesting but too much for me. What else?",
              "What are you trying to say? I am just a humble AI, please try again.",
              "Sorry, I did not get that."]
YOU_ASK = ["I see. This is what I got from what you ask: ", "I got it. So you are asking: ", "Ok, so: ",
           "So interesting, so you want to know "]
GREETINGS = ["Please tell me anything new!", "What's up!", "Tell me something.",
             "I have not been outside lately. What is going on?"]
greet_words = ["hi", "hello", "how are you", "how do you do", "hello", "good day", "good morning", "good evening", "greetings", "yo"]
BYES = ["Great talking to you!", "See you soon!", "Have a great day.", "Get back soon!", "Gonna miss you."]
bye_words = ["bye", "goodbye", "have a nice day", "stop", "have to leave", "cheers", "see you next time", "see you"]


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
            return DialogueAct.QUESTION
        else:
            return DialogueAct.STATEMENT


class TripleExtractionService(GroupProcessor):
    @classmethod
    def from_config(cls, extractor: Analyzer, emissor_client: EmissorDataClient, event_bus: EventBus,
                    resource_manager: ResourceManager,
                    config_manager: ConfigurationManager):
        config = config_manager.get_config("cltl.triple_extraction")
        feedback = bool(config.get_boolean("feedback")) if "feedback" in config else False
        agent_topic = config.get("topic_agent") if "topic_agent" in config else None
        dialogue_act_topic = config.get("topic_dialogue_act") if "topic_dialogue_act" in config else None
        topic_input = config.get("topic_input")
        topic_output = config.get("topic_output")
        topic_intention = config.get("topic_intention") if "topic_intention" in config else None
        intentions = config.get("intentions", multi=True) if "intentions" in config else []
        topic_scenario = config.get("topic_scenario") if "topic_scenario" in config else None

        return cls(topic_input, agent_topic, dialogue_act_topic, topic_output,
                   topic_scenario, topic_intention, intentions,
                   extractor, emissor_client, event_bus, resource_manager, feedback=feedback)

    def __init__(self, input_topic: str, agent_topic: str, dialogue_act_topic: str, output_topic: str,
                 scenario_topic: str,
                 intention_topic: str, intentions: List[str], extractor: Analyzer,
                 emissor_client: EmissorDataClient, event_bus: EventBus, resource_manager: ResourceManager, feedback:bool):
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

        self._chat = dict()
        self._speaker = defaultdict(Agent)
        self._agent = defaultdict(Agent)

        self._dialog_aware_processor = GroupByProcessor(self, max_size=4, buffer_size=16)
        self._feedback = False

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
            self._active_intentions = {intention.label for intention in event.payload.intentions}
            logger.info("Set active intentions to %s", self._active_intentions)
            return

        if event.metadata.topic == self._scenario_topic:
            self._update_chat(event)
            return

        if self._intentions and not (self._active_intentions.intersection(self._intentions)):
            logger.debug("Skipped event outside intention %s, active: %s (%s)",
                         self._intentions, self._active_intentions, event)
            return

        if event.metadata.scenario_id and event.metadata.scenario_id not in self._chat:
            logger.warning("Received utterance outside of a chat (%s)", event)
            return

        if self._dialogue_act_topic:
            # TODO support multiple scenarios for GroupByProcessor
            raise NotImplementedError("Multiple scenarios are not supported")
            self._dialog_aware_processor.process(event)
        else:
            self._process_last_utterance(event.payload.signal, event)

    def _process_last_utterance(self, text_signal: TextSignal, source_event, dialogue_acts: List[DialogueAct] = None):
        scenario_id = extract_scenario_id(source_event)

        is_agent = any(self._get_name(annotation).lower() == ConversationalAgent.LEOLANI.name.lower()
                       for mention in text_signal.mentions
                       for annotation in mention.annotations
                       if annotation.type == ConversationalAgent.__name__)
        source = self._chat[scenario_id].agent if is_agent else self._chat[scenario_id].speaker
        logger.debug("Processing utterance %s (%s) from SOURCE %s", text_signal.id, text_signal.text, source)
        self._chat[scenario_id].add_utterance(text_signal.text, self._chat[scenario_id].agent if is_agent else self._chat[scenario_id].speaker, dialogue_acts)

        if is_agent:
            logger.debug("Skipping triple extraction for SOURCE %s", source)
            # Add robot utterances to the chat without triple extraction
            return
        else:
            logger.debug("Doing triple extraction for SOURCE %s", source)

       # self._chat.add_utterance(text_signal.text, self._chat.speaker, dialogue_acts)

        llm_response = self._extractor.analyze_in_context(self._chat[scenario_id])

        if llm_response:
            response = [{'This is the LLM response': llm_response}]
            self._event_bus.publish("cltl.topic.text_out", Event.for_payload(response), source=source_event)
            return
       # response = self._utterance_to_capsules(self._extractor.utterance, text_signal)
        response = self._utterance_to_capsules(self._chat[scenario_id].last_utterance, text_signal)

        #         # TODO: transform capsules into proper EMISSOR annotations
        #         if response:
        #             self._event_bus.publish(self._output_topic, Event.for_payload(response))
        #             logger.info("Published %s triples for signal %s (%s): %s",
        #                          len(response), text_signal.id, text_signal.text, response)
        #         else:
        #             logger.info("No triples for signal %s (%s)", text_signal.id, text_signal.text)

        scenario_id = self._emissor_client.get_current_scenario_id()
        dialog_act = self._chat[scenario_id].last_utterance.dialogue_acts[0]
        logger.debug("Dialog act of the last utterance %s (%s) is %s", text_signal.id, text_signal.text, dialog_act)

        if not self._feedback:
            ##### Clean version
            if response:
                self._event_bus.publish(self._output_topic, Event.for_payload(response), source=source_event)
                logger.debug("Published %s triples for signal %s (%s): %s",
                             len(response), text_signal.id, text_signal.text, response)
            else:
                logger.debug("No triples for signal %s (%s)", text_signal.id, text_signal.text)
                utterance = None
                signal = None
                for word in greet_words:
                    if word in text_signal.text.lower():
                        utterance = f"{choice(GREETINGS)}"
                        break
                if not utterance:
                    for word in bye_words:
                        if word in text_signal.text.lower():
                            utterance = f"{choice(BYES)}"
                            break
                if not utterance:
                    utterance = f"{choice(I_DONT_SEE)}"

                # signal = TextSignal.for_scenario(scenario_id, timestamp_now(), timestamp_now(), None, utterance)
                # self._event_bus.publish("cltl.topic.text_out", Event.for_payload(TextSignalEvent.for_agent(signal)))
                response = [{'text_response': utterance}]
                self._event_bus.publish("cltl.topic.brain_response", Event.for_payload(response), source=source_event)
                ### Need to post this as a cltl.topic.brain_response to trigger the replier.
                #  self._event_bus.publish(self._output_topic, Event.for_payload(TextSignalEvent.for_agent(signal)))
        else:
            ##### Feedback version
            if dialog_act == UtteranceType.QUESTION or dialog_act == DialogueAct.QUESTION:
                self.respond_to_question(response, text_signal, source_event)
            else:
                self.respond_to_statement(response, text_signal, source_event)

    def respond_to_statement(self, response, text_signal: TextSignal, source_event: Event):
        scenario_id = extract_scenario_id(source_event)
        if response:
            self._event_bus.publish(self._output_topic, Event.for_payload(response), source=source_event)
            logger.debug("Published %s triples for signal %s (%s): %s",
                         len(response), text_signal.id, text_signal.text, response)
            utterance = f"You said: {text_signal.text}."
            signal = TextSignal.for_scenario(scenario_id, timestamp_now(), timestamp_now(), None, utterance)
            self._event_bus.publish("cltl.topic.text_out", Event.for_payload(TextSignalEvent.for_agent(signal)), source=source_event)
            for ch in response:
                if isinstance(ch, str):
                    try:
                        ch = json.loads(ch)
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON: {e}")
                if self.check_triple(ch):
                    triple = "(" + ch['subject']['label'] + ", " + ch['predicate']['label'] + ", " + ch['object'][
                        'label'] + ') '
                    I_SEE = ["And this is what I got from what you said: ", "I got it. So you are claiming: ",
                             "Ok, so understand this as: ", "So interesting what you said. It boils down to: "]
                    utterance = f"{choice(I_SEE)} {triple}"
                    signal = TextSignal.for_scenario(scenario_id, timestamp_now(), timestamp_now(), None, utterance)
                    self._event_bus.publish("cltl.topic.text_out", Event.for_payload(TextSignalEvent.for_agent(signal)), source=source_event)
                else:
                    utterance = ""
                    if "utterance" in ch:
                        utterance = ch["utterance"]
                    logger.debug("Malformed triples for signal %s", ch)
                    I_SEE = ["I could not really understand what you said: ", "I did not got it. So you are claiming: ",
                             "Ok, so must be interesting but I am lost here: ", "Could be interesting what you said. But I just got: "]
                    utterance = f"{choice(I_SEE)} {utterance}, This is not a complete triple for my Knowledge Graph."
                    signal = TextSignal.for_scenario(scenario_id, timestamp_now(), timestamp_now(), None, utterance)
                    self._event_bus.publish("cltl.topic.text_out", Event.for_payload(TextSignalEvent.for_agent(signal)), source=source_event)
        else:
            logger.debug("No triples for signal %s (%s)", text_signal.id, text_signal.text)
            I_SEE = ["Cannot make much of what you said.", "I hear you but it does not make any sense to me.",
                     "Ok, interesting but too much for me. What else?",
                     "What are you trying to say? I am just a humble AI, please try again.",
                     "Sorry, I did not get that."]
            utterance = f"I have no response. {choice(I_SEE)}"
            signal = TextSignal.for_scenario(scenario_id, timestamp_now(), timestamp_now(), None, utterance)
            self._event_bus.publish("cltl.topic.text_out", Event.for_payload(TextSignalEvent.for_agent(signal)), source=source_event)

    def respond_to_question(self, response, text_signal: TextSignal, source_event: Event):
        scenario_id = extract_scenario_id(source_event)
        if response:
            self._event_bus.publish(self._output_topic, Event.for_payload(response), source=source_event)
            logger.debug("Published %s triples for signal %s (%s): %s",
                         len(response), text_signal.id, text_signal.text, response)
            utterance = f"You asked me: {text_signal.text}."
            signal = TextSignal.for_scenario(scenario_id, timestamp_now(), timestamp_now(), None, utterance)
            self._event_bus.publish("cltl.topic.text_out", Event.for_payload(TextSignalEvent.for_agent(signal)), source=source_event)
            for ch in response:
                if self.check_triple(ch):
                    triple = "(" + ch['subject']['label'] + ", " + ch['predicate']['label'] + ", " + ch['object'][
                        'label'] + ') '
                    I_SEE = ["And this is the query for my memory that I got from what you asked: ", "I got it. So you are asking: ",
                             "Ok, so: ", "So interesting what you asked. Your question boils down to: "]
                    utterance = f"{choice(I_SEE)} {triple}. I will check my memory for this triple. One moment please..."
                    signal = TextSignal.for_scenario(scenario_id, timestamp_now(), timestamp_now(), None, utterance)
                    self._event_bus.publish("cltl.topic.text_out", Event.for_payload(TextSignalEvent.for_agent(signal)), source=source_event)
                else:
                    logger.debug("Malformed triples for signal %s", text_signal.text)
                    I_SEE = ["And this is what I got from what you asked: ", "I got it. So you are asking: ",
                             "Ok, so: ", "So interesting what you asked. It boils down to: "]
                    utterance = f"{choice(I_SEE)} {ch}, but it is not a complete triple for my Knowledge Graph."
                    signal = TextSignal.for_scenario(scenario_id, timestamp_now(), timestamp_now(), None, utterance)
                    self._event_bus.publish("cltl.topic.text_out", Event.for_payload(TextSignalEvent.for_agent(signal)), source=source_event)
        else:
            logger.debug("No triples for signal %s (%s)", text_signal.id, text_signal.text)
            I_SEE = ["Cannot make much of what you said.", "I hear you but it does not make any sense to me.",
                     "Ok, interesting but too much for me. What else?",
                     "What are you trying to say? I am just a humble AI, please try again.",
                     "Sorry, I did not get that."]
            utterance = f"I did not manage to get a query from your question. {choice(I_SEE)}"
            signal = TextSignal.for_scenario(scenario_id, timestamp_now(), timestamp_now(), None, utterance)
            self._event_bus.publish("cltl.topic.text_out", Event.for_payload(TextSignalEvent.for_agent(signal)), source=source_event)


    def check_triple(self, triple):
        if 'subject' not in triple:
            logger.debug("No subject in triple %s", triple)
            return False
        if 'predicate' not in triple:
            logger.debug("No predicate in triple %s", triple)
            return False
        if 'object' not in triple:
            logger.debug("No object in triple %s", triple)
            return False
        # if 'perspective' not in triple:
        #     logger.debug("No perspective in triple %s", triple)
        #     return False
        return True

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
        # "type": "ConversationalAgent",
        # "value": "SPEAKER",
        # "@type": "Annotation",
        # "source": "LEOLANI",
        if isinstance(agent_annotation.value, str):
            return agent_annotation.value
        if isinstance(agent_annotation.value, ConversationalAgent):
            return agent_annotation.value.name

        raise ValueError("Cannot parse annotation value " + str(agent_annotation))

    def _update_chat(self, event):
        scenario_id = extract_scenario_id(event)

        if event.payload.scenario.context.agent:
            self._agent[scenario_id] = event.payload.scenario.context.agent
        if event.payload.scenario.context.speaker:
            self._speaker[scenario_id] = event.payload.scenario.context.speaker

        if event.payload.type == ScenarioStarted.__name__:
            agent_name = self._agent[scenario_id].name if self._agent[scenario_id].name else "Leolani"
            speaker_name = self._speaker[scenario_id].name if self._speaker[scenario_id].name else "Stranger"
            self._chat[scenario_id] = Chat(agent_name, speaker_name)
            logger.debug("Started chat with speaker %s, agent %s", self._chat[scenario_id].speaker, self._chat[scenario_id].agent)
        elif event.payload.type == ScenarioStopped.__name__:
            logger.debug("Stopping chat with %s, agent %s", self._chat[scenario_id].speaker, self._chat[scenario_id].agent)
            del self._chat[scenario_id]
            del self._speaker[scenario_id]
            del self._agent[scenario_id]
        elif event.payload.type == ScenarioEvent.__name__:
            if self._speaker[scenario_id].name and self._speaker[scenario_id].name != self._chat[scenario_id].speaker:
                self._chat[scenario_id].speaker = self._speaker[scenario_id].name
                logger.debug("Set speaker in chat to %s", self._chat[scenario_id].speaker)
            if self._agent[scenario_id].name and self._agent[scenario_id].name != self._chat[scenario_id].agent:
                self._chat[scenario_id].agent = self._agent[scenario_id].name
                logger.debug("Set agent in chat to %s", self._chat[scenario_id].agent)

    def _utterance_to_capsules(self, utterance, signal):
        capsules = []
        utterance_type = UtteranceType.STATEMENT
        if utterance._dialogue_acts and len(utterance._dialogue_acts[0])>0:
            utterance_type = utterance._dialogue_acts[0]
            logger.debug("Obtained UtteranceType from utterance: %s", utterance_type)
        for triple in utterance.triples:
            logger.debug("Triple input: %s", triple)
            self._add_uri_to_triple(triple)
            logger.debug("Triple input after adding URI: %s", triple)
            scenario_id = signal.time.container_id
            capsule = {"chat": scenario_id,
                       "turn": signal.id,
                       "author": self._get_author(scenario_id),
                       "utterance": utterance.transcript,
                       "utterance_type": utterance_type,
                       "position": "0-" + str(len(utterance.transcript)),
                       ###
                       "subject": triple['subject'],
                       "predicate": triple['predicate'],
                       "object": triple['object'],
                       ###
                       "context_id": scenario_id,
                       "timestamp": timestamp_now()
                       }
            if 'perspective' in triple:
                capsule.update({'perspective': triple['perspective']})
            capsules.append(capsule)
            logger.debug("Capsule input after adding URI: %s", capsule)
        return capsules

    def _add_uri_to_triple(self, triple: dict):
        uri = {'uri': None}
        triple['subject'].update(uri)
        triple['predicate'].update(uri)
        triple['object'].update(uri)

    # @TODO check if this needs to be the TextSignal source
    def _get_author(self, scenario_id):
        return {
            "label": self._speaker[scenario_id].name if self._speaker[scenario_id].name else self._chat[scenario_id].speaker,
            "type": ["person"],
            "uri": self._speaker[scenario_id].uri
        }
