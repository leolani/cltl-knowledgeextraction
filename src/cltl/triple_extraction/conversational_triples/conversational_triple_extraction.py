import math

import sys

sys.path.append('predicate_normalization')

from cltl.triple_extraction.conversational_triples.argument_extraction import ArgumentExtraction
from cltl.triple_extraction.conversational_triples.triple_scoring import TripleScoring
from cltl.triple_extraction.conversational_triples.post_processing import PostProcessor
from cltl.triple_extraction.conversational_triples.utils import pronoun_to_speaker_id, speaker_id_to_speaker, bio_tags_to_tokens
from itertools import product
import spacy

import logging

logger = logging.getLogger(__name__)


class AlbertTripleExtractor:
    def __init__(self, path: object, max_triples: int = 0, base_model: object = 'albert-base-v2', lang: object = "en") -> object:
        """ Constructor of the Albert-based Triple Extraction Pipeline.

        :param path:       path to savefile
        :param base_model: base model (default: albert-base-v2)
        :param sep:        separator token used to delimit dialogue turns (default: <eos>)
        :param speaker1:   name of user (default: speaker1)
        :param speaker2:   name of system (default: speaker2)
        """
        logger.debug("Loading model %s", path)
        self._argument_module = ArgumentExtraction(base_model, path=path)
        self._scoring_module = TripleScoring(base_model, path=path)
        self._base_model = base_model
        self._post_processor = PostProcessor()
        if lang=="nl":
            self._nlp = spacy.load('nl_core_news_sm')
        else:
            self._nlp = spacy.load('en_core_web_sm')

        self._sep = self._argument_module._tokenizer.decode(self._argument_module._tokenizer.sep_token_id)

        self._max_triples = max_triples

    @property
    def name(self):
        return "ALBERT"

    def _tokenize_with_speakers(self, dialog, speakers):
        """ Divides up the dialogue into separate turns and dereferences
            personal pronouns 'I' and 'you'.

        :param dialog: separator-delimited dialogue
        :return:       list of tokenized dialogue turns
        """
        print("DIALOG", dialog)
        # Split dialogue into turns
        turns = [turn.lower().strip() for turn in dialog.split(self._sep)]

        # Tokenize each turn separately (and splitting "n't" off)
        tokens = []
        for speaker, turn in zip(speakers, turns):
            # Assign speaker ID to turns (tn=1, tn-1=0, tn-2=1, etc.)
           # speaker_id = (len(turns) - turn_id + 1) % 2
            if speaker=="speaker1":
                speaker_id = 1
            else:
                speaker_id = 2
            if turn:
                tokens += [pronoun_to_speaker_id(t.lower_, speaker_id) for t in self._nlp(turn)] + [self._sep]
        return tokens

    def _tokenize(self, dialog):
        """ Divides up the dialogue into separate turns and dereferences
            personal pronouns 'I' and 'you'.

        :param dialog: separator-delimited dialogue
        :return:       list of tokenized dialogue turns
        """
        print("DIALOG", dialog)
        # Split dialogue into turns
        turns = [turn.lower().strip() for turn in dialog.split(self._sep)]

        # Tokenize each turn separately (and splitting "n't" off)
        tokens = []
        for turn_id, turn in enumerate(turns):
            # Assign speaker ID to turns (tn=1, tn-1=0, tn-2=1, etc.)
            speaker_id = (len(turns) - turn_id + 1) % 2
            if turn:
                tokens += [pronoun_to_speaker_id(t.lower_, speaker_id) for t in self._nlp(turn)] + [self._sep]
        return tokens

    # def simple_test(self, dialog, speaker1, speaker2):
    #     inputs = dialog.split()
    #     y_subj, y_pred, y_obj = self._argument_module.predict(inputs)
    #
    #     # show results
    #     for arg, y in [('Subject', y_subj), ('Predicate', y_pred), ('Object', y_obj)]:
    #         print('\n', arg)
    #         print('O\tB\tI')
    #         for score, token in zip(y.T, subwords):
    #             score_str = '\t'.join(
    #                 ["[" + str(s)[:5] + "]" if s == max(score) else " " + str(round(s, 4))[:5] + " " for s in score])
    #             token_str = token.replace('▁', '')
    #             print(score_str, token_str)
    #
    #     # Albert
    #     print(' '.join(subwords).replace('▁', '') + '\n')
    #     # MLBert
    #     print(' '.join(subwords).replace('##', '') + '\n')
    #
    #     print('Subjects:  ', bio_tags_to_tokens(subwords, y_subj.T, one_hot=True))
    #     print('Predicates:', bio_tags_to_tokens(subwords, y_pred.T, one_hot=True))
    #     print('Objects:   ', bio_tags_to_tokens(subwords, y_obj.T, one_hot=True))

    def extract_triples(self, speakers, dialog, speaker1, speaker2, post_process=True, batch_size=32, verbose=False):
        """
        :param dialog:       separator-delimited dialogue
        :param speaker1:       speaker of odd turns
        :param speaker2:       speaker of even turns
        :param post_process: Whether to apply rules to fix contractions and strip auxiliaries (like baselines)
        :param batch_size:   If a lot of possible triples exist, batch up processing
        :param verbose:      whether to print messages (True) or be silent (False) (default: False)
        :return:             A list of confidence-triple pairs of the form (confidence, (subj, pred, obj, polarity))
        """
        # Assign unambiguous tokens to you/I
        tokens = self._tokenize_with_speakers(dialog, speakers)

        # Extract SPO arguments from token sequence
        subjs, preds, objs = self._argument_module.predict(tokens)

        logger.debug('subjects:   %s' % subjs)
        logger.debug('predicates: %s' % preds)
        logger.debug('objects:    %s\n' % objs)

        # List all possible combinations of arguments
        # List all possible combinations of arguments
        if not subjs and preds and objs:
            candidates = [list(triple) for triple in product({'who'}, preds, objs)]
        elif subjs and preds and not objs:
            candidates = [list(triple) for triple in product(subjs, preds, {'what'})]
        elif subjs and not preds and objs:
            candidates = [list(triple) for triple in product(subjs, {'is'}, objs)]
        else:
            candidates = [list(triple) for triple in product(subjs, preds, objs)]
        if not candidates:
            return []

        if self._max_triples > 0:
            candidates = candidates[:int(math.ceil(self._max_triples / batch_size)) * batch_size]

        # Score candidate triples
        predictions = []
        for i in range(0, len(candidates), batch_size):
            batch = candidates[i:i + batch_size]
            for y_hat in self._scoring_module.predict(tokens, batch):
                predictions.append(y_hat)
        # Rank candidates according to entailment predictions
        triples = []
        for y_hat, (subj, pred, obj) in zip(predictions, candidates):
            pol = 'negative' if y_hat[2] > y_hat[1] else 'positive'
            ent = max(y_hat[1], y_hat[2])
            #print('y_hat', y_hat, ent)

            # Replace SPEAKER* with speaker
            subj = speaker_id_to_speaker(subj, speaker1, speaker2)
            pred = speaker_id_to_speaker(pred, speaker1, speaker2)
            obj = speaker_id_to_speaker(obj, speaker1, speaker2)

            # Fix mistakes, expand contractions
            if post_process:
                subj, pred, obj = self._post_processor.format((subj, pred, obj))
            triples.append((ent, (subj, pred, obj, pol)))

        return sorted(triples, key=lambda x: -x[0])


if __name__ == '__main__':
   # model = AlbertTripleExtractor(path='/Users/piek/Desktop/d-Leolani/leolani-models/conversational_triples/22_04_27', base_model='albert-base-v2', lang='en')

    model = AlbertTripleExtractor(path='/Users/piek/Desktop/d-Leolani/leolani-models/conversational_triples/2024-03-11', base_model='google-bert/bert-base-multilingual-cased', lang="en")
    SEP = model._sep
    # Test!
    examples = ["I enjoy watching american football but don\'t like to make homework " + SEP + " what does Mike like to do? " + SEP + " gaming, but I hate cats " + SEP]
    examples = ["Ik vind het leuk om naar voetbal te kijken maar ik hou niet van huiswerk " + SEP + " Wat zou mike graag willen doen? " + SEP + " gaming, maar ik heb een hekel aan katten " + SEP]
    speakers = ["speaker1", "speaker2", "speaker1"]
    #examples = ["I hope his school was n't too bad . I am also a mom both kids and pups ! " + SEP +  " Do you have any kids of your's own now ? " + SEP + " no " + SEP]
                #,
                #'I went to the new university. It was great! '+model._sep+' I like studying too and learning. You? ' + model._sep+ ' No, can afford it!'+model._sep,
                #'Ik ben naar de nieuwe universiteit gegaan. Het was geweldig! '+model._sep+' Ik hou ook van studeren en leren. Jij? ' +model._sep +' Nee, ik heb het niet nodig!'+model._sep]
    for example in examples:
        print('example', example)
        for score, triple in model.extract_triples(speakers, example, speaker1="Thomas", speaker2="LEOLANI"):
           print(score, triple)

### Albert:
# 0.99959534 ('Thomas', 'visit', 'the new university', 'positive')
# 0.9995055 ('it', 'be', 'great', 'positive')
# 0.9986526 ('LEOLANI', 'like', 'studying', 'positive')
# 0.9986406 ('Thomas', 'possible', 'it', 'positive')
# 0.99787045 ('Thomas', 'possible', 'the new university', 'positive')
# 0.9932249 ('LEOLANI', 'like', 'learning', 'positive')
# 0.96144116 ('Thomas', 'possible', 'studying', 'positive')
# 0.011400834 ('Thomas', 'like', 'studying', 'negative')
# 0.006049461 ('Thomas', 'like', 'learning', 'positive')
# 0.0032076072 ('LEOLANI', 'possible', 'it', 'positive')
# 0.0013780214 ('Thomas', 'like', 'the new university', 'positive')
# 0.0010418103 ('LEOLANI', 'like', 'the new university', 'positive')
# 0.0008511438 ('it', 'possible', 'it', 'positive')
# 0.00079880405 ('it', 'possible', 'studying', 'positive')
# 0.0007219936 ('it', 'possible', 'the new university', 'positive')
# 0.00072045357 ('Thomas', 'possible', 'learning', 'positive')
# 0.0007036675 ('LEOLANI', 'possible', 'the new university', 'positive')
# 0.0007000112 ('Thomas', 'visit', 'it', 'positive')
# 0.00068866526 ('Thomas', 'like', 'it', 'positive')
# 0.00068758824 ('LEOLANI', 'possible', 'studying', 'positive')
# 0.00066923944 ('it', 'possible', 'great', 'positive')
# 0.0006125862 ('it', 'possible', 'learning', 'positive')
# 0.0005751967 ('it', 'visit', 'studying', 'positive')
# 0.00054846046 ('Thomas', 'possible', 'great', 'positive')
# 0.00051013735 ('LEOLANI', 'like', 'it', 'positive')
# 0.0005035872 ('it', 'visit', 'the new university', 'positive')
# 0.00049910566 ('Thomas', 'be', 'it', 'positive')
# 0.00049432553 ('it', 'be', 'it', 'positive')
# 0.000473403 ('it', 'visit', 'great', 'positive')
# 0.00046508387 ('it', 'visit', 'it', 'positive')
# 0.00044310055 ('it', 'visit', 'learning', 'positive')
# 0.00044172764 ('Thomas', 'be', 'the new university', 'positive')
# 0.00044077839 ('LEOLANI', 'possible', 'great', 'positive')
# 0.00044015673 ('LEOLANI', 'be', 'it', 'positive')
# 0.0004345927 ('Thomas', 'like', 'great', 'positive')
# 0.0004202819 ('Thomas', 'visit', 'learning', 'positive')
# 0.00041443948 ('it', 'like', 'it', 'positive')
# 0.00039777264 ('Thomas', 'be', 'great', 'positive')
# 0.00039474334 ('it', 'like', 'studying', 'positive')
# 0.00039182068 ('Thomas', 'be', 'studying', 'positive')
# 0.00038896903 ('it', 'like', 'great', 'positive')
# 0.00038604366 ('it', 'like', 'learning', 'positive')
# 0.0003824353 ('it', 'be', 'the new university', 'positive')
# 0.0003821528 ('LEOLANI', 'visit', 'it', 'positive')
# 0.0003818124 ('LEOLANI', 'possible', 'learning', 'positive')
# 0.00037740736 ('it', 'like', 'the new university', 'positive')
# 0.0003731111 ('LEOLANI', 'be', 'the new university', 'positive')
# 0.00036376243 ('Thomas', 'visit', 'studying', 'positive')
# 0.00036373927 ('Thomas', 'visit', 'great', 'positive')
# 0.00036202974 ('LEOLANI', 'visit', 'the new university', 'positive')
# 0.0003549336 ('LEOLANI', 'be', 'studying', 'positive')
# 0.00034140534 ('Thomas', 'be', 'learning', 'positive')
# 0.00033830604 ('it', 'be', 'studying', 'positive')
# 0.00033441288 ('LEOLANI', 'visit', 'great', 'positive')
# 0.00032569116 ('LEOLANI', 'visit', 'studying', 'positive')
# 0.00032366754 ('LEOLANI', 'like', 'great', 'positive')
# 0.0003202108 ('it', 'be', 'learning', 'positive')
# 0.00030509668 ('LEOLANI', 'be', 'great', 'positive')
# 0.0002984874 ('LEOLANI', 'visit', 'learning', 'positive')
# 0.00025656258 ('LEOLANI', 'be', 'learning', 'positive')
# example Ik ben naar de nieuwe universiteit gegaan. Het was geweldig! <eos> Ik hou ook van studeren en leren. Jij? <eos> Nee, ik heb het niet nodig!
# 0.99862194 ('he', 'be', 'geweldig', 'positive')
# 0.2825692 ('Thomas', 'heb', 'geweldig', 'negative')
# 0.12623471 ('Thomas', 'be', 'geweldig', 'negative')
# 0.0031245297 ('he', 'heb', 'geweldig', 'positive')
