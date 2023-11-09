import logging
import json
from cltl.commons import discrete
from cltl.commons.triple_helpers import continuous_to_enum

from cltl.commons.discrete import UtteranceType
from cltl.commons.language_helpers import lexicon_lookup, lexicon, lexicon_lookup_subword, lexicon_lookup_subword_class
from cltl.commons.triple_helpers import fix_nlp_types
from cltl.triple_extraction.utils.helper_functions import get_triple_element_type, lemmatize, trim_dash, fix_pronouns

logger = logging.getLogger(__name__)

class TripleNormalizer():
    LEXICON = lexicon

    def __init__(self):
        # Load Grammar Json
        self._triple = self.initialize_triple()
        self.utterance = None
        self.prepositions = ["in", "of", "to", "for", "on", "at", "under", "above", "next", "after", "before"]
        self.modals = ["will", "can", "shall", "could", "would", "should", "may", "must", "might"]
        self.names= ['lenka', 'selene', 'suzana', 'bram', 'thomas', 'jaap', 'lea', 'annika', 'luis', 'lucia', 'piek']
        self.combot=["joe", "kerem", "carl", "anna", "lidia" , "carla", "jimmy", "estelle", "arthur", "zula", "angus", "frederique", "suzy", "marie", "yannis", "hermann"]


    def normalize(self, utterance, a_triple):
        """
        GeneralStatementAnalyzer factory function

        Parameters
        ----------
        utterance: Utterance
            utterance to be analyzed
        """

        # Initialize
        utterance_info = {'neg': False}
        self.utterance = utterance
        normalised_triple = a_triple
        logger.debug('initial triple: {}'.format(normalised_triple))

        ### We use preempted to catch words that have fixed predicates
        preempted = ""
        normalised_triple, utterance_info, preempted = self.get_kinship(normalised_triple, utterance_info)
        #if preempted: print('KINSHIP TRIPLE', preempted, triple)

        ## This is now a cascade, we could change this to get a list of triples and either vote or take them all
        if not preempted:
            normalised_triple, utterance_info, preempted = self.get_activity(normalised_triple, utterance_info)
            #if preempted: print('ACTIVITY TRIPLE',  preempted,normalised_triple)
            if not preempted:
                normalised_triple, utterance_info, preempted = self.get_condition(normalised_triple, utterance_info)
                #if preempted: print('CONDITION TRIPLE',  preempted,normalised_triple)
                if not preempted:
                    normalised_triple, utterance_info, preempted = self.get_location(normalised_triple, utterance_info)
                    #if preempted: print('LOCATION TRIPLE',  preempted,normalised_triple)
                    if not preempted:
                        normalised_triple, utterance_info, preempted = self.get_profession(normalised_triple, utterance_info)
                        #if preempted: print('PROFESSION TRIPLE',  preempted,normalised_triple)

        if preempted:
            #If preempteed we do not want to change the predicate again so only subject and object details are modified
            normalised_triple, utterance_info = self.fix_triple_details_subject_object(normalised_triple, utterance_info)
        else:
             # Fix phrases and multiword information
             normalised_triple, utterance_info = self.fix_triple_details(normalised_triple, utterance_info)

        # Extract perspective
        perspective = self.extract_perspective(normalised_triple, utterance_info)
        normalised_triple.update({"perspective": perspective})
        # Final triple assignment
        #print('FINAL NORMALISED TRIPLE', normalised_triple)

        return self.get_types_in_triple(normalised_triple)

    def initialize_triple(self):
        return NotImplementedError()


    def analyze_multiword_complement(self, triple):
        """
        This function analyses complex objects in statements
        :param triple: S,P,C triple
        :return: updated triple
        """
        first_word = triple['object'].split('-')[0]
        if first_word in self.prepositions:
            triple = self.analyze_complement_with_preposition(triple)

        elif lexicon_lookup(first_word) and 'person' in lexicon_lookup(first_word):
            triple = self.analyze_possessive(triple, 'object')

        # elif get_pos_in_tree(CFGAnalyzer.PARSER.structure_tree, first_word).startswith('V') \
        #         and get_pos_in_tree(CFGAnalyzer.PARSER.structure_tree, triple['predicate']) == 'MD':
        elif first_word in self.modals:
            triple['predicate'] += '-' + first_word
            triple['object'] = triple['object'].replace(first_word, '')
        return triple

    #@staticmethod
    # def analyze_certainty_statement(triple):
    #     """
    #     :param triple:
    #     :return:
    #     """
    #     index = 0
    #     for subtree in CFGAnalyzer.PARSER.constituents[2]['structure']:
    #         text = ''
    #         for leaf in subtree.leaves():
    #             if not (index == 0 and leaf == 'that'):
    #                 text += leaf + '-'
    #         if subtree.label() == 'VP':
    #             triple['predicate'] = text[:-1]
    #         elif subtree.label() == 'NP':
    #             triple['subject'] = text[:-1]
    #         else:
    #             triple['object'] = text[:-1]
    #         index += 1
    #     return triple

   # @staticmethod

    def extract_perspective(self, triple, utterance_info=None):
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

        ## Adapted since conversational triple extraction already gives values in triple
        if "perspective" in triple:
            if "polarity" in triple["perspective"]:
                polarity = triple["perspective"]["polarity"]
            if "certainty" in triple["perspective"]:
                certainty = triple["perspective"]["certainty"]

        predicate = triple['predicate']['label']
        for word in predicate.split('-'):
            word = lemmatize(word)  # with a pos tag ?
            if word == 'not' and polarity==1:
                utterance_info['neg'] = -1
            entry = lexicon_lookup(word, 'verb')
            if entry:
                if 'sentiment' in entry:
                    sentiment = entry['sentiment']
                if 'certainty' in entry and certainty==1:
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
                logger.warning("Cannot find {} in statement".format(el))
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
                logger.warning("Cannot find {} in statement".format(el))
                return False
        return True

    def set_extracted_values(self, utterance_type=None, triple=None, perspective={}):
        # Pack everything together
        triple["perspective"] = perspective
        triple["utterance_type"] = utterance_type

        # Set type, and triple
        triple_is_new = self.utterance.add_triple(triple)

        if not triple_is_new:
            return

        if utterance_type:
            self._log_info("Utterance type: {}".format(json.dumps(utterance_type.name,
                                                                  sort_keys=True, separators=(', ', ': '))))

        if triple:
            for el in ["subject", "predicate", "object"]:
                self._log_info("RDF triplet {:>10}: {}".format(el, json.dumps(triple[el],
                                                                              sort_keys=True, separators=(', ', ': '))))
        if triple["perspective"]:
            for el in ['certainty', 'polarity', 'sentiment', 'emotion']:
                cls = getattr(discrete, el.title())
                closest = continuous_to_enum(cls, triple["perspective"][el])
                self._log_info("Perspective {:>10}: {}".format(el, closest.name))

    def fix_triple_details(self, triple, utterance_info):
        # Analyze verb phrase
        # triple, utterance_info = self.analyze_vp(triple, utterance_info)
        # logger.debug('after VP: {}'.format(triple))

        # Analyze noun phrase
        triple = self.analyze_np(triple)
        logger.debug('after NP: {}'.format(triple))

        # Analyze object
        if len(triple['object'].split('-')) > 1:  # multi-word object, consisting of a phrase
            triple = self.analyze_multiword_complement(triple)
        elif len(triple['object'].split('-')) == 1:
            triple = self.analyze_one_word_complement(triple)
        logger.debug('after object analysis: {}'.format(triple))

        # Analyze subject
        if len(triple['subject'].split('-')) > 1:  # multi-word subject
            triple = self.analyze_multiword_subject(triple)
        elif len(triple['subject'].split('-')) == 1:
            triple = self.analyze_one_word_subject(triple)
        logger.debug('after subject analysis: {}'.format(triple))

        # Final fixes to triple
        triple = trim_dash(triple)
        triple['predicate'] = self.fix_predicate(triple['predicate'])
        logger.debug('after predicate fix: {}'.format(triple))

        # Get triple types
        triple = self.get_types_in_triple(triple)
        logger.debug('final triple: {} {}'.format(triple, utterance_info))

        return triple, utterance_info


    def fix_triple_details_subject_object(self, triple, utterance_info):
        # Analyze noun phrase
        triple = self.analyze_np(triple)
        logger.debug('after NP: {}'.format(triple))
        # Analyze object
        if not triple['object'] == None:
            # print(triple['object'])
            if len(triple['object'].split('-')) > 1:  # multi-word object, consisting of a phrase
                # print('multi-word object, consisting of a phrase', triple['object'])
                triple = self.analyze_multiword_complement(triple)
            elif len(triple['object'].split('-')) == 1:
                triple = self.analyze_one_word_complement(triple)
            logger.debug('after object analysis: {}'.format(triple))

        # Analyze subject
        if triple['subject']:
            if len(triple['subject'].split('-')) > 1:  # multi-word subject
                triple = self.analyze_multiword_subject(triple)
            elif len(triple['subject'].split('-')) == 1:
                triple = self.analyze_one_word_subject(triple)
            logger.debug('after subject analysis: {}'.format(triple))

        # Get triple types
        triple = self.get_types_in_triple(triple)
        logger.debug('final triple: {} {}'.format(triple, utterance_info))

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
            #
            # if get_pos_in_tree(CFGAnalyzer.PARSER.structure_tree, predicate) in ['IN', 'TO']:
            #     predicate = 'be-' + predicate
            # elif predicate == '':
            #     predicate = 'be'

        if predicate == 'hat':  # lemmatizer issue with verb 'hate'
            predicate = 'hate'

        elif predicate == 'bear':  # bear-in
            predicate = 'born'  # lemmatizer issue

        elif predicate == 'bear-in':  # bear-in
            predicate = 'born'  # lemmatizer issue

        return predicate


    def get_types_in_triple(self, triple):
        """
        This function gets types for all the elements of the triple
        :param triple: S,P,C triple
        :return: triple dictionary with types
        """
        # Get type
        for el in triple:
            if type(triple[el])==dict:
                continue
            if el=="perspective":
                continue
            text = triple[el]
            final_type = []
            triple[el] = {'label': text, 'type': []}

            # If no text was extracted we cannot get a type
            if text == '':
                continue

            # First attempt at typing via forest
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
                            elif typ.lower() in self.names:
                                final_type.append('person')
                            elif typ.lower() in self.combot:
                                final_type.append('person')
                            elif typ.capitalize() == typ:
                                final_type.append('None')  ## This was person before, now it should trigger the type infenence function in the brain
                            else:
                                final_type.append('None')
                        elif 'proximity' in entry:
                            final_type.append('deictic')
                        elif 'person' in entry:
                            final_type.append('pronoun')

                    else:
                        final_type.append(triple[el]['type'][typ])

                final_type = fix_nlp_types(final_type)
                triple[el]['type'] = final_type
            # Patch special types
            elif triple[el]['type'] in [None, ''] or triple[el]['type']==[]:
                entry = ''
                token = ''
                if 'text' in triple[el]:
                    token = triple[el]['text']
                elif 'label' in triple[el]:
                    token = triple[el]['label']

                entry = lexicon_lookup(token)
                if entry is None:

                    # TODO: Remove Hardcoded Names
                    if token.lower() in ['leolani']:
                        triple[el]['type'] = ['robot']
                    elif token.lower() in self.names:
                        triple[el]['type'] = ['person']
                    elif token.lower() in self.combot:
                        triple[el]['type'] = ['person']
                    elif token.capitalize() == token:
                        triple[el]['type'] = [
                            'None']  ## This was person before, now it should trigger the type infenence function in the brain
                elif 'proximity' in entry:
                    triple[el]['type'] = ['deictic']

        return triple


    def get_kinship(self, triple, utterance_info):
        kinship_word = ""
        if triple['predicate'] == "be" or triple['predicate'] == "is":
            predicate, kinship_word = lexicon_lookup_subword(triple['subject'], 'kinship')
            if predicate and kinship_word:
                triple['predicate'] = predicate
                first = triple['subject'].split("-")[0].lower()
                last = triple['subject'].split("-")[-1]
                #  print('predicate', predicate, 'first', first, 'last', last)
                triple['subject'] = triple['object']
                if first == 'my':
                    triple['object'] = self.utterance._chat_speaker
                elif first == "your":
                    triple['object'] = self.utterance._chat_agent
                else:
                    triple['object'] = first

            #   print('s-kinship', triple)
            else:
                predicate, kinship_word = lexicon_lookup_subword(triple['object'], 'kinship')
                if predicate and kinship_word:
                    # my kinship is obj
                    triple['predicate'] = predicate
                    first = triple['object'].split("-")[0].lower()
                    if first == 'my':
                        triple['object'] = self.utterance._chat_speaker
                    elif first == 'your':
                        triple['object'] = self.utterance._chat_agent
                #   print('o-kinship', triple)
        elif triple['predicate'] == "have" or triple['predicate'] == "has":
            # my kinship is obj
            predicate, kinship_word = lexicon_lookup_subword(triple['object'], 'kinship')
            if predicate and kinship_word:
                triple['predicate'] = predicate
                last = triple['object'].split("-")[-1]
                if triple['subject'].lower() == 'i':
                    triple['object'] = self.utterance._chat_speaker
                elif triple['subject'].lower() == 'you':
                    triple['object'] = self.utterance._chat_agent
                else:
                    triple['object'] = triple['subject']
                if not last == kinship_word:
                    triple['subject'] = last
                else:
                    triple['subject'] = 'someone'
            #   print('o-kinship', triple)
        elif triple['predicate'] == "is-named" or triple['predicate'] == "is-called" or triple['predicate'] == "is-married":
            predicate, kinship_word = lexicon_lookup_subword(triple['subject'], 'kinship')
            if predicate and kinship_word:
                triple['predicate'] = predicate
                first = triple['subject'].split("-")[0].lower()
                last = triple['subject'].split("-")[-1]
                #   print('predicate', predicate, 'first', first, 'last', last)
                triple['subject'] = triple['object']
                if first == 'my':
                    triple['object'] = self.utterance._chat_speaker
                elif first == "your":
                    triple['object'] = self.utterance._chat_agent
                else:
                    triple['object'] = first
            #  print('s-kinship-called', triple)
        #  print('predicative reading triple', triple)
        return triple, utterance_info, kinship_word


    def get_activity(self, triple, utterance_info):
        activity_markers = ["be-to","have-been","has-been","was-at","was-to","were-at","were-to","am-at","am-to","go","went","go-to","went-to","attend","attended","watch","watched","watching","see","seeing","saw","play","plays","played","visit","visits","visited","listen","listens","listening","listen-to"]
        activity_word = ""

        lemma = lemmatize(triple['predicate'], 'v')
        if lemma in activity_markers:
            predicate, activity_word = lexicon_lookup_subword(triple['object'], 'activities')
            if predicate and activity_word:
                triple['predicate'] = predicate
                triple['object'] = activity_word
            #  print('o-activity', triple)
        # else:
        #    print('predicate lemmatisation', triple['predicate'], lemmatize(triple['predicate'], "v"))
        # print('predicative reading triple', triple)
        return triple, utterance_info, activity_word


    def get_condition(self, triple, utterance_info):
        condition_word = ""
        lemma = lemmatize(triple['predicate'], 'v')
        if lemma == "be":
            predicate, condition_word = lexicon_lookup_subword(triple['object'], 'feelings')
            if predicate and condition_word:
                triple['predicate'] = predicate
                triple['object'] = condition_word
            # print('o-condition', triple)
        elif lemma == "feel":
            # my kinship is obj
            predicate, condition_word = lexicon_lookup_subword(triple['object'], 'feelings')
            if predicate and condition_word:
                triple['predicate'] = predicate
                triple['object'] = condition_word
            # print('o-condition', triple)
        # print('predicative reading triple', triple)
        return triple, utterance_info, condition_word


    def get_location(self, triple, utterance_info):
        container_word = ""
        lemma = lemmatize(triple['predicate'], 'v')

        if lemma == "be" and ( triple['object'].startswith("in-") or triple['object'].startswith("on-")):
            container_word = lexicon_lookup_subword_class(triple['object'], 'containers')
            if container_word:
                triple['predicate'] = "be-inside"
                ### We keep the full object phrase, take out comment to use the container word
                ##triple['object'] =  container_word
            # print('container_word', triple)
        elif lemma == "be" and triple['object'].startswith("next-to-"):
            container_word = lexicon_lookup_subword_class(triple['object'], 'containers')
            if container_word:
                triple['predicate'] = "be-next-to"
                ### We keep the full object phrase, take out comment to use the container word
                ##triple['object'] =  container_word
                triple['object'] = triple['object'].split('next-to-')[1]
            # print('container_word', triple)
        # print('predicative reading triple', triple)
        return triple, utterance_info, container_word


    def get_profession(self, triple, utterance_info):
        profession_word = ""
        lemma = lemmatize(triple['predicate'], 'v')
        if lemma == "be":
            profession_word = lexicon_lookup_subword_class(triple['object'], 'professions')
            if profession_word:
                triple['predicate'] = "work-as"
                triple['object'] = profession_word
            # print('container_word', triple)
        if lemma == "work" and triple['object'].startswith("as-"):
            triple['predicate'] = "work-as"
            triple['object'] = profession_word
        # print('predicative reading triple', triple)
        return triple, utterance_info, profession_word


    # def analyze_vp(self, triple, utterance_info):
    #     """
    #     This function analyzes verb phrases
    #     :param triple: triple (subject, predicate, object)
    #     :param utterance_info: the result of analysis thus far
    #     :return: triple and utterance info, updated with the results of VP analysis
    #     """
    #     pred = ''
    #     ind = 0
    #
    #     # one word predicate is just lemmatized
    #     if len(triple['predicate'].split('-')) == 1:
    #         # prepositions are joined to the predicate and removed from the object
    #         label = get_pos_in_tree(CFGAnalyzer.PARSER.structure_tree, triple['predicate'])
    #
    #         triple['predicate'] = lemmatize(triple['predicate'], 'v')
    #
    #         if triple['predicate'] == 'cannot':  # special case with no space between not and verb
    #             triple['predicate'] = 'can'
    #             utterance_info['neg'] = True
    #         ####
    #
    #         if label in ['IN', 'TO']:
    #             pred += '-' + triple['predicate']
    #             for elem in triple['predicate'].split('-')[ind + 1:]:
    #                 triple['object'] = elem + '-' + triple['object']
    #             triple['predicate'] = pred
    #         ####
    #         return triple, utterance_info
    #
    #     # complex predicate
    #     for el in triple['predicate'].split('-'):
    #         label = get_pos_in_tree(CFGAnalyzer.PARSER.structure_tree, el)
    #         # negation
    #         if label == 'RB':
    #             if el in ['not', 'never', 'no']:
    #                 utterance_info['neg'] = True
    #
    #         # verbs that carry sentiment or certainty are considered followed by their object
    #         elif lexicon_lookup(lemmatize(el, 'v'), 'lexical'):
    #             pred += '-' + lemmatize(el, 'v')
    #             for elem in triple['predicate'].split('-')[ind + 1:]:
    #                 label = get_pos_in_tree(CFGAnalyzer.PARSER.structure_tree, elem)
    #                 if label in ['TO', 'IN', 'RB']:
    #                     pred += '-' + elem
    #                 else:
    #                     triple['object'] = elem + '-' + triple['object']
    #             triple['predicate'] = pred
    #             break
    #
    #         # prepositions are joined to the predicate and removed from the object
    #         elif label in ['IN', 'TO']:
    #             pred += '-' + el
    #             for elem in triple['predicate'].split('-')[ind + 1:]:
    #                 triple['object'] = elem + '-' + triple['object']
    #             triple['predicate'] = pred
    #             break
    #
    #         # auxiliary verb
    #         elif lexicon_lookup(el, 'aux'):  # and not triple['predicate'].endswith('-is'):
    #             utterance_info['aux'] = lexicon_lookup(el, 'aux')
    #
    #         # verb or modal verb
    #         elif label.startswith('V') or label in ['MD']:
    #             if pred == '':
    #                 pred = lemmatize(el, 'v')
    #             else:
    #                 pred += '-' + lemmatize(el, 'v')
    #
    #         else:
    #             logger.debug('uncaught verb phrase element {}:{}'.format(el, label))
    #
    #         ind += 1
    #
    #     if pred == '':
    #         pred = 'be'
    #
    #     triple['predicate'] = pred
    #     return triple, utterance_info


    def analyze_np(self, triple):
        """
        This function analyses noun phrases
        :param triple: S,P,C triple
        :return: triple with updated elements
        """

        label = triple['subject']
        # multi-word subject (possessive phrase)
        if len(label.split('-')) > 1:
            first_word = label.split('-')[0].lower()
            if lexicon_lookup(first_word) and 'person' in lexicon_lookup(first_word):
                triple = self.analyze_possessive(triple, 'subject')

            if 'not-' in label:  # for sentences that start with negation "haven't you been to London?"
                triple['subject'] = triple['subject'].replace('not-', '')

        else:  # one word subject
            triple['subject'] = fix_pronouns(triple['subject'].lower(), self.utterance._chat_speaker,
                                             self.utterance._chat_agent)
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
            objct = fix_pronouns(first_word, self.utterance._chat_speaker, self.utterance._chat_agent)

            for word in triple['object'].split('-')[1:]:
                objct += '-' + word

            triple['object'] = objct

        else:

            subject = fix_pronouns(first_word, self.utterance.chat_speaker, self.utterance._chat_agent)
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
        elif len(triple['predicate'].split(
                "-")) == 1:  ## this checks prevents that predicate that are already augmented with particles are not extended
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
                subject = fix_pronouns(triple['subject'].lower(), self.utterance._chat_speaker, self.utterance._chat_agent)
                pred = ''
                for el in triple['subject'].split('-')[1:]:
                    pred += el + '-'
                triple['predicate'] = pred + 'is'
                triple['object'] = triple['subject'].split('-')[0]
                triple['subject'] = subject
            else:
                triple['object'] = fix_pronouns(triple['object'].lower(), self.utterance._chat_speaker,
                                                self.utterance._chat_agent)
        # elif get_pos_in_tree(CFGAnalyzer.PARSER.structure_tree, triple['subject']).startswith('V') \
        #         and get_pos_in_tree(CFGAnalyzer.PARSER.structure_tree, triple['predicate']) == 'MD':
        elif triple['predicate'] in self.modals:
             triple['predicate'] += '-' + triple['subject']
             triple['object'] = ''
        return triple


    def analyze_one_word_complement(self, triple):
        """
        This function analyses one word objects and updates the triple
        :param triple: S,P,C triple
        :return: updated triple
        """
        modals = ["will", "can", "shall", "could", "would", "should", "may", "must", "might"]
        # TODO
        if lexicon_lookup(triple['object']) and 'person' in lexicon_lookup(triple['object']):
            if triple['predicate'] == 'be':
                subject = fix_pronouns(triple['object'].lower(), self.utterance._chat_speaker, self.utterance._chat_agent)
                pred = ''
                for el in triple['subject'].split('-')[1:]:
                    pred += el + '-'
                triple['predicate'] = pred + 'is'
                triple['object'] = triple['subject'].split('-')[0]
                triple['subject'] = subject
            else:
                triple['object'] = fix_pronouns(triple['object'].lower(), self.utterance._chat_speaker,
                                                self.utterance._chat_agent)
        elif triple['predicate'] in modals:
            triple['predicate'] += '-' + triple['object']
            triple['object'] = ''
        return triple


    def analyze_multiword_subject(self, triple):
        first_word = triple['subject'].split('-')[0]
        if first_word in self.prepositions:
            triple = self.analyze_subject_with_preposition(triple)

        if lexicon_lookup(first_word) and 'person' in lexicon_lookup(first_word):
            triple = self.analyze_possessive(triple, 'subject')

        return triple

    def _log_info(self, message):
        logger.info("%s: %s", self.__class__.__name__, message)