import logging

from cltl.combot.infra.config import ConfigurationManager
from cltl.combot.infra.event import Event, EventBus
from cltl.combot.infra.resource import ResourceManager
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

        return cls(config.get("topic_input"), config.get("topic_output"), extractor, config.get("speaker"),
                   event_bus, resource_manager)

    def __init__(self, input_topic: str, output_topic: str, extractor: Analyzer, speaker: str,
                 event_bus: EventBus, resource_manager: ResourceManager):
        self._extractor = extractor
        self._chat = Chat(speaker)

        self._event_bus = event_bus
        self._resource_manager = resource_manager

        self._input_topic = input_topic
        self._output_topic = output_topic

        self._topic_worker = None

    @property
    def app(self):
        return None

    def start(self, timeout=30):
        self._topic_worker = TopicWorker([self._input_topic], self._event_bus, provides=[self._output_topic],
                                         resource_manager=self._resource_manager, processor=self._process,
                                         name=self.__class__.__name__)
        self._topic_worker.start().wait()

    def stop(self):
        if not self._topic_worker:
            pass

        self._topic_worker.stop()
        self._topic_worker.await_stop()
        self._topic_worker = None

    def _process(self, event: Event):
        self._chat.add_utterance(event.payload.signal.text)
        self._extractor.analyze(self._chat.last_utterance)
        response = self._utterance_to_capsules(self._chat.last_utterance, event.payload.signal)

        if response:
            # TODO: transform capsules into proper EMISSOR annotations
            self._event_bus.publish(self._output_topic, Event.for_payload(response))
            logger.debug("Published %s triples for signal %s (%s)", len(response), event.payload.signal.id, event.payload.signal.text)
        else:
            logger.debug("No triples for signal %s (%s)", event.payload.signal.id, event.payload.signal.text)

    def _utterance_to_capsules(self, utterance, signal):
        capsules = []

        for triple in utterance.triples:
            self._add_uri_to_triple(triple)
            scenario_id = signal.time.container_id

            capsule = {"chat": scenario_id,
                       "turn": signal.id,
                       "author": utterance.chat_speaker,
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
                       "date": utterance.datetime.isoformat(),
                       "place": "",
                       "place_id": None,
                       "country": "",
                       "region": "",
                       "city": "",
                       "objects": [],
                       "people": []
                       }

            capsules.append(capsule)

        return capsules

    def _add_uri_to_triple(self, triple: dict):
        uri = {'uri':None}
        triple['subject'].update(uri)
        triple['predicate'].update(uri)
        triple['object'].update(uri)
