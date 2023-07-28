import logging

import spacy

from cltl.commons.discrete import UtteranceType
from cltl.triple_extraction.analyzer import Analyzer
from cltl.triple_extraction.api import Chat
from cltl.triple_extraction.spacy_triples import dep_to_triple


logger = logging.getLogger(__name__)


#TODO Fix class name
class spacyAnalyzer(Analyzer):
    def __init__(self):
        """
        spaCy Analyzer Object

        Parameters
        ----------
        """
        self._nlp = spacy.load("en_core_web_sm")
        self._utterance = None

    @property
    def utterance(self):
        return self._utterance

    def analyze_in_context(self, chat: Chat):
        self.analyze(chat.last_utterance)

    # TODO this doesn't match the Analyzer interface!
    def analyze(self, utterance):
        """
        Analyzer factory function

        Find appropriate Analyzer for this utterance

        Parameters
        ----------
        utterance: Utterance
            utterance to be analyzed

        """
        self._utterance = utterance
        speaker = self._utterance.chat.speaker
        hearer = self._utterance.chat.agent

        # @TODO: check if there are embedded clauses:
        # - ccomp  "I think ccomp that S. likes chees"
        # - xcomp, subject or object raising  "I like xcomp talking to her"
        triples, speaker_mentions, hearer_mentions, subject_mentions, object_mentions = dep_to_triple.get_subj_obj_triples_with_spacy(
            self._nlp, utterance.transcript, speaker, hearer)
        if not triples:
            triples, speaker_mentions, hearer_mentions, subject_mentions, object_mentions = dep_to_triple.get_subj_amod_triples_with_spacy(
                self._nlp, utterance.transcript, speaker, hearer)
        if not triples:
            triples, speaker_mentions, hearer_mentions, subject_mentions, object_mentions = dep_to_triple.get_subj_attr_triples_with_spacy(
                self._nlp, utterance.transcript, speaker, hearer)
        if not triples:
            triples, speaker_mentions, hearer_mentions, subject_mentions, object_mentions = dep_to_triple.get_subj_prep_pobj_triples_with_spacy(
                self._nlp, utterance.transcript, speaker, hearer)

        if triples:
            for triple in triples:
                self.set_extracted_values(utterance_type=UtteranceType.STATEMENT, triple=triple)
        else:
            logger.warning("Couldn't extract triples")

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


if __name__ == "__main__":
    '''
    test files with triples are formatted like so "test sentence : subject predicate object" 
    multi-word-expressions have dashes separating their elements, and are marked with apostrophes if they are a 
    collocation
    '''
    utterance = "I love cats."
    chat = Chat("Leolani", "Lenka")
    analyzer = spacyAnalyzer()

    chat.add_utterance(utterance)
    analyzer.analyze(chat.last_utterance, "I", "")
    print(chat.last_utterance.triples)
