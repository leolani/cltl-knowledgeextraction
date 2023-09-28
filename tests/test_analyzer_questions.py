import unittest

from cltl.commons.discrete import UtteranceType
from parameterized import parameterized, parameterized_class

from cltl.triple_extraction.api import Chat, Utterance
from cltl.triple_extraction.cfg_analyzer import CFGAnalyzer


@parameterized_class(('analyzer',), [(CFGAnalyzer(), )])
class TestQuestionAnalyzers(unittest.TestCase):
    def setUp(self) -> None:
        self.chat = Chat("Leolani", "Piek")

    @parameterized.expand([
        ("question_who", "Who likes pizza", UtteranceType.QUESTION, "", "like", "pizza"),
        ("question_who_punctuation", "Who likes pizza?", UtteranceType.QUESTION, "", "like", "pizza"),
        ("question_who_casing", "who likes pizza", UtteranceType.QUESTION, "", "like", "pizza"),
        ("question_what", "What does Piek like", UtteranceType.QUESTION, "Piek", "like", ""),
        ("question_what_punctuation", "What does Piek like?", UtteranceType.QUESTION, "Piek", "like", ""),
        ("question_what_casing", "what does Piek like?", UtteranceType.QUESTION, "Piek", "like", "")
    ])
    def test_single_utterance(self, _, transcript, type, subject, predicate, object):
        utterance = Utterance(self.chat, transcript, 0)

        self.analyzer.analyze(utterance)

        self.assertEqual(1, len(utterance.triples))
        triple = utterance.triples[0]
        self.assertEqual(type, triple['utterance_type'])
        self.assertEqual(subject, triple['subject']['label'])
        self.assertEqual(predicate, triple['predicate']['label'])
        self.assertEqual(object, triple['object']['label'])
