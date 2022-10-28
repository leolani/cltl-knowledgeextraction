from cltl.commons.discrete import UtteranceType
from cltl.commons.language_helpers import lexicon_lookup, lexicon, lexicon_lookup_subword
from cltl.commons.triple_helpers import fix_nlp_types

from cltl.triple_extraction.analyzer import Analyzer
from cltl.triple_extraction.nlp.parser import Parser
from cltl.triple_extraction.utils.helper_functions import get_triple_element_type, lemmatize, trim_dash, fix_pronouns, \
    get_pos_in_tree


class CFGAnalyzer(Analyzer):
    # Load Grammar Json
    LEXICON = lexicon

    # Load ntlk Tree generated by the CFG parser
    # TODO: Optimize: takes 2.6 seconds now! Should be < 1 second!?
    PARSER = Parser()

    def __init__(self):
        """
        Abstract Analyzer Object

        Parameters
        ----------
        """

        super(CFGAnalyzer, self).__init__()

    def analyze(self, utterance):
        """
        CFGAnalyzer factory function

        Find appropriate CFGAnalyzer for this utterance

        Parameters
        ----------
        utterance: Utterance
            utterance to be analyzed

        """

        super(CFGAnalyzer, self).analyze(utterance)

        CFGAnalyzer.PARSER.parse(utterance)
        ###PIEK
        print(CFGAnalyzer.PARSER.constituents)
        if not CFGAnalyzer.PARSER.forest:
            self._log.warning("Couldn't parse input")

        else:
            self._log.info(f'Found {len(CFGAnalyzer.PARSER.forest)} triples')

            for tree in CFGAnalyzer.PARSER.forest:
                sentence_type = tree[0].label()

                try:
                    if sentence_type == 'S':
                        analyzer = StatementAnalyzer()
                        analyzer.analyze(utterance)

                    elif sentence_type == 'Q':
                        analyzer = QuestionAnalyzer()
                        analyzer.analyze(utterance)

                    else:
                        self._log.warning("Error: {}".format(sentence_type))

                except Exception as e:
                    self._log.warning("Couldn't extract triples")
                    self._log.exception(e)

    def initialize_triple(self):
        return NotImplementedError()

    def analyze_multiword_complement(self, triple):
        return NotImplementedError()

    def fix_triple_details(self, triple, utterance_info):
        # Analyze verb phrase
        triple, utterance_info = self.analyze_vp(triple, utterance_info)
        self._log.debug('after VP: {}'.format(triple))

        # Analyze noun phrase
        triple = self.analyze_np(triple)
        self._log.debug('after NP: {}'.format(triple))

        # Analyze object
        if len(triple['object'].split('-')) > 1:  # multi-word object, consisting of a phrase
            triple = self.analyze_multiword_complement(triple)
        elif len(triple['object'].split('-')) == 1:
            triple = self.analyze_one_word_complement(triple)
        self._log.debug('after object analysis: {}'.format(triple))

        # Analyze subject
        if len(triple['subject'].split('-')) > 1:  # multi-word subject
            triple = self.analyze_multiword_subject(triple)
        elif len(triple['subject'].split('-')) == 1:
            triple = self.analyze_one_word_subject(triple)
        self._log.debug('after subject analysis: {}'.format(triple))

        # Final fixes to triple
        triple = trim_dash(triple)
        triple['predicate'] = self.fix_predicate(triple['predicate'])
        self._log.debug('after predicate fix: {}'.format(triple))

        # Get triple types
        triple = self.get_types_in_triple(triple)
        self._log.debug('final triple: {} {}'.format(triple, utterance_info))

        return triple, utterance_info

    @staticmethod
    def fix_predicate(predicate):
        """
        This function returns the lemmatized predicate and fixes the errors with lemmatizing
        :param predicate: predicate to lemmatize
        :return: lemmatized predicate
        """

        if '-' not in predicate:
            predicate = lemmatize(predicate, 'v')

            if get_pos_in_tree(CFGAnalyzer.PARSER.structure_tree, predicate) in ['IN', 'TO']:
                predicate = 'be-' + predicate
            elif predicate == '':
                predicate = 'be'

        if predicate == 'hat':  # lemmatizer issue with verb 'hate'
            predicate = 'hate'

        elif predicate == 'bear':  # bear-in
            predicate = 'born'  # lemmatizer issue

        elif predicate == 'bear-in':  # bear-in
            predicate = 'born'  # lemmatizer issue

        return predicate

    @staticmethod
    def get_types_in_triple(triple):
        """
        This function gets types for all the elements of the triple
        :param triple: S,P,C triple
        :return: triple dictionary with types
        """
        # Get type
        for el in triple:
            text = triple[el]
            final_type = []
            triple[el] = {'label': text, 'type': []}

            # If no text was extracted we cannot get a type
            if text == '':
                continue

            # First attempt at typing via forest
            triple[el]['type'] = get_triple_element_type(text, CFGAnalyzer.PARSER.structure_tree)

            # Analyze types
            if type(triple[el]['type']) == dict:
                # Loop through dictionary for multiword entities
                for typ in triple[el]['type']:
                    # If type is None or empty, look it up
                    if triple[el]['type'][typ] in [None, '']:
                        entry = lexicon_lookup(typ)

                        if entry is None:
                            if typ.lower() in ['leolani']:
                                final_type.append('robot')
                            elif typ.lower() in ['lenka', 'selene', 'suzana', 'bram',
                                                 'piek'] or typ.capitalize() == typ:
                                final_type.append('person')
                            else:
                                node = get_pos_in_tree(CFGAnalyzer.PARSER.structure_tree, typ)
                                if node in ['IN', 'TO']:
                                    final_type.append('preposition')
                                elif node.startswith('V'):
                                    final_type.append('verb')
                                elif node.startswith('N'):
                                    final_type.append('noun')

                        elif 'proximity' in entry:
                            final_type.append('deictic')
                        elif 'person' in entry:
                            final_type.append('pronoun')

                    else:
                        final_type.append(triple[el]['type'][typ])

                final_type = fix_nlp_types(final_type)
                triple[el]['type'] = final_type

            # Patch special types
            elif triple[el]['type'] in [None, '']:
                entry = lexicon_lookup(triple[el]['text'])
                if entry is None:

                    # TODO: Remove Hardcoded Names
                    if triple[el]['text'].lower() in ['leolani']:
                        triple[el]['type'] = ['robot']
                    elif triple[el]['text'].lower() in ['lenka', 'selene', 'suzana', 'bram', 'piek']:
                        triple[el]['type'] = ['person']
                    elif triple[el]['text'].capitalize() == triple[el]['text']:
                        triple[el]['type'] = ['person']
                elif 'proximity' in entry:
                    triple[el]['type'] = ['deictic']

        return triple

    def _get_predicative_reading(self, triple):
        if triple['predicate']=="be":
            #my name is
            if triple['subject']=='name':
                triple['predicate']= 'label'
                #print('name', triple)

            predicate, name = lexicon_lookup_subword(triple['subject'], 'kinship')
            if predicate:
                triple['predicate']= predicate
                if name:
                    triple['object'] = name
                else:
                    triple['object'] = 'someone'
                # print('s-kinship', triple)
            #my kinship is obj
            predicate, name = lexicon_lookup_subword(triple['object'], 'kinship')
            if predicate:
                triple['predicate']= predicate
                if name:
                    triple['object'] = name
                else:
                    triple['object'] = 'someone'
                    # print('o-kinship', triple)
            predicate, name = lexicon_lookup_subword(triple['object'], 'condition')
            print
            if predicate:
                triple['predicate']= 'condition'
               # print('o-condition', triple)
        elif triple['predicate']=="have":
            # my kinship is obj
            predicate, name = lexicon_lookup_subword(triple['object'], 'kinship')
            if predicate:
                triple['predicate'] = predicate
                if name:
                    triple['object'] = name
                else:
                    triple['object'] = 'someone'
              #  print('o-kinship', triple)
        else:
            # activity
            predicate, name = lexicon_lookup_subword(triple['object'], 'activities')
            if predicate:
                triple['predicate'] = 'experience'
                triple['object'] = predicate
              #  print('o-activity', triple)


    def analyze_vp(self, triple, utterance_info):
        """
        This function analyzes verb phrases
        :param triple: triple (subject, predicate, object)
        :param utterance_info: the result of analysis thus far
        :return: triple and utterance info, updated with the results of VP analysis
        """
        pred = ''
        ind = 0

        # one word predicate is just lemmatized
        if len(triple['predicate'].split('-')) == 1:
            # prepositions are joined to the predicate and removed from the object
            label = get_pos_in_tree(CFGAnalyzer.PARSER.structure_tree, triple['predicate'])

            triple['predicate'] = lemmatize(triple['predicate'], 'v')

            if triple['predicate'] == 'cannot':  # special case with no space between not and verb
                triple['predicate'] = 'can'
                utterance_info['neg'] = True
            ####

            if label in ['IN', 'TO']:
                pred += '-' + triple['predicate']
                for elem in triple['predicate'].split('-')[ind + 1:]:
                    triple['object'] = elem + '-' + triple['object']
                triple['predicate'] = pred
            ####
            return triple, utterance_info

        # complex predicate
        for el in triple['predicate'].split('-'):
            label = get_pos_in_tree(CFGAnalyzer.PARSER.structure_tree, el)
            # negation
            if label == 'RB':
                if el in ['not', 'never', 'no']:
                    utterance_info['neg'] = True

            # verbs that carry sentiment or certainty are considered followed by their object
            elif lexicon_lookup(lemmatize(el, 'v'), 'lexical'):
                pred += '-' + lemmatize(el, 'v')
                for elem in triple['predicate'].split('-')[ind + 1:]:
                    label = get_pos_in_tree(CFGAnalyzer.PARSER.structure_tree, elem)
                    if label in ['TO', 'IN']:
                        pred += '-' + elem
                    else:
                        triple['object'] = elem + '-' + triple['object']
                triple['predicate'] = pred
                break

            # prepositions are joined to the predicate and removed from the object
            elif label in ['IN', 'TO']:
                pred += '-' + el
                for elem in triple['predicate'].split('-')[ind + 1:]:
                    triple['object'] = elem + '-' + triple['object']
                triple['predicate'] = pred
                break

            # auxiliary verb
            elif lexicon_lookup(el, 'aux'):  # and not triple['predicate'].endswith('-is'):
                utterance_info['aux'] = lexicon_lookup(el, 'aux')

            # verb or modal verb
            elif label.startswith('V') or label in ['MD']:
                if pred == '':
                    pred = lemmatize(el, 'v')
                else:
                    pred += '-' + lemmatize(el, 'v')

            else:
                self._log.debug('uncaught verb phrase element {}:{}'.format(el, label))

            ind += 1

        if pred == '':
            pred = 'be'

        triple['predicate'] = pred
        return triple, utterance_info

    def analyze_np(self, triple):
        """
        This function analyses noun phrases
        :param triple: S,P,C triple
        :return: triple with updated elements
        """

        # multi-word subject (possessive phrase)
        if len(triple['subject'].split('-')) > 1:
            first_word = triple['subject'].split('-')[0].lower()
            if lexicon_lookup(first_word) and 'person' in lexicon_lookup(first_word):
                triple = self.analyze_possessive(triple, 'subject')

            if 'not-' in triple['subject']:  # for sentences that start with negation "haven't you been to London?"
                triple['subject'] = triple['subject'].replace('not-', '')

        else:  # one word subject
            triple['subject'] = fix_pronouns(triple['subject'].lower(), self.utterance.chat_speaker)
        return triple

    def analyze_possessive(self, triple, element):
        """
        This function analyses possessive phrases, which start with pos. pronoun
        :param triple: subject, predicate, object triple
        :param element: element of the triple which has the possessive phrase
        :return: updated triple
        """
        first_word = triple[element].split('-')[0]

        if element == 'object':
            objct = fix_pronouns(first_word, self.utterance.chat_speaker)

            for word in triple['object'].split('-')[1:]:
                objct += '-' + word

            triple['object'] = objct

        else:

            subject = fix_pronouns(first_word, self.utterance.chat_speaker)
            predicate = ''
            for word in triple[element].split('-')[1:]:
                # words that express people are grouped together in the subject
                if (lexicon_lookup(word, 'kinship') or lexicon_lookup(lemmatize(word, 'n'),
                                                                      'kinship')) or word == 'best':
                    subject += '-' + word
                else:
                    predicate += '-' + word
            if element == 'object':
                triple['object'] = triple['subject']

            # properties are stored with a suffix "-is"
            if predicate:
                triple['predicate'] = predicate + '-is'

            triple['subject'] = subject

        return triple

    @staticmethod
    def analyze_subject_with_preposition(triple):
        """
        This function analyses triple object which starts with a preposition and updates the triple
        :param triple: S,P,C triple
        :return: updated triple
        """
        if lexicon_lookup(triple['predicate'], 'aux') or lexicon_lookup(triple['predicate'], 'modal'):
            triple['predicate'] += '-be-' + triple['subject'].split('-')[0]
        else:
            triple['predicate'] += '-' + triple['subject'].split('-')[0]

        triple['subject'] = triple['subject'].replace(triple['subject'].split('-')[0], '', 1)[1:]
        return triple

    @staticmethod
    def analyze_complement_with_preposition(triple):
        """
        This function analyses triple object which starts with a preposition and updates the triple
        :param triple: S,P,C triple
        :return: updated triple
        """
        if lexicon_lookup(triple['predicate'], 'aux') or lexicon_lookup(triple['predicate'], 'modal'):
            triple['predicate'] += '-be-' + triple['object'].split('-')[0]
        else:
            triple['predicate'] += '-' + triple['object'].split('-')[0]
        triple['object'] = triple['object'].replace(triple['object'].split('-')[0], '', 1)[1:]
        return triple

    def analyze_one_word_subject(self, triple):
        """
        This function analyses one word objects and updates the triple
        :param triple: S,P,C triple
        :return: updated triple
        """

        # TODO
        if lexicon_lookup(triple['subject']) and 'person' in lexicon_lookup(triple['subject']):
            if triple['predicate'] == 'be':
                subject = fix_pronouns(triple['subject'].lower(), self.utterance.chat_speaker)
                pred = ''
                for el in triple['subject'].split('-')[1:]:
                    pred += el + '-'
                triple['predicate'] = pred + 'is'
                triple['object'] = triple['subject'].split('-')[0]
                triple['subject'] = subject
            else:
                triple['object'] = fix_pronouns(triple['object'].lower(), self.utterance.chat_speaker)
        elif get_pos_in_tree(CFGAnalyzer.PARSER.structure_tree, triple['subject']).startswith('V') \
                and get_pos_in_tree(CFGAnalyzer.PARSER.structure_tree, triple['predicate']) == 'MD':
            triple['predicate'] += '-' + triple['subject']
            triple['object'] = ''
        return triple

    def analyze_one_word_complement(self, triple):
        """
        This function analyses one word objects and updates the triple
        :param triple: S,P,C triple
        :return: updated triple
        """

        # TODO
        if lexicon_lookup(triple['object']) and 'person' in lexicon_lookup(triple['object']):
            if triple['predicate'] == 'be':
                subject = fix_pronouns(triple['object'].lower(), self.utterance.chat_speaker)
                pred = ''
                for el in triple['subject'].split('-')[1:]:
                    pred += el + '-'
                triple['predicate'] = pred + 'is'
                triple['object'] = triple['subject'].split('-')[0]
                triple['subject'] = subject
            else:
                triple['object'] = fix_pronouns(triple['object'].lower(), self.utterance.chat_speaker)
        elif get_pos_in_tree(CFGAnalyzer.PARSER.structure_tree, triple['object']).startswith('V') \
                and get_pos_in_tree(CFGAnalyzer.PARSER.structure_tree, triple['predicate']) == 'MD':
            triple['predicate'] += '-' + triple['object']
            triple['object'] = ''
        return triple

    def analyze_multiword_subject(self, triple):
        first_word = triple['subject'].split('-')[0]

        if get_pos_in_tree(CFGAnalyzer.PARSER.structure_tree, first_word) in ['TO', 'IN']:
            triple = self.analyze_subject_with_preposition(triple)

        if lexicon_lookup(first_word) and 'person' in lexicon_lookup(first_word):
            triple = self.analyze_possessive(triple, 'subject')

        return triple


class StatementAnalyzer(CFGAnalyzer):
    """Abstract StatementAnalyzer Object: call StatementAnalyzer.analyze(utterance) factory function"""

    def __init__(self):
        """
        Statement Analyzer Object

        Parameters
        ----------
        """

        super(StatementAnalyzer, self).__init__()

    def analyze(self, utterance):
        """
        StatementAnalyzer factory function

        Find appropriate StatementAnalyzer for this utterance

        Parameters
        ----------
        utterance: Utterance
            utterance to be analyzed
        """

        super(CFGAnalyzer, self).analyze(utterance)

        analyzer = GeneralStatementAnalyzer()
        analyzer.analyze(utterance)


class GeneralStatementAnalyzer(StatementAnalyzer):

    def __init__(self):
        """
        General Statement Analyzer

        Parameters
        ----------
        """

        super(GeneralStatementAnalyzer, self).__init__()

    def analyze(self, utterance):
        """
        GeneralStatementAnalyzer factory function

        Parameters
        ----------
        utterance: Utterance
            utterance to be analyzed
        """

        super(CFGAnalyzer, self).analyze(utterance)

        # Initialize
        utterance_info = {'neg': False}
        triple = self.initialize_triple()
        ### This fixes clauses in which the main verb is a copula or auxilairy and the predicate/property is actually the complement
        self._get_predicative_reading(triple)
        self._log.debug('initial triple: {}'.format(triple))

        # sentences such as "I think (that) ..."
        entry = lexicon_lookup(lemmatize(triple['predicate'], 'v'), 'lexical')
        if entry and 'certainty' in entry:
            if CFGAnalyzer.PARSER.constituents[2]['label'] == 'S':
                utterance_info['certainty'] = entry['certainty']
                triple = self.analyze_certainty_statement(triple)

        # Fix phrases and multiword information
        triple, utterance_info = self.fix_triple_details(triple, utterance_info)

        # Extract perspective
        perspective = self.extract_perspective(triple['predicate']['label'], utterance_info)

        # Final triple assignment
        self.set_extracted_values(utterance_type=UtteranceType.STATEMENT, triple=triple, perspective=perspective)

    def initialize_triple(self):
        """
        This function initializes the triple with assumed word order: NP VP C
        subject is the NP, predicate is VP and object can be NP, VP, PP, another S or nothing
        """
        triple = {'subject': CFGAnalyzer.PARSER.constituents[0]['raw'],
                  'predicate': CFGAnalyzer.PARSER.constituents[1]['raw'],
                  'object': CFGAnalyzer.PARSER.constituents[2]['raw']}
        return triple

    def analyze_multiword_complement(self, triple):
        """
        This function analyses complex objects in statements
        :param triple: S,P,C triple
        :return: updated triple
        """
        first_word = triple['object'].split('-')[0]

        if get_pos_in_tree(CFGAnalyzer.PARSER.structure_tree, first_word) in ['TO', 'IN']:
            triple = self.analyze_complement_with_preposition(triple)

        elif lexicon_lookup(first_word) and 'person' in lexicon_lookup(first_word):
            triple = self.analyze_possessive(triple, 'object')

        elif get_pos_in_tree(CFGAnalyzer.PARSER.structure_tree, first_word).startswith('V') \
                and get_pos_in_tree(CFGAnalyzer.PARSER.structure_tree, triple['predicate']) == 'MD':

            triple['predicate'] += '-' + first_word
            triple['object'] = triple['object'].replace(first_word, '')

        return triple

    @staticmethod
    def analyze_certainty_statement(triple):
        """
        :param triple:
        :return:
        """
        index = 0
        for subtree in CFGAnalyzer.PARSER.constituents[2]['structure']:
            text = ''
            for leaf in subtree.leaves():
                if not (index == 0 and leaf == 'that'):
                    text += leaf + '-'
            if subtree.label() == 'VP':
                triple['predicate'] = text[:-1]
            elif subtree.label() == 'NP':
                triple['subject'] = text[:-1]
            else:
                triple['object'] = text[:-1]
            index += 1
        return triple

    @staticmethod
    def extract_perspective(predicate, utterance_info=None):
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

        for word in predicate.split('-'):
            word = lemmatize(word)  # with a pos tag ?
            if word == 'not':
                utterance_info['neg'] = -1
            entry = lexicon_lookup(word, 'verb')
            if entry:
                if 'sentiment' in entry:
                    sentiment = entry['sentiment']
                if 'certainty' in entry:
                    certainty = entry['certainty']

        if 'certainty' in utterance_info:
            certainty = utterance_info['certainty']

        if utterance_info['neg']:
            polarity = -1

        perspective = {'sentiment': float(sentiment), 'certainty': float(certainty), 'polarity': float(polarity),
                       'emotion': float(emotion)}
        return perspective

    def check_triple_completeness(self, triple):
        """
        This function checks whether an extracted triple is complete
        :param triple: S,P,C triple
        :return: True if the triple has all three elements, False otherwise
        """
        for el in ['predicate', 'subject', 'object']:
            if not triple[el] or not len(triple[el]):
                self._log.warning("Cannot find {} in statement".format(el))
                return False
        return True

    def check_perspective_completeness(self, perspective):
        """
        This function checks whether an extracted perspective is complete
        :param perspective: sentiment, certainty, polarity, emotion perspective
        :return: True if the perspective has all four elements, False otherwise
        """
        for el in ['sentiment', 'certainty', 'polarity', 'emotion']:
            if not perspective[el] or not len(perspective[el]):
                self._log.warning("Cannot find {} in statement".format(el))
                return False
        return True


class ObjectStatementAnalyzer(StatementAnalyzer):
    def __init__(self, ):
        """
        Object Statement Analyzer

        Parameters
        ----------
        """

        super(ObjectStatementAnalyzer, self).__init__()


class QuestionAnalyzer(CFGAnalyzer):
    """Abstract QuestionAnalyzer Object: call QuestionAnalyzer.analyze(utterance) factory function"""

    def __init__(self):
        """
        Statement Analyzer Object

        Parameters
        ----------
        """

        super(QuestionAnalyzer, self).__init__()

    def analyze(self, utterance):
        """
        QuestionAnalyzer factory function

        Find appropriate QuestionAnalyzer for this utterance

        Parameters
        ----------
        utterance: Utterance
            utterance to be analyzed
        """

        super(CFGAnalyzer, self).analyze(utterance)

        if utterance.tokens:
            first_word = utterance.tokens[0]
            if first_word.lower() in CFGAnalyzer.LEXICON['question words']:
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

        super(WhQuestionAnalyzer, self).__init__()

    def analyze(self, utterance):
        """
        WhQuestionAnalyzer factory function

        Parameters
        ----------
        utterance: Utterance
            utterance to be analyzed
        """

        super(CFGAnalyzer, self).analyze(utterance)

        # Initialize
        utterance_info = {'neg': False,
                          'wh_word': lexicon_lookup(CFGAnalyzer.PARSER.constituents[0]['raw'].lower())}
        triple = self.initialize_triple()
        self._log.debug('initial triple: {}'.format(triple))

        # Fix phrases and multiword information
        triple, utterance_info = self.fix_triple_details(triple, utterance_info)

        # Final triple assignment
        self.set_extracted_values(utterance_type=UtteranceType.QUESTION, triple=triple)

    def initialize_triple(self):
        """
        This function initializes the triple for wh_questions with the assumed word order:
                aux before predicate, subject before object
        :return: initial S,P,O triple
        """

        triple = {'predicate': '', 'subject': '', 'object': ''}
        constituents = CFGAnalyzer.PARSER.constituents
        if len(constituents) == 3:
            label = get_pos_in_tree(CFGAnalyzer.PARSER.structure_tree, constituents[2]['raw'])
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
            label = get_pos_in_tree(CFGAnalyzer.PARSER.structure_tree, constituents[1]['raw'])
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
            self._log.debug('MORE CONSTITUENTS %s %s'.format(len(constituents), constituents))

        return triple

    def analyze_multiword_complement(self, triple):
        first_word = triple['object'].split('-')[0]

        if get_pos_in_tree(CFGAnalyzer.PARSER.structure_tree, first_word) in ['TO', 'IN']:
            triple = self.analyze_complement_with_preposition(triple)

        if lexicon_lookup(first_word) and 'person' in lexicon_lookup(first_word):
            triple = self.analyze_possessive(triple, 'object')

        return triple


class VerbQuestionAnalyzer(QuestionAnalyzer):

    def __init__(self, ):
        """
        Verb Question Analyzer

        Parameters
        ----------
        """

        super(VerbQuestionAnalyzer, self).__init__()

    def analyze(self, utterance):
        """
        VerbQuestionAnalyzer factory function

        Parameters
        ----------
        utterance: Utterance
            utterance to be analyzed
        """

        super(CFGAnalyzer, self).analyze(utterance)

        # Initialize
        utterance_info = {'neg': False}
        triple = self.initialize_triple()
        self._log.debug('initial triple: {}'.format(triple))

        # Fix phrases and multiword information
        triple, utterance_info = self.fix_triple_details(triple, utterance_info)

        # Final triple assignment
        self.set_extracted_values(utterance_type=UtteranceType.QUESTION, triple=triple)

    def initialize_triple(self):
        triple = {'predicate': '', 'subject': '', 'object': ''}

        constituents = CFGAnalyzer.PARSER.constituents
        triple['subject'] = constituents[1]['raw']

        if len(constituents) == 4:
            triple['predicate'] = constituents[0]['raw'] + '-' + constituents[2]['raw']
            triple['object'] = constituents[3]['raw']
        elif len(constituents) == 3:
            triple['predicate'] = constituents[0]['raw']
            triple['object'] = constituents[2]['raw']
        else:
            self._log.debug('MORE CONSTITUENTS %s %s'.format(len(constituents), constituents))
        return triple

    def analyze_multiword_complement(self, triple):

        first_word = triple['object'].split('-')[0]

        if get_pos_in_tree(CFGAnalyzer.PARSER.structure_tree, first_word) in ['IN', 'TO']:
            triple = self.analyze_complement_with_preposition(triple)

        elif lexicon_lookup(first_word) and 'person' in lexicon_lookup(first_word):
            triple = self.analyze_possessive(triple, 'object')

        elif get_pos_in_tree(CFGAnalyzer.PARSER.structure_tree, first_word).startswith('V') \
                and get_pos_in_tree(CFGAnalyzer.PARSER.structure_tree, triple['predicate']) == 'MD':

            for word in triple['object'].split('-'):
                label = get_pos_in_tree(CFGAnalyzer.PARSER.structure_tree, word)
                if label in ['IN', 'TO', 'MD'] or label.startswith('V'):
                    triple['predicate'] += '-' + word
                    triple['object'] = triple['object'].replace(word, '')

        elif triple['predicate'].endswith('-is'):
            triple['predicate'] = triple['predicate'][:-3]
            for word in triple['object'].split('-')[:-1]:
                triple['predicate'] += '-' + word
            triple['object'] = triple['object'].split('-')[len(triple['object'].split('-')) - 1]
            triple['predicate'] += '-is'

        return triple
