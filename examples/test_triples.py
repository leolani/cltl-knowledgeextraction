"""
THIS SCRIPT TESTS THE TRIPLE (AND PERSPECTIVE) EXTRACTION. IT LOOPS THROUGH FOUR TXT FILES (STATEMENTS, PERSPECTIVES,
WH-QUESTIONS AND VERB-QUESTIONS) WHICH CONTAIN SINGLE UTTERANCES AND THEIR IDEAL EXTRACTED TRIPLE.
THIS SCRIPT PROCESSES EACH UTTERANCE AND COMPARES THE TRIPLE EXTRACTED WITH THE IDEAL EXTRACTION, ELEMENTWISE.
THEREFORE EACH UTTERANCE MAY HAVE THREE COMPARISONS (SPO) OR MORE (IF COUNTING THE PERSPECTIVE).
TRIPLE ELEMENTS ARE ONLY COMPARED AT A LABEL LEVEL, NO TYPE INFORMATION IS TAKEN INTO ACCOUNT.
"""

import json
from collections import defaultdict

from cltl.triple_extraction.api import Chat, UtteranceHypothesis


def load_golden_triples(filepath):
    """
    :param filepath: path to the test file with gold standard
    :return: set with test suite and a set with golden standard
    """
    file = open(filepath, "r")
    test = file.readlines()
    test_suite = []

    for sample in test:
        if sample == '\n':
            break

        try:
            # set utterance, triple and perspective
            item = {'utterance': sample.split(':')[0], 'triple': {'subject': sample.split(':')[1].split()[0].lower(),
                                                                  'predicate': sample.split(':')[1].split()[1].lower(),
                                                                  'object': sample.split(':')[1].split()[2].lower()}}

            # set perspective if available
            if len(sample.split(':')) > 2:
                item['perspective'] = {'certainty': float(sample.split(':')[2].split()[0]),
                                       'polarity': float(sample.split(':')[2].split()[1]),
                                       'sentiment': float(sample.split(':')[2].split()[2])}

            # cleanup
            for k, v in item['triple'].items():
                if v == '?':
                    item['triple'][k] = ''

            test_suite.append(item)

        except:
            print(sample)

    return test_suite


def compare_triples(triple, gold):
    """
    :param triple: triple extracted by the system
    :param gold: golden triple to compare with
    :return: number of correct elements in a triple
    """
    correct = 0

    for key in triple:
        if key not in gold.keys():
            continue

        if triple[key]['label'].lower() != gold[key]:
            print(f"Mismatch in triple {key}: {triple[key]['label'].lower()} != {gold[key]}")
        else:
            correct += 1

    return correct


def compare_perspectives(perspective, gold):
    """
    :param perspective: perspective extracted by the system
    :param gold: golden perspective to compare with
    :return: number of correct elements in a perspective
    """
    correct = 0

    for key in perspective:
        if key not in gold.keys():
            continue

        if float(perspective[key]) != gold[key]:
            print(f"Mismatch in perspective {key}: {perspective[key]} != {gold[key]}")
        else:
            correct += 1

    return correct


def test_triples(item, correct, incorrect, issues):
    chat = Chat("Lenka")
    chat.add_utterance([UtteranceHypothesis(item['utterance'], 1.0)])
    chat.last_utterance.analyze()

    # No triple was extracted, so we missed three items (s, p, o)
    if chat.last_utterance.triple is None:
        print((chat.last_utterance, 'ERROR'))
        incorrect += 3
        issues[chat.last_utterance.transcript]['parsing'] = 'NOT PARSED'
        return correct, incorrect, issues

    # A triple was extracted so we compare it elementwise
    t = compare_triples(chat.last_utterance.triple, item['triple'])
    correct += t
    incorrect += (3 - t)
    if t < 3:
        issues[chat.last_utterance.transcript]['triple'] = (3 - t)

    # Report
    print(f"\nUtterance: \t{chat.last_utterance}")
    print(f"Triple:            \t{chat.last_utterance.triple}")
    print(f"Expected triple:   \t{item['triple']}")

    # Compare perspectives if available
    if 'perspective' in item.keys():
        t = compare_perspectives(chat.last_utterance.perspective, item['perspective'])
        correct += t
        incorrect += (3 - t)
        if t < 3:
            issues[chat.last_utterance.transcript]['perspective'] = (3 - t)

        print(f"Perspective:            \t{chat.last_utterance.perspective}")
        print(f"Expected perspective:   \t{item['perspective']}")

    return correct, incorrect, issues


def test_triples_in_file(path):
    """
    This function loads the test suite and gold standard and prints the mismatches between the system analysis of the
    test suite, including perspective if it is added, as well as the number of correctly and incorrectly extracted
    triple elements
    :param path: filepath of test file
    """
    correct = 0
    incorrect = 0
    issues = defaultdict(dict)
    test_suite = load_golden_triples(path)

    print(f'\nRUNNING {len(test_suite)} UTTERANCES FROM FILE {path}\n')

    for item in test_suite:
        print(f'\n---------------------------------------------------------------\n')
        correct, incorrect, issues = test_triples(item, correct, incorrect, issues)

    print(f'\n\n\n---------------------------------------------------------------\nSUMMARY\n')
    print(f'\nCORRECT TRIPLE ELEMENTS: {correct}\t\t\tINCORRECT TRIPLE ELEMENTS: {incorrect}')
    print(f"ISSUES ({len(issues)} UTTERANCES): {json.dumps(issues, indent=4, sort_keys=True, separators=(', ', ': '))}")


if __name__ == "__main__":
    '''
    test files with triples are formatted like so "test sentence : subject predicate object" 
    multi-word-expressions have dashes separating their elements, and are marked with apostrophes if they are a 
    collocation
    '''

    all_test_files = ["./data/wh-questions.txt", "./data/verb-questions.txt",
                      "./data/statements.txt", "./data/perspective.txt"]

    print(f'\nRUNNING {len(all_test_files)} FILES\n\n')

    for test_file in all_test_files:
        test_triples_in_file(test_file)
