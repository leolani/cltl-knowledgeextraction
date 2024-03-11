import glob
import json
import random
import re
from collections import defaultdict
from copy import deepcopy

import numpy as np


def load_annotations(path, remove_unk=True, keep_skipped=False):
    """ Reads all annotation files from path. By default, it filters skipped
        files and removes the [unk] tokens appended at the end of each turn.

        params:
        str path:           name of directory containing annotations
        bool remove_unk:    whether to remove [unk] tokens (default: True)
        bool keep_skipped:  whether to keep skipped annotations (default: False)

        returns:    list of annotations dicts
    """
    annotations = []
    for fname in glob.glob(path + '/*.json'):
        with open(fname, 'r', encoding='utf-8') as file:
            data = json.load(file)

            if data['skipped'] and not keep_skipped:
                continue

            if remove_unk:
                data['tokens'] = [[t for t in turn if t != '[unk]'] for turn in data['tokens']]

            annotations.append(data)

    return annotations


def triple_to_bio_tags(annotation, arg):
    """ Converts the token indices of the annotations to a vector of BIO labels
        for an argument.

        params:
        dict annotation:    loaded annotation file (see load_annotations)
        int arg:            argument to create tag sequence for (subj=0, pred=1, obj=2)

        returns:    ndarray with BIO labels (I=2, B=1, O=0)
    """
    # Determine length of dialogue
    turns = annotation['tokens']
    triples = annotation['annotations']
    num_tokens = sum([len(turn) + 1 for turn in turns])  # +1 for <eos>

    # Create vector same size as dialogue
    mask = np.zeros(num_tokens, dtype=np.uint8)

    # Label annotated arguments as BIO tags
    for triple in triples:
        for j, (turn_id, token_id) in enumerate(triple[arg]):
            k = sum([len(t) + 1 for t in turns[:turn_id]]) + token_id  # k = index of token in dialogue
            mask[k] = 1 if j == 0 else 2
    return mask


def bio_tags_to_tokens(tokens, mask, one_hot=False):
    """ Converts a vector of BIO-tags into spans of tokens. If BIO-tags are one-hot encoded,
        one_hot=True will first perform an argmax to obtain the BIO labels.

        params:
        list tokens:    list of subwords or tokens (as tokenized by Albert/AutoTokenizer)
        ndarray mask:   list of bio labels (one for each subword or token in 'tokens')
        bool one_hot:   whether to interpret mask as a one-hot encoded sequence of shape |sequence|x3
    """
    out = []
    span = []
    for i, token in enumerate(tokens):
        pred = mask[i]

        # Reverse one-hot encoding (optional)
        if one_hot:
            pred = np.argmax(pred)

        if pred == 1:  # B
            if len(span)<2:
                span = re.sub('[^\w\d\-\']+', ' ', ''.join(span)).strip()
                span = span.replace('SPEAKER', ' SPEAKER').replace('speaker', ' speaker').strip()
            out.append(span)
            span = [token]

        elif pred == 2:  # I
            if token.startswith('##'):
                span[-1]=span[-1]+token[2:]
            elif token.startswith('_'):
                span[-1]=span[-1]+token[1:]
            else:
                span[-1]=span[-1]+" "+token
                #span.append(token)

    if span:
        if len(span) < 2:
            span = re.sub('[^\w\d\-\']+', ' ', ''.join(span)).strip()
            span = span.replace('SPEAKER', ' SPEAKER').replace('speaker', ' speaker').strip()
        out.append(span)
    # Remove empty strings and duplicates
    return set([span for span in out if span.strip()])


def extract_triples(annotation, neg_oversampling=7, contr_oversampling=0.7, ellipsis_oversampling=3):
    """ Extracts plain-text triples from an annotation file and samples 'negative' examples by
        crossover. By default, the function will over-extract triples with negative polarity and
        elliptical constructions to counter class imbalance.

        params:
        dict annotation:            loaded annotation file (see load_annotations)
        int neg_oversampling:       how much to over-sample triples with negative polarity
        float contr_oversampling:   how much to sample contrast/invalid triples relative to true triples
        int ellipsis_oversampling:  how much to over-sample elliptical triples
    """
    turns = annotation['tokens']
    triple_ids = [t[:4] for t in annotation['annotations']]

    arguments = defaultdict(list)
    triples = []
    labels = []

    # Oversampling of elliptical triples
    for triple in deepcopy(triple_ids):
        subj_obj_turns = set([i for i, _ in triple[0] + triple[2]])
        if len(subj_obj_turns) > 1:
            triple_ids += [triple] * int(ellipsis_oversampling)

    # Extract 'True' triples
    for subj, pred, obj, polar in triple_ids:

        subj = ' '.join(turns[i][j] for i, j in subj) if subj else ''
        pred = ' '.join(turns[i][j] for i, j in pred) if pred else ''
        obj = ' '.join(turns[i][j] for i, j in obj) if obj else ''

        if subj or pred or obj:

            if not polar:
                triples += [(subj, pred, obj)]
                labels += [1]
            else:
                triples += [(subj, pred, obj)] * neg_oversampling  # Oversampling negative polarities
                labels += [2] * neg_oversampling

            arguments['subjs'].append(subj)
            arguments['preds'].append(pred)
            arguments['objs'].append(obj)

    # Skip if the annotation file was blank
    if not triples:
        return [], [], []

    # Sample fake contrast examples (invalid extractions)
    n = int(len(triples) * contr_oversampling)
    for i in range(50):
        s = random.choice(arguments['subjs'])
        p = random.choice(arguments['preds'])
        o = random.choice(arguments['objs'])

        # Ensure samples are new (and not actually valid!)
        if (s, p, o) not in triples and s and p and o:
            triples += [(s, p, o)]
            labels += [0]
            n -= 1

        # Create as many fake examples as there were 'real' triples
        if n == 0:
            break

    return turns, triples, labels


def pronoun_to_speaker_id(token, turn_idx):
    # Even turns -> speaker1
    if turn_idx % 2 == 0:
        if token in ['i', 'me', 'myself', 'we', 'us', 'ourselves']:
            return 'SPEAKER1'
        elif token in ['my', 'mine', 'our', 'ours']:
            return "SPEAKER1's"
        elif token in ['you', 'yourself', 'yourselves']:
            return 'SPEAKER2'
        elif token in ['your', 'yours']:
            return "SPEAKER2's"
        ##### DUTCH
        elif token in ['ik', 'me', 'mezelf', 'mijzelf', 'mij', 'we', 'wij', 'ons', 'onszelf']:
            return 'SPEAKER1'
        elif token in ['mijn', 'mijne', 'onze']:
            return "SPEAKER1's"
        elif token in ['jij', 'je', 'jou', 'jezelf', 'jijzelf']:
            return 'SPEAKER2'
        elif token in ['jouw']:
            return "SPEAKER2's"
    else:
        if token in ['i', 'me', 'myself', 'we', 'us', 'ourselves']:
            return "SPEAKER2"
        elif token in ['my', 'mine', 'our', 'ours']:
            return "SPEAKER2's"
        elif token in ['you', 'yourself', 'yourselves']:
            return 'SPEAKER1'
        elif token in ['your', 'yours']:
            return "SPEAKER1's"
        ##### DUTCH
        elif token in ['ik', 'me', 'mezelf', 'mijzelf', 'mij', 'we', 'wij', 'ons', 'onszelf']:
            return 'SPEAKER2'
        elif token in ['mijn', 'mijne', 'onze']:
            return "SPEAKER2's"
        elif token in ['jij', 'je', 'jou', 'jezelf', 'jijzelf']:
            return 'SPEAKER1'
        elif token in ['jouw']:
            return "SPEAKER1's"
    return token


def speaker_id_to_speaker(string, speaker1, speaker2):
    return string.replace('SPEAKER1', ' ' + speaker1).replace('SPEAKER2', ' ' + speaker2).strip()