import logging

from cltl.commons.discrete import UtteranceType
from cltl.triple_extraction.analyzer import Analyzer
from cltl.triple_extraction.api import Chat
from cltl.triple_extraction.conversational_triples.conversational_triple_extraction import AlbertTripleExtractor

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
        if chat.last_utterance.chat_speaker == chat.speaker:
            self._chat = chat

            self._utterance = chat.last_utterance
            self._extractor._speaker1 =chat.speaker
            self._extractor._speaker2 =chat.agent
            conversation  = "<eos><eos>"+chat.last_utterance.transcript
            if len(chat.utterances)>2:
                conversation = chat.utterances[-2].transcript+"<eos>"+ chat.utterances[-1].transcript+"<eos>" + chat.last_utterance.transcript
            elif len(chat.utterances)==2:
                conversation = "<eos>"+ chat.utterances[-1].transcript+"<eos>" + chat.last_utterance.transcript

            for score, triple_value in self._extractor.extract_triples(conversation):
                if score>=THRESHOLD:
                    if len(triple_value)>2:
                        triple = {"subject" : {"label": triple_value[0], "type": [], "uri": None},
                                  "predicate" : {"label": triple_value[1], "type": [], "uri": None},
                                  "object" : {"label": triple_value[2], "type": [], "uri": None}
                                  }
                    if len(triple_value)==4:
                        triple["perspective"]={"polarity" : triple_value[3]}
                    if len(triple_value)==5:
                        triple["perspective"]={"certainty" : triple_value[3]}

                    self.set_extracted_values(utterance_type=UtteranceType.STATEMENT, triple=triple)
        if triples:
            for triple in triples:
                logger.debug("triple: %s", triple)
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

    @property
    def utterance(self):
        return self._chat.last_utterance


if __name__ == "__main__":
    '''
    test files with triples are formatted like so "test sentence : subject predicate object" 
    multi-word-expressions have dashes separating their elements, and are marked with apostrophes if they are a 
    collocation
    '''
    model = "/Users/tkb/automatic/workspaces/robo/leolani-mmai-parent/cltl-leolani-app/py-app/resources/conversational_triples"

    analyzer = ConversationalAnalyzer(model)
    utterances = ["I love cats.", "Do you also love dogs?", "No I do not."]
    chat = Chat("Leolani", "Lenka")
    for utterance in utterances:
        chat.add_utterance(utterance)
        analyzer.analyze_in_context(chat)
    for utterance in chat.utterances:
        print(utterance)
        print('Final triples', utterance.triples)
