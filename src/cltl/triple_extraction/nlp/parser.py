import os

from nltk import CFG, RecursiveDescentParser
from nltk import pos_tag

from cltl.triple_extraction import logger
from cltl.triple_extraction.nlp.ner import NER
from cltl.triple_extraction.nlp.pos import POS


class Parser(object):
    POS_TAGGER = None  # Type: POS
    NER_TAGGER = None
    GRAMMAR = None
    CFG_GRAMMAR_FILE = os.path.join(os.path.dirname(__file__), '../data', 'cfg.txt')

    def __init__(self):
        self._log = logger.getChild(self.__class__.__name__)

        if not Parser.POS_TAGGER:
            Parser.POS_TAGGER = POS()

        if not Parser.NER_TAGGER:
            Parser.NER_TAGGER = NER()

        with open(Parser.CFG_GRAMMAR_FILE) as cfg_file:
            if not Parser.GRAMMAR:
                Parser.GRAMMAR = cfg_file.read()
                self._log.debug("Loaded grammar")
            self._cfg = Parser.GRAMMAR

    @property
    def forest(self):
        return self._forest

    @property
    def constituents(self):
        return self._constituents

    @property
    def structure_tree(self):
        return self._structure_tree

    def parse(self, utterance):
        """
        :param utterance: an Utterance object, typically last one in the Chat
        :return: parsed syntax tree and a dictionary of syntactic realizations
        """
        self._log.debug("Start parsing")
        tokenized_sentence = utterance.tokens
        pos = self.POS_TAGGER.tag(tokenized_sentence)  # stanford
        alternative_pos = pos_tag(tokenized_sentence)  # nltk

        self._log.debug(pos)
        self._log.debug(alternative_pos)

        if pos != alternative_pos:
            self._log.debug('DIFFERENT POS tag: %s != %s' % (pos, alternative_pos))

        # fixing issues with POS tagger (Does and like)
        ind = 0
        for w in tokenized_sentence:
            if w == 'like':
                pos[ind] = (w, 'VB')
            ind += 1

        if pos and pos[0][0] == 'Does':
            pos[0] = ('Does', 'VBD')

        # the POS tagger returns one tag with a $ sign (POS$) and this needs to be fixed for the CFG parsing
        ind = 0
        for word, tag in pos:
            if '?' in word:
                word = word[:-1]
            if tag.endswith('$'):
                new_rule = tag[:-1] + 'POS -> \'' + word + '\'\n'
                pos[ind] = (pos[ind][0], 'PRPPOS')
            else:
                # CFG grammar is created dynamically, with the terminals added each time from the specific utterance
                new_rule = tag + ' -> \'' + word + '\'\n'
            if new_rule not in self._cfg:
                self._cfg += new_rule
            ind += 1

        try:
            cfg_parser = CFG.fromstring(self._cfg)
            rd = RecursiveDescentParser(cfg_parser)

            last_token = tokenized_sentence[len(tokenized_sentence) - 1]

            if '?' in last_token:
                tokenized_sentence[len(tokenized_sentence) - 1] = last_token[:-1]

            parsed = rd.parse(tokenized_sentence)

            s_r = {}  # syntactic_realizations are the topmost branches, usually VP/NP
            index = 0

            forest = [tree for tree in parsed]

            if len(forest):
                if (len(forest)) > 1:
                    self._log.debug('* Ambiguity in grammar *')
                for tree in forest[0]:  # alternative trees? f
                    for branch in tree:
                        s_r[index] = {'label': branch.label(), 'structure': branch}
                        raw = ''
                        for node in branch:
                            for leaf in node.leaves():
                                raw += leaf + '-'

                        s_r[index]['raw'] = raw[:-1]
                        index += 1
            else:
                self._log.debug("no forest")

            for el in s_r:
                if type(s_r[el]['raw']) == list:
                    string = ''
                    for e in s_r[el]['raw']:
                        string += e + ' '
                    s_r[el]['raw'] = string
                s_r[el]['raw'] = s_r[el]['raw'].strip()

            self._forest = forest
            self._constituents = s_r
            self._structure_tree = self.forest[0] if self.forest else None

        except:
            self._forest = []
            self._constituents = {}
            self._structure_tree = None
