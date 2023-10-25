import logging
import unittest

import time
from cltl.commons.discrete import UtteranceType

from cltl.triple_extraction.api import Utterance, DialogueAct, Chat
from cltl.triple_extraction.cfg_analyzer import CFGAnalyzer
from cltl.triple_extraction.chat_analyzer import ChatAnalyzer


class TestChatAnalyzers(unittest.TestCase):
    def setUp(self) -> None:
        self.chat = Chat("Leolani", "Piek")

    def test_exceed_timeout(self):
        analyzers = CFGAnalyzer(process_questions=False), CFGAnalyzer(process_questions=False)
        analyzer = ChatAnalyzer(analyzers, 0.001)

        utterance = Utterance(self.chat, "I like pizza.", 0)
        utterance.dialogue_acts = [DialogueAct.STATEMENT]

        start = time.time()
        analyzer.analyze(utterance)
        elapsed = time.time() - start

        self.assertTrue(elapsed < 0.01)
        self.assertEqual(0, len(utterance.triples))

    def test_within_timeout(self):
        analyzers = CFGAnalyzer(process_questions=False), CFGAnalyzer(process_questions=False)
        analyzer = ChatAnalyzer(analyzers, 60000000)

        utterance = Utterance(self.chat, "I like pizza.", 0)
        utterance.dialogue_acts = [DialogueAct.STATEMENT]

        analyzer.analyze(utterance)

        self.assertEqual(2, len(utterance.triples))
        triple = utterance.triples[0]
        self.assertEqual(UtteranceType.STATEMENT, triple['utterance_type'])
        self.assertEqual("Piek", triple['subject']['label'])
        self.assertEqual("like", triple['predicate']['label'])
        self.assertEqual("pizza", triple['object']['label'])
        self.assertEqual(utterance.triples[0], utterance.triples[1])


if __name__ == '__main__':
    # DEBUG for demonstration purposes, but you could set the level from
    # cmdline args to whatever you like
    logging.basicConfig(level=logging.DEBUG, format='%(name)s %(levelname)s %(message)s')
    unittest.main()