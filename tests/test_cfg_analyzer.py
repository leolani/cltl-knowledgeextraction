import unittest

from cltl.commons.discrete import UtteranceType

from cltl.triple_extraction.api import Chat, Utterance, DialogueAct
from cltl.triple_extraction.cfg_analyzer import CFGAnalyzer


class TestCfgAnalyzers(unittest.TestCase):
    def setUp(self) -> None:
        self.chat = Chat("Leolani", "Piek")

    def test_no_question_processing_statement(self):
        analyzer = CFGAnalyzer(process_questions=False)

        utterance = Utterance(self.chat, "I like pizza.", 0)
        utterance.dialogue_acts = [DialogueAct.STATEMENT]

        analyzer.analyze(utterance)

        self.assertEqual(1, len(utterance.triples))
        triple = utterance.triples[0]
        self.assertEqual(UtteranceType.STATEMENT, triple['utterance_type'])
        self.assertEqual("Piek", triple['subject']['label'])
        self.assertEqual("like", triple['predicate']['label'])
        self.assertEqual("pizza", triple['object']['label'])

    def test_no_question_processing_question(self):
        analyzer = CFGAnalyzer(process_questions=False)

        utterance = Utterance(self.chat, "Do I like pizza?", 0)
        utterance.dialogue_acts = [DialogueAct.QUESTION]

        analyzer.analyze(utterance)

        self.assertEqual(0, len(utterance.triples))

    def test_question_processing_statement(self):
        analyzer = CFGAnalyzer()

        utterance = Utterance(self.chat, "I like pizza.", 0)
        utterance.dialogue_acts = [DialogueAct.STATEMENT]

        analyzer.analyze(utterance)

        self.assertEqual(1, len(utterance.triples))
        triple = utterance.triples[0]
        self.assertEqual(UtteranceType.STATEMENT, triple['utterance_type'])
        self.assertEqual("Piek", triple['subject']['label'])
        self.assertEqual("like", triple['predicate']['label'])
        self.assertEqual("pizza", triple['object']['label'])

    def test_question_processing_question(self):
        analyzer = CFGAnalyzer()

        utterance = Utterance(self.chat, "Do I like pizza?", 0)
        utterance.dialogue_acts = [DialogueAct.QUESTION]

        analyzer.analyze(utterance)

        self.assertEqual(1, len(utterance.triples))
        triple = utterance.triples[0]
        self.assertEqual(UtteranceType.QUESTION, triple['utterance_type'])
        self.assertEqual("Piek", triple['subject']['label'])
        self.assertEqual("Do-like", triple['predicate']['label'])
        self.assertEqual("pizza", triple['object']['label'])