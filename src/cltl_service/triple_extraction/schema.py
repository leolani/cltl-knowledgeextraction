from dataclasses import dataclass

from cltl_service.backend.schema import TextSignalEvent
from emissor.representation.container import Index
from emissor.representation.scenario import Modality, TextSignal


@dataclass
class TripleExtractionTextSignalEvent(TextSignalEvent):
    confidence: float
    audio_segment: Index

    @classmethod
    def create(cls, signal: TextSignal, confidence: float, audio_segment: Index):
        return cls(cls.__name__, Modality.TEXT, signal, confidence, audio_segment)