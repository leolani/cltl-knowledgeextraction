import logging
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import List

from cltl.question_extraction.analyzer import Analyzer
from cltl.triple_extraction.api import Chat

logger = logging.getLogger(__name__)


class _AnalyzerContextTask:
    def __init__(self, analyzer: Analyzer, chat):
        self._analyzer = analyzer
        self._chat = chat

    def __call__(self, *args, **kwargs):
        self._analyzer.analyze_in_context(self._chat)


class _AnalyzerUtteranceTask:
    def __init__(self, analyzer: Analyzer, utterance):
        self._analyzer = analyzer
        self._utterance = utterance

    def __call__(self, *args, **kwargs):
        self._analyzer.analyze(self._utterance)


class ChatAnalyzer(Analyzer):
    def __init__(self, analyzers: List[Analyzer], timeout: float = 0.0):
        super().__init__()
        self._analyzers = analyzers
        self._timeout = timeout
        self._chat = None

    def analyze_in_context(self, chat: Chat):
        self._chat = chat
        self._parallel(_AnalyzerContextTask(analyzer, chat) for analyzer in self._analyzers)

    def analyze(self, utterance):
        """Deprecated, use `analyze_in_context` instead!"""
        self._parallel(_AnalyzerUtteranceTask(analyzer, utterance) for analyzer in self._analyzers)

    executor = ThreadPoolExecutor(max_workers=1)
    def _parallel(self, tasks):
        # start = time.time()
        # try:
        #     for task, future in [(i, executor.submit(i)) for i in tasks]:
        #         try:
        #             elapsed = time.time() - start
        #             future.result(timeout=max(0.001, self._timeout - elapsed) if self._timeout else None)
        #             logger.debug("Extracted triples for %s", task._analyzer.__class__.__name__)
        #         except TimeoutError:
        #             logger.warning("Timeout during triple extraction for %s", task._analyzer.__class__.__name__)
        # finally:
        #     executor.shutdown(wait=False, cancel_futures=True)
        start = time.time()
        try:
            for task in tasks:
                try:
                    elapsed = time.time() - start
                    task()
                    logger.debug("Extracted triples for %s", task._analyzer.__class__.__name__)
                except TimeoutError:
                    logger.warning("Timeout during triple extraction for %s", task._analyzer.__class__.__name__)
        finally:
            pass

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