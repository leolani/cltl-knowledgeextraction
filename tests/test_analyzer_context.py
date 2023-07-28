import unittest

from cltl.commons.discrete import UtteranceType
from parameterized import parameterized, parameterized_class

from cltl.triple_extraction.api import Chat
from cltl.triple_extraction.conversational_analyzer import ConversationalAnalyzer


@parameterized_class(('analyzer',), [(ConversationalAnalyzer("../resources/conversational_triples"), )])
class TestConversationalAnalyzer(unittest.TestCase):
    def setUp(self) -> None:
        self.chat = Chat("Leolani", "Piek")

    @parameterized.expand([
        ("statement two turns", "I like dogs.<eos>I like pizza", UtteranceType.STATEMENT,
                    [("leolani", "like", "dogs"), ("piek", "like", "pizza")]),
        ("statement two turns two utterances", "I like dogs.<utt>I like cats.<eos>I like pizza.<utt>I like tacos.", UtteranceType.STATEMENT,
                    [("leolani", "like", "dogs"), ("leolani", "like", "cats"),
                     ("piek", "like", "pizza"), ("piek", "like", "tacos")]),
        ("statement three turns", "I like tacos.<eos>I like dogs.<eos>I like pizza", UtteranceType.STATEMENT,
                    [("leolani", "like", "dogs"), ("piek", "like", "tacos"), ("piek", "like", "pizza")]),
    ])
    def test_utterances(self, _, transcript, type, triples):
        turns = transcript.split("<eos>")
        speaker_utterances = [turn.split("<utt>") for turn in turns]

        even_speaker = "Leolani" if len(turns) % 2 == 0 else "Piek"
        odd_speaker = "Piek" if len(turns) % 2 == 0 else "Leolani"

        for idx, utterances in enumerate(speaker_utterances):
            for utterance in utterances:
                speaker = even_speaker if idx % 2 == 0 else odd_speaker
                self.chat.add_utterance(utterance, utterance_speaker=speaker)

        self.analyzer.analyze_in_context(self.chat)

        self.assertEqual(len(triples), len(self.chat.last_utterance.triples), self.chat.last_utterance.triples)
        for triple in self.chat.last_utterance.triples:
            self.assertEqual(type, triple['utterance_type'])
            triple_labels = (triple['subject']['label'], triple['predicate']['label'], triple['object']['label'])
            self.assertTrue(triple_labels in triples, f"{triple} not in {triples}")
