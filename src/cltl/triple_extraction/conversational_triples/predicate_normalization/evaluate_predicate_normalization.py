from predicate_normalization import PredicateNormalizer
from sklearn.metrics import classification_report


def speaker_to_pronoun(arg, slot='subj'):
    """ Maps back from speaker ids to pronouns. Helps BERT with creating
        better embeddings as speaker* is not in the vocabulary.
    """
    sing_pron = 'I' if slot == 'subj' else 'you'
    poss_pron = 'my' if slot == 'subj' else 'your'
    arg = arg.replace("speaker1 's", poss_pron)
    arg = arg.replace("speaker2 's", poss_pron)
    arg = arg.replace("speaker1", sing_pron)
    arg = arg.replace("speaker2", sing_pron)
    return arg.strip()


def load_test_data(fname):
    """ Extracts triples and corresponding normalized predicate
        labels from test set.
    """
    triples = []
    labels = []
    with open(fname, 'r', encoding='utf-8') as file:
        for i, line in enumerate(file):
            if line.strip() and not line.startswith('#'):
                try:
                    subj, pred, obj, _, norm_pred = line.strip().split(',')
                    triples.append((speaker_to_pronoun(subj, slot='subj'),
                                    speaker_to_pronoun(pred, slot='pred'),
                                    speaker_to_pronoun(obj, slot='obj')))
                    labels.append(norm_pred)
                except:
                    print('Error at %s: %s' % (i, line))

    print("Found %s test samples" % len(triples))
    return triples, labels


def evaluate(normalizer, test_triples, test_labels):
    """ Evaluates predicate normalization and disambiguation.
    """
    pred_labels = []
    for i, triple in enumerate(test_triples):
        norm_pred, conf = normalizer.normalize(*triple)
        pred_labels.append(norm_pred)
        print('%s (%s)' % (triple, conf))
        print('True:', test_labels[i])
        print('Pred:', norm_pred)
        print()

    print(classification_report(test_labels, pred_labels, zero_division=0))


if __name__ == '__main__':
    test_triples, test_labels = load_test_data('test_exemplars.txt')
    normalizer = PredicateNormalizer('training_exemplars.txt')
    evaluate(normalizer, test_triples, test_labels)
