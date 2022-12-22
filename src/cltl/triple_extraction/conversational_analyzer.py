from cltl.commons.discrete import UtteranceType
from cltl.triple_extraction.analyzer import Analyzer
from cltl.triple_extraction.api import Chat
from cltl.triple_extraction.spacy_triples import dep_to_triple
from cltl.triple_extraction.conversational_triples.conversational_triple_extraction import AlbertTripleExtractor

THRESHOLD = 0.8

class conversationalAnalyzer(Analyzer):

    def __init__(self):
        """
        spaCy Analyzer Object

        Parameters
        ----------
        """

        super(conversationalAnalyzer, self).__init__()
        self._extractor = AlbertTripleExtractor(path='models/2022-04-27')

    def analyze(self, utterance):
        """
        Analyzer factory function

        Determines the type of utterance, extracts the RDF triple and perspective attaching them to the last utterance

        Parameters
        ----------
        utterance: Utterance
            utterance to be analyzed

        """

        self._utterance = utterance

        NotImplementedError()

    def analyze_in_context(self, chat, utterance, speaker, hearer):
        """
        Analyzer factory function

        Find appropriate Analyzer for this utterance

        Parameters
        ----------
        utterance: Utterance
            utterance to be analyzed

        """
        super(conversationalAnalyzer, self).analyze_in_context(chat, utterance)

        self._chat = chat
        self._extractor._speaker1 =chat.speaker
        self._extractor._speaker2 =chat.agent

        example = "I went to the new university. It was great! <eos> I like studying too and learning. You? <eos> No, hate it!"

        conversation  = "<eos><eos>"+chat.last_utterance
        if len(chat.utterances>2):
            conversation = chat.utterances[-2]+"<eos>"+ chat.utterances[-1]+"<eos>" + chat.last_utterance
        elif (len(chat.utterances==2)):
            conversation = "<eos>"+ chat.utterances[-1]+"<eos>" + chat.last_utterance

        subjects: {'SPEAKER1', 'it', 'SPEAKER2'}
        predicates: {'like', 'hate', 'was', 'went to'}
        objects: {'studying', 'great', 'learning', 'the new university', 'it'}

        # 0.9995951('HUMAN', 'went to', 'the new university', 'positive')
        # 0.9994972('it', 'was', 'great', 'positive')
        # 0.99911314('HUMAN', 'hate', 'the new university', 'positive')
        # 0.99910575('HUMAN', 'hate', 'it', 'positive')
        # 0.99836904('LEOLANI', 'like', 'studying', 'positive')
        # 0.9970577('HUMAN', 'hate', 'studying', 'positive')
        # 0.9905161('LEOLANI', 'like', 'learning', 'positive')
        # 0.99003685('LEOLANI', 'hate', 'it', 'positive')
        # 0.4502159('LEOLANI', 'hate', 'studying', 'positive')

        for score, triple in self._extractor.extract_triples(conversation):

        #   nlp = spacy.load("en_core_web_sm")

        # @TODO: check if there are embedded clauses:
        # - ccomp  "I think ccomp that S. likes chees"
        # - xcomp, subject or object raising  "I like xcomp talking to her"
        triples, speaker_mentions, hearer_mentions, subject_mentions, object_mentions = dep_to_triple.get_subj_obj_triples_with_spacy(nlp, utterance.transcript, speaker, hearer)
        if not triples:
            triples, speaker_mentions, hearer_mentions, subject_mentions, object_mentions = dep_to_triple.get_subj_amod_triples_with_spacy(
                nlp, utterance.transcript, speaker, hearer)
        if not triples:
            triples, speaker_mentions, hearer_mentions, subject_mentions, object_mentions = dep_to_triple.get_subj_attr_triples_with_spacy(
                nlp, utterance.transcript, speaker, hearer)
        if not triples:
            triples, speaker_mentions, hearer_mentions, subject_mentions, object_mentions = dep_to_triple.get_subj_prep_pobj_triples_with_spacy(
                nlp, utterance.transcript, speaker, hearer)

        if triples:
            for triple in triples:
                print("triple", triple)
                self.set_extracted_values(utterance_type=UtteranceType.STATEMENT, triple=triple)
        else:
            self._log.warning("Couldn't extract triples")

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
