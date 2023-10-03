import itertools
import logging

from cltl.commons.discrete import UtteranceType, Polarity, Certainty

from cltl.triple_extraction.analyzer import Analyzer
from cltl.triple_extraction.api import Chat
from cltl.triple_extraction.conversational_triples.conversational_triple_extraction import AlbertTripleExtractor
from cltl.triple_extraction.utils.triple_normalization import TripleNormalizer

logger = logging.getLogger(__name__)

THRESHOLD = 0.8


class ConversationalAnalyzer(Analyzer):
    def __init__(self, model_path: str):
        """
        Parameters
        ----------
        model_path: str Path to the model
        """
        self._extractor = AlbertTripleExtractor(path=model_path)
        self._triple_normalizer = TripleNormalizer()
        self._chat = None

    def analyze(self, utterance):
        """
        Analyzer factory function

        Determines the type of utterance, extracts the RDF triple and perspective attaching them to the last utterance

        Parameters
        ----------
        utterance: Utterance
            utterance to be analyzed

        """
        raise NotImplementedError("Analyzing a single utterance is deprecated, use analayze_in_context instead!")

    def analyze_in_context(self, chat):
        """
        Analyzer factory function

        Find appropriate Analyzer for this utterance

        Parameters
        ----------
        utterance: Utterance
            utterance to be analyzed

        """
        self._chat = chat

        triples = []
        # print('chat.last_utterance.utterance_speaker', chat.last_utterance.utterance_speaker)
        # print('chat.speaker', chat.speaker)
        if chat.last_utterance.utterance_speaker == chat.speaker:
            self._chat = chat

            self._utterance = chat.last_utterance
            conversation, speaker1, speaker2 = self._chat_to_converstation(chat)

            # print('speaker1', speaker1)
            # print('speaker2', speaker2)
            # print(conversation)

            for score, triple_value in self._extractor.extract_triples(conversation, speaker1, speaker2):
                if score >= THRESHOLD:
                    triple = None

                    if len(triple_value) > 2:
                        triple = {"subject": {"label": triple_value[0], "type": [], "uri": None},
                                  "predicate": {"label": triple_value[1], "type": [], "uri": None},
                                  "object": {"label": triple_value[2], "type": [], "uri": None}
                                  }

                    if len(triple_value) == 4:
                        triple["perspective"] = {"polarity": Polarity.from_str(triple_value[3]).value}
                    elif len(triple_value) == 5:
                        triple["perspective"] = {"polarity": Polarity.from_str(triple_value[3]).value,
                                                 "certainty": Certainty.from_str(triple_value[4]).value}
                    # else:
                    #     triple["perspective"]={"polarity" : Polarity.POSITIVE}
                    #     triple["perspective"]={"certainty" : Certainty.CERTAIN}

                    if triple:
                        triple = self._triple_normalizer.normalize(self.utterance, self.get_simple_triple(triple))
                        triples.append(triple)
        else:
            print('This is not from the human speaker', chat.speaker, ' but from:',
                  chat.last_utterance.utterance_speaker)
        if triples:
            for triple in triples:
                logger.debug("triple: %s", triple)
                self.set_extracted_values_given_perspective(utterance_type=UtteranceType.STATEMENT, triple=triple)
        else:
            logger.warning("Couldn't extract triples")

    def _chat_to_converstation(self, chat):
        utterances_by_speaker = [(speaker, " ".join(utt.transcript for utt in utterances)) for speaker, utterances
                                 in itertools.groupby(chat.utterances, lambda utt: utt.utterance_speaker)]
        utterances_by_speaker = utterances_by_speaker[-3:]

        speakers = list(zip(*utterances_by_speaker))[0]
        turns = list(zip(*utterances_by_speaker))[1]
        conversation = ("<eos>" * min(2, (3 - len(utterances_by_speaker)))) + "<eos>".join(turns)

        speaker1 = speakers[-1] if speakers else None
        if len(speakers) > 1:
            speaker2 = speakers[-2]
        else:
            speaker2 = chat.agent if speaker1 == chat.speaker else chat.speaker

        return conversation, speaker1, speaker2

    def get_simple_triple(self, triple):
        simple_triple = {'subject': triple['subject']['label'].replace(" ", "-").replace('---', '-'),
                         'predicate': triple['predicate']['label'].replace(" ", "-").replace('---', '-'),
                         'object': triple['object']['label'].replace(" ", "-").replace('---', '-'),
                         'perspective': triple['perspective']}
        return simple_triple

    def extract_perspective(self):
        """
        This function extracts perspective from statements
        :param predicate: statement predicate
        :param utterance_info: product of statement analysis thus far
        :return: perspective dictionary consisting of sentiment, certainty, and polarity value
        """
        certainty = 1  # Possible
        polarity = 1  # Positive
        sentiment = 0  # Underspecified
        emotion = 0  # Underspecified
        perspective = {'sentiment': float(sentiment), 'certainty': float(certainty), 'polarity': float(polarity),
                       'emotion': float(emotion)}
        return perspective

    @property
    def utterance(self):
        return self._chat.last_utterance


if __name__ == "__main__":
    '''
    test files with triples are formatted like so "test sentence : subject predicate object" 
    multi-word-expressions have dashes separating their elements, and are marked with apostrophes if they are a 
    collocation
    '''

    model = "resources/conversational_triples"

    analyzer = ConversationalAnalyzer(model)
    utterances = ["I love cats.", "Do you also love dogs?", "No I do not."]
    chat = Chat("Leolani", "Lenka")
    for utterance in utterances:
        chat.add_utterance(utterance)
        analyzer.analyze_in_context(chat)
    for utterance in chat.utterances:
        print(utterance)
        print('Final triples', utterance.triples)
