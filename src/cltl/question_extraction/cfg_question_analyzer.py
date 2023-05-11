import logging

from cltl.commons.discrete import UtteranceType
from cltl.commons.language_helpers import lexicon_lookup, lexicon
from cltl.triple_extraction.analyzer import Analyzer
from cltl.triple_extraction.cfg_analyzer import CFGAnalyzer
from cltl.triple_extraction.api import Chat
from cltl.triple_extraction.nlp.parser import Parser
from cltl.triple_extraction.utils.helper_functions import get_pos_in_tree

logger = logging.getLogger(__name__)


class CFGQuestionAnalyzer(Analyzer):
    cfgAnalyzer = CFGAnalyzer()
    # Load Grammar Json
    cfgAnalyzer.LEXICON = lexicon

    # Load ntlk Tree generated by the CFG parser
    # TODO: Optimize: takes 2.6 seconds now! Should be < 1 second!?
    cfgAnalyzer.PARSER = Parser()
    def __init__(self):
        """
        Abstract Analyzer Object

        Parameters
        ----------
        """
        self._utterance = None

    @property
    def utterance(self):
        return self._utterance

    def analyze(self, utterance):
        """
        CFGAnalyzer factory function

        Find appropriate CFGAnalyzer for this utterance

        Parameters
        ----------
        utterance: Utterance
            utterance to be analyzed

        """
        self._utterance = utterance
        self.cfgAnalyzer._utterance = utterance
        self.cfgAnalyzer.PARSER.parse(utterance)
        if not self.cfgAnalyzer.PARSER.forest:
            logger.warning("Couldn't parse input")

        else:
            logger.info(f'Found {len(self.cfgAnalyzer.PARSER.forest)} triples')

            for tree in self.cfgAnalyzer.PARSER.forest:
                sentence_type = tree[0].label()

                try:
                    if sentence_type == 'Q':
                        analyzer = QuestionAnalyzer()
                        analyzer.cfgAnalyzer.analyze(utterance)

                    else:
                        logger.warning("Error: {}".format(sentence_type))

                except Exception as e:
                    logger.warning("Couldn't extract triples")
                    logger.exception(e)

    def initialize_triple(self):
        return NotImplementedError()


class QuestionAnalyzer(CFGQuestionAnalyzer):
    """Abstract QuestionAnalyzer Object: call QuestionAnalyzer.analyze(utterance) factory function"""

    def __init__(self):
        """
        Statement Analyzer Object

        Parameters
        ----------
        """

        super().__init__()

    def analyze(self, utterance):
        """
        QuestionAnalyzer factory function

        Find appropriate QuestionAnalyzer for this utterance

        Parameters
        ----------
        utterance: Utterance
            utterance to be analyzed
        """

        self._utterance = utterance

        if utterance.tokens:
            first_word = utterance.tokens[0]
            if first_word.lower() in self.cfgAnalyzer.LEXICON['question words']:
                analyzer = WhQuestionAnalyzer()
                analyzer.analyze(utterance)

            else:
                analyzer = VerbQuestionAnalyzer()
                analyzer.analyze(utterance)


class WhQuestionAnalyzer(QuestionAnalyzer):

    def __init__(self):
        """
        Wh-Question Analyzer

        Parameters
        ----------
        """

        super().__init__()

    def analyze(self, utterance):
        """
        WhQuestionAnalyzer factory function

        Parameters
        ----------
        utterance: Utterance
            utterance to be analyzed
        """

        self.cfgAnalyzer._utterance = utterance

        # Initialize
        utterance_info = {'neg': False,
                          'wh_word': lexicon_lookup(self.cfgAnalyzer.PARSER.constituents[0]['raw'].lower())}
        triple = self.initialize_triple()
        logger.debug('initial triple: {}'.format(triple))
        if triple:
            # Fix phrases and multiword information
            triple, utterance_info = self.cfgAnalyzer.fix_triple_details(triple, utterance_info)

            # Final triple assignment
            self.cfgAnalyzer.set_extracted_values(utterance_type=UtteranceType.QUESTION, triple=triple)

    def initialize_triple(self):
        """
        This function initializes the triple for wh_questions with the assumed word order:
                aux before predicate, subject before object
        :return: initial S,P,O triple
        """

        triple = {'predicate': '', 'subject': '', 'object': ''}
        constituents = self.cfgAnalyzer.PARSER.constituents
        if len(constituents) == 3:
            label = get_pos_in_tree(self.cfgAnalyzer.PARSER.structure_tree, constituents[2]['raw'])
            if constituents[0]['raw'].lower() == 'who':
                triple['predicate'] = constituents[1]['raw']
                triple['object'] = constituents[2]['raw']
            elif label.startswith('V') or label == 'MD':  # rotation "(do you know) what a dog is?"s
                triple['subject'] = constituents[1]['raw']
                triple['predicate'] = constituents[2]['raw']
            else:
                triple['predicate'] = constituents[1]['raw']
                triple['subject'] = constituents[2]['raw']

        elif len(constituents) == 4:
            label = get_pos_in_tree(self.cfgAnalyzer.PARSER.structure_tree, constituents[1]['raw'])
            if not (label.startswith('V') or label == 'MD'):
                triple['subject'] = constituents[3]['raw']
                triple['predicate'] = constituents[2]['raw']
            else:
                triple['subject'] = constituents[2]['raw']
                triple['predicate'] = constituents[1]['raw'] + '-' + constituents[3]['raw']

        elif len(constituents) == 5:
            triple['predicate'] = constituents[1]['raw'] + '-' + constituents[3]['raw']
            triple['subject'] = constituents[2]['raw']
            triple['object'] = constituents[4]['raw']
        else:
            logger.debug('MORE CONSTITUENTS %s %s'.format(len(constituents), constituents))

        return triple

    def analyze_multiword_complement(self, triple):
        first_word = triple['object'].split('-')[0]

        if get_pos_in_tree(self.cfgAnalyzer.PARSER.structure_tree, first_word) in ['TO', 'IN']:
            triple = self.cfgAnalyzer.analyze_complement_with_preposition(triple)

        if lexicon_lookup(first_word) and 'person' in lexicon_lookup(first_word):
            triple = self.cfgAnalyzer.analyze_possessive(triple, 'object')

        return triple


class VerbQuestionAnalyzer(QuestionAnalyzer):

    def __init__(self, ):
        """
        Verb Question Analyzer

        Parameters
        ----------
        """

        super().__init__()

    def analyze(self, utterance):
        """
        VerbQuestionAnalyzer factory function

        Parameters
        ----------
        utterance: Utterance
            utterance to be analyzed
        """

        self._utterance = utterance

        # Initialize
        utterance_info = {'neg': False}
        triple = self.initialize_triple()
        logger.debug('initial triple: {}'.format(triple))

        # Fix phrases and multiword information
        triple, utterance_info = self.cfgAnalyzer.fix_triple_details(triple, utterance_info)

        # Final triple assignment
        self.cfgAnalyzer.set_extracted_values(utterance_type=UtteranceType.QUESTION, triple=triple)

    def initialize_triple(self):
        triple = {'predicate': '', 'subject': '', 'object': ''}

        constituents = self.cfgAnalyzer.PARSER.constituents
        triple['subject'] = constituents[1]['raw']

        if len(constituents) == 4:
            triple['predicate'] = constituents[0]['raw'] + '-' + constituents[2]['raw']
            triple['object'] = constituents[3]['raw']
        elif len(constituents) == 3:
            triple['predicate'] = constituents[0]['raw']
            triple['object'] = constituents[2]['raw']
        else:
            logger.debug('MORE CONSTITUENTS %s %s'.format(len(constituents), constituents))
        return triple

if __name__ == "__main__":
    analyzer = CFGQuestionAnalyzer()
    chat = Chat("Leolani", "Lenka")

    texts = ["What tracks users?", "who can sing", "what can sing"]
    for text in texts:
        try:

            chat.add_utterance(text)
            analyzer.analyze(chat.last_utterance)
            print(chat.last_utterance)
            print(chat.last_utterance.triples)
        except Exception as e:
            print("Exception:", text)
            raise e

