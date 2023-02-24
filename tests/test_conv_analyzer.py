import unittest

from cltl.commons.discrete import UtteranceType
from parameterized import parameterized, parameterized_class

from cltl.triple_extraction.api import Chat
from cltl.triple_extraction.conversational_analyzer import ConversationalAnalyzer


# @parameterized_class(('analyzer',), [(CFGAnalyzer(), ), (OIEAnalyzer(),), (spacyAnalyzer())])
@parameterized_class(('analyzer',), [(ConversationalAnalyzer("../resources/conversational_triples"), )])
class TestConversationalAnalyzer(unittest.TestCase):
    def setUp(self) -> None:
        self.chat = Chat("Leolani", "Piek")

    @parameterized.expand([
        ("statement", "I like pizza", UtteranceType.STATEMENT, "Piek", "like", "pizza"),
        ("statement dot", "I like pizza.", UtteranceType.STATEMENT, "Piek", "like", "pizza"),
        ("statement exclamation", "I like pizza!", UtteranceType.STATEMENT, "Piek", "like", "pizza"),
        ("statement excited", "I like pizza, really!", UtteranceType.STATEMENT, "Piek", "like", "pizza"),
        ("statement_punctuation", "I like pizza.", UtteranceType.STATEMENT, "Piek", "like", "pizza"),
        ("statement_casing", "i like pizza", UtteranceType.STATEMENT, "Piek", "like", "pizza"),
        ("question_who", "Who likes pizza", UtteranceType.QUESTION, "", "like", "pizza"),
        ("question_who_punctuation", "Who likes pizza?", UtteranceType.QUESTION, "", "like", "pizza"),
        ("question_who_casing", "who likes pizza", UtteranceType.QUESTION, "", "like", "pizza"),
        ("question_what", "What does Piek like", UtteranceType.QUESTION, "Piek", "like", ""),
        ("question_what_punctuation", "What does Piek like?", UtteranceType.QUESTION, "Piek", "like", ""),
        ("question_what_casing", "what does Piek like?", UtteranceType.QUESTION, "Piek", "like", "")
    ])
    def test_single_utterance(self, _, transcript, type, subject, predicate, object):
        self.chat.add_utterance(transcript)

        self.analyzer.analyze_in_context(self.chat)

        self.assertEqual(1, len(self.chat.last_utterance.triples))
        triple = self.chat.last_utterance.triples[0]
        self.assertEqual(type, triple['utterance_type'])
        self.assertEqual(subject, triple['subject']['label'])
        self.assertEqual(predicate, triple['predicate']['label'])
        self.assertEqual(object, triple['object']['label'])