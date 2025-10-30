

import logging

from cltl.commons.discrete import UtteranceType
from cltl.triple_extraction.analyzer import Analyzer
from cltl.triple_extraction.api import Chat
from transformers import pipeline

logger = logging.getLogger(__name__)

# https://github.com/Babelscape/rebel
class RebelAnalyzer(Analyzer):
    def __init__(self):
        """
        spaCy Analyzer Object

        Parameters
        ----------
        """
        super().__init__()
        self._rebel = pipeline('text2text-generation', model='Babelscape/rebel-large', tokenizer='Babelscape/rebel-large')

        self._utterance = None

    @property
    def utterance(self):
        return self._utterance

    def analyze_in_context(self, chat: Chat):
        self.analyze(chat.last_utterance)

    # TODO this doesn't match the Analyzer interface!
    def analyze(self, chat):
        """
        Analyzer factory function

        Find appropriate Analyzer for this utterance

        Parameters
        ----------
        utterance: Utterance
            utterance to be analyzed

        """
        self._utterance = chat.last_utterance
        # speaker = chat.speaker
        # hearer = chat.agent

        # We need to use the tokenizer manually since we need special tokens.
        extracted_text = self._rebel.tokenizer.batch_decode([self._rebel(self._utterance.transcript, return_tensors=True, return_text=False)[0]["generated_token_ids"]])
        triples = self.extract_triplets(extracted_text[0])
        if triples:
            for triple in triples:
                self.set_extracted_values(utterance_type=UtteranceType.STATEMENT, triple=triple)
        else:
            logger.warning("Couldn't extract triples")


    def extract_triplets(self, text):
        triplets = []
        relation, subject, relation, object_ = '', '', '', ''
        text = text.strip()
        current = 'x'
        print(text)
        for token in text.replace("<s>", "").replace("<pad>", "").replace("</s>", "").split():
            if token == "<triplet>":
                current = 't'
                if relation != '':
                    triplets.append({'subject': subject.strip(), 'predicate': relation.strip(),'object': object_.strip()})
                    relation = ''
                subject = ''
            elif token == "<subj>":
                current = 's'
                if relation != '':
                    triplets.append({'subject': subject.strip(), 'predicate': relation.strip(),'object': object_.strip()})
                object_ = ''
            elif token == "<obj>":
                current = 'o'
                relation = ''
            else:
                if current == 't':
                    subject += ' ' + token
                elif current == 's':
                    object_ += ' ' + token
                elif current == 'o':
                    relation += ' ' + token
        if subject != '' and relation != '' and object_ != '':
            triplets.append({'subject': subject.strip(), 'predicate': relation.strip(),'object': object_.strip()})
        return triplets


if __name__ == "__main__":
    '''
    test files with triples are formatted like so "test sentence : subject predicate object" 
    multi-word-expressions have dashes separating their elements, and are marked with apostrophes if they are a 
    collocation
    '''
    #
    utterance = "Bram lives in New Tork."
    utterance = "I love cats."
    #utterance = "Punta Cana is a resort town in the municipality of Higuey, in La Altagracia Province, the eastern most province of the Dominican Republic"
    chat = Chat("Leolani", "Lenka")
    analyzer = RebelAnalyzer()
    chat.add_utterance(utterance, utterance_speaker=chat.speaker, dialogue_acts=[UtteranceType.STATEMENT])
    analyzer.analyze(chat)
    print(chat.last_utterance.triples)