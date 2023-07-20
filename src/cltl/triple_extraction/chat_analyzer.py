import logging
from typing import List

from cltl.question_extraction.analyzer import Analyzer
from cltl.triple_extraction.api import Chat

logger = logging.getLogger(__name__)


class ChatAnalyzer(Analyzer):
    def __init__(self, analyzers: List[Analyzer]):
        self._analyzers = analyzers
        self._chat = None

    def analyze_in_context(self, chat: Chat):
        self._chat = chat
        for analyzer in self._analyzers:
            analyzer.analyze_in_context(chat)

    def analyze(self, utterance):
        """Deprecated, use `analyze_in_context` instead!"""
        for analyzer in self._analyzers:
            analyzer.analyze(utterance)

    @property
    def utterance(self):
        """
        Returns
        -------
        utterance: Utterance
            Utterance
        """
        return self._chat.last_utterance

    @property
    def triple(self):
        """
        Returns
        -------
        triple: dict or None
        """
        return self.utterance.triple