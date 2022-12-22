from cltl.commons.discrete import UtteranceType
from cltl.triple_extraction.analyzer import Analyzer
from cltl.triple_extraction.api import Chat
from cltl.triple_extraction.conversational_triples.conversational_triple_extraction import AlbertTripleExtractor

THRESHOLD = 0.8
MODEL_PATH = "/Users/piek/Desktop/d-Leolani/cltl-knowledgeextraction/src/cltl/triple_extraction/conversational_triples/models/2022-04-27"
class conversationalAnalyzer(Analyzer):

    def __init__(self):
        """
        spaCy Analyzer Object

        Parameters
        ----------
        """

        super(conversationalAnalyzer, self).__init__()
        self._extractor = AlbertTripleExtractor(path=MODEL_PATH)

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

    def analyze_in_context(self, chat):
        """
        Analyzer factory function

        Find appropriate Analyzer for this utterance

        Parameters
        ----------
        utterance: Utterance
            utterance to be analyzed

        """
        super(conversationalAnalyzer, self).analyze_in_context(chat)

        self._chat = chat

        self._utterance = chat.last_utterance
        self._extractor._speaker1 =chat.speaker
        self._extractor._speaker2 =chat.agent

        conversation  = "<eos><eos>"+chat.last_utterance.transcript
        if len(chat.utterances)>2:
            conversation = chat.utterances[-2].transcript+"<eos>"+ chat.utterances[-1].transcript+"<eos>" + chat.last_utterance.transcript
        elif len(chat.utterances)==2:
            conversation = "<eos>"+ chat.utterances[-1].transcript+"<eos>" + chat.last_utterance.transcript

        print("conversation", conversation)
        # subjects: {'SPEAKER1', 'it', 'SPEAKER2'}
        # predicates: {'like', 'hate', 'was', 'went to'}
        # objects: {'studying', 'great', 'learning', 'the new university', 'it'}

        # 0.9995951('HUMAN', 'went to', 'the new university', 'positive')
        # 0.9994972('it', 'was', 'great', 'positive')
        # 0.99911314('HUMAN', 'hate', 'the new university', 'positive')
        # 0.99910575('HUMAN', 'hate', 'it', 'positive')
        # 0.99836904('LEOLANI', 'like', 'studying', 'positive')
        # 0.9970577('HUMAN', 'hate', 'studying', 'positive')
        # 0.9905161('LEOLANI', 'like', 'learning', 'positive')
        # 0.99003685('LEOLANI', 'hate', 'it', 'positive')
        # 0.4502159('LEOLANI', 'hate', 'studying', 'positive')

        triples = []
        for score, triple_value in self._extractor.extract_triples(conversation):
            if score>=THRESHOLD:
                if len(triple_value)>2:
                    triple = {"subject" : triple_value[0], "predicate" : triple_value[1], "object" : triple_value[2]}
                if len(triple_value)==4:
                    triple["perspective"]={"polarity" : triple_value[3]}
                if len(triple_value)==5:
                    triple["perspective"]={"certainty" : triple_value[3]}

                self.set_extracted_values(utterance_type=UtteranceType.STATEMENT, triple=triple)
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
    analyzer = conversationalAnalyzer()
    utterances = ["I love cats.", "Do you also love dogs?", "No I do not."]
    chat = Chat("Leolani", "Lenka")
    for utterance in utterances:
        chat.add_utterance(utterance)
        analyzer.analyze_in_context(chat)
    for utterance in chat.utterances:
        print(utterance)
        print('Final triples', utterance.triples)
