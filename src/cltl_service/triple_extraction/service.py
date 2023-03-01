import logging
from typing import List

from cltl.combot.event.emissor import ScenarioStarted, ScenarioStopped, ScenarioEvent, Agent, ConversationalAgent
from cltl.combot.infra.config import ConfigurationManager
from cltl.combot.infra.event import Event, EventBus
from cltl.combot.infra.resource import ResourceManager
from cltl.combot.infra.time_util import timestamp_now
from cltl.combot.infra.topic_worker import TopicWorker

from cltl.triple_extraction.analyzer import Analyzer
from cltl.triple_extraction.api import Chat

logger = logging.getLogger(__name__)

CONTENT_TYPE_SEPARATOR = ';'


class TripleExtractionService:
    @classmethod
    def from_config(cls, extractor: Analyzer, event_bus: EventBus, resource_manager: ResourceManager,
                    config_manager: ConfigurationManager):
        config = config_manager.get_config("cltl.triple_extraction")

        agent_topic = config.get("topic_agent") if "topic_agent" in config else None

        return cls(config.get("topic_input"), agent_topic, config.get("topic_output"),
                   config.get("topic_scenario"), config.get("topic_intention"), config.get("intentions", multi=True),
                   extractor, event_bus, resource_manager)

    def __init__(self, input_topic: str, agent_topic: str, output_topic: str, scenario_topic: str,
                 intention_topic: str, intentions: List[str], extractor: Analyzer,
                 event_bus: EventBus, resource_manager: ResourceManager):
        self._extractor = extractor

        self._event_bus = event_bus
        self._resource_manager = resource_manager

        self._input_topic = input_topic
        self._agent_topic = agent_topic
        self._output_topic = output_topic
        self._scenario_topic = scenario_topic

        self._intention_topic = intention_topic if intention_topic else None
        self._intentions = set(intentions) if intentions else {}
        self._active_intentions = {}

        self._topic_worker = None

        self._chat = None
        self._speaker = Agent()
        self._agent = Agent()

    @property
    def app(self):
        return None

    def start(self, timeout=30):
        topics = [self._input_topic, self._scenario_topic, self._intention_topic]
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

        if self._intentions and not (self._active_intentions & self._intentions):
            logger.debug("Skipped event outside intention %s, active: %s (%s)",
                         self._intentions, self._active_intentions, event)
            return

        if not self._chat:
            logger.warning("Received utterance outside of a chat (%s)", event)
            return

        is_agent = any(annotation.value.lower() == ConversationalAgent.LEOLANI.name.lower()
                       for mention in event.payload.signal.mentions
                       for annotation in mention.annotations
                       if annotation.type == ConversationalAgent.__name__)

        self._chat.add_utterance(event.payload.signal.text, self._chat.agent if is_agent else self._chat.speaker)

        if is_agent:
            # Only add robot utterances to the chat
            return

        self._extractor.analyze_in_context(self._chat)
        response = self._utterance_to_capsules(self._extractor.utterance, event.payload.signal)

        if response:
            # TODO: transform capsules into proper EMISSOR annotations
            self._event_bus.publish(self._output_topic, Event.for_payload(response))
            logger.debug("Published %s triples for signal %s (%s): %s",
                         len(response), event.payload.signal.id, event.payload.signal.text, response)
        else:
            logger.debug("No triples for signal %s (%s)", event.payload.signal.id, event.payload.signal.text)

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
                       "context_id": None,
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
