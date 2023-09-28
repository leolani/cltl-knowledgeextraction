import unittest

from cltl.commons.discrete import UtteranceType
from parameterized import parameterized, parameterized_class

from cltl.triple_extraction.api import Chat, Utterance
from cltl.triple_extraction.cfg_analyzer import CFGAnalyzer
from cltl.triple_extraction.oie_analyzer import OIEAnalyzer
from cltl.triple_extraction.spacy_analyzer import spacyAnalyzer


@parameterized_class(('analyzer',), [(CFGAnalyzer(), ), (OIEAnalyzer(), ), (spacyAnalyzer(), ),])
class TestStatementAnalyzers(unittest.TestCase):
    def setUp(self) -> None:
        self.chat = Chat("Leolani", "Piek")

    @parameterized.expand([
        ("statement", "I like pizza", UtteranceType.STATEMENT, "Piek", "like", "pizza"),
        ("statement dot", "I like pizza.", UtteranceType.STATEMENT, "Piek", "like", "pizza"),
        ("statement exclamation", "I like pizza!", UtteranceType.STATEMENT, "Piek", "like", "pizza"),
        ("statement excited", "I like pizza, really!", UtteranceType.STATEMENT, "Piek", "like", "pizza"),
        ("statement_punctuation", "I like pizza.", UtteranceType.STATEMENT, "Piek", "like", "pizza"),
        ("statement_casing", "i like pizza", UtteranceType.STATEMENT, "Piek", "like", "pizza"),
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

    @parameterized.expand([
        ("statement", "I like pizza", UtteranceType.STATEMENT, "Piek", "like", "pizza"),
        ("statement dot", "I like pizza.", UtteranceType.STATEMENT, "Piek", "like", "pizza"),
        ("statement exclamation", "I like pizza!", UtteranceType.STATEMENT, "Piek", "like", "pizza"),
        ("statement excited", "I like pizza, really!", UtteranceType.STATEMENT, "Piek", "like", "pizza"),
        ("statement_punctuation", "I like pizza.", UtteranceType.STATEMENT, "Piek", "like", "pizza"),
        ("statement_casing", "i like pizza", UtteranceType.STATEMENT, "Piek", "like", "pizza"),
    ])
    def test_single_utterance_in_context(self, _, transcript, type, subject, predicate, object):
        self.chat.add_utterance(transcript, self.chat.speaker)
        self.analyzer.analyze_in_context(self.chat)

        self.assertEqual(1, len(self.chat.last_utterance.triples))
        triple = self.chat.last_utterance.triples[0]
        self.assertEqual(type, triple['utterance_type'])
        self.assertEqual(subject, triple['subject']['label'])
        self.assertEqual(predicate, triple['predicate']['label'])
        self.assertEqual(object, triple['object']['label'])
