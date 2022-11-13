"""
THIS SCRIPT TESTS THE TRIPLE (AND PERSPECTIVE) EXTRACTION. IT LOOPS THROUGH FOUR TXT FILES (STATEMENTS, PERSPECTIVES,
WH-QUESTIONS AND VERB-QUESTIONS) WHICH CONTAIN SINGLE UTTERANCES AND THEIR IDEAL EXTRACTED TRIPLE.
THIS SCRIPT PROCESSES EACH UTTERANCE AND COMPARES THE TRIPLE EXTRACTED WITH THE IDEAL EXTRACTION, ELEMENTWISE.
THEREFORE EACH UTTERANCE MAY HAVE THREE COMPARISONS (SPO) OR MORE (IF COUNTING THE PERSPECTIVE).
TRIPLE ELEMENTS ARE ONLY COMPARED AT A LABEL LEVEL, NO TYPE INFORMATION IS TAKEN INTO ACCOUNT.
"""

import json
from collections import defaultdict

from cltl.triple_extraction.api import Chat
from cltl.triple_extraction.cfg_analyzer import CFGAnalyzer


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


def compare_elementwise(triple, gold):
    """
    :param triple: triple extracted by the system
    :param gold: golden triple to compare with
    :return: number of correct elements in a triple
    """
    correct = 0

    for key in triple:
        if key not in gold.keys():
            continue
        if type(triple[key]) == dict and triple[key]['label'].lower() != gold[key]:
            print(f"Mismatch in triple {key}: {triple[key]['label'].lower()} != {gold[key]}")

        elif type(triple[key]) == float and triple[key] != gold[key]:
            print(f"Mismatch in perspective {key}: {triple[key]} != {gold[key]}")

        elif type(triple[key]) == dict and triple[key]['label'].lower() == gold[key]:
            print(f"Match triple {key}: {triple[key]} == {gold[key]}")
            correct += 1

    return correct


def compare_elementwise_perspective(triple, gold):
    """
    :param triple: triple extracted by the system
    :param gold: golden triple to compare with
    :return: number of correct elements in a triple
    """
    correct = 0

    for key in triple:
        if key not in gold.keys():
            continue
        if type(triple[key]) == float and triple[key] != gold[key]:
            print(f"Mismatch in perspective {key}: {triple[key]} != {gold[key]}")

        elif type(triple[key]) == float and triple[key]['label'].lower() == gold[key]:
            print(f"Match triple {key}: {triple[key]} == {gold[key]}")
            correct += 1

    return correct


def compare_elementwise_triple(triple, gold):
    """
    :param triple: triple extracted by the system
    :param gold: golden triple to compare with
    :return: number of correct elements in a triple
    """
    correct = 0
    for key in triple:
        if key not in gold.keys():
            # print("key not in triple", key)
            continue
        if type(triple[key]) == dict and triple[key]['label'].lower() != gold[key]:
            print(f"Mismatch in triple {key}: {triple[key]['label'].lower()} != {gold[key]}")
        elif type(triple[key]) == dict and triple[key]['label'].lower() == gold[key]:
            # print(f"Match triple {key}: {triple[key]} == {gold[key]}")
            correct += 1

    return correct


def test_triples(item, correct, incorrect, issues):
    chat = Chat("Leolani", "Lenka")
    analyzer = CFGAnalyzer()

    chat.add_utterance(item['utterance'])
    analyzer.analyze(chat.last_utterance)

    # No triple was extracted, so we missed three items (s, p, o)
    if not chat.last_utterance.triples:
        print((chat.last_utterance, 'ERROR'))
        incorrect += 3
        issues[chat.last_utterance.transcript]['parsing'] = 'NOT PARSED'
        return correct, incorrect, issues

    # A triple was extracted so we compare it elementwise
    else:
        # Compare all extracted triples, select the one with the most correct elements
        triples_scores = [compare_elementwise(extracted_triple, item['triple'])
                          for extracted_triple in chat.last_utterance.triples]

        score_best_triple = max(triples_scores)
        idx_best_triple = triples_scores.index(score_best_triple)

        # add to statistics
        correct += score_best_triple
        incorrect += (3 - score_best_triple)
        if score_best_triple < 3:
            issues[chat.last_utterance.transcript]['triple'] = (3 - score_best_triple)

        # Report
        print(f"\nUtterance: \t{chat.last_utterance}")
        print(f"Triple:            \t{chat.last_utterance.triples[idx_best_triple]}")
        print(f"Expected triple:   \t{item['triple']}")

        # Compare perspectives if available
        if 'perspective' in item.keys():
            score_best_pesp = compare_elementwise(chat.last_utterance.triples[idx_best_triple]['perspective'],
                                                  item['perspective'])

            correct += score_best_pesp
            incorrect += (3 - score_best_pesp)
            if score_best_pesp < 3:
                issues[chat.last_utterance.transcript]['perspective'] = (3 - score_best_pesp)

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
    print(f'\nRAN {len(test_suite)} UTTERANCES FROM FILE {path}\n')
    print(f'\nCORRECT TRIPLE ELEMENTS: {correct}\t\t\tINCORRECT TRIPLE ELEMENTS: {incorrect}')
    print(f"ISSUES ({len(issues)} UTTERANCES): {json.dumps(issues, indent=4, sort_keys=True, separators=(', ', ': '))}")


if __name__ == "__main__":
    '''
    test files with triples are formatted like so "test sentence : subject predicate object" 
    multi-word-expressions have dashes separating their elements, and are marked with apostrophes if they are a 
    collocation
    '''

    all_test_files = [
        "./data/statements.txt",
        "./data/perspective.txt"
       # "./data/wh-questions.txt",
       # "./data/verb-questions.txt",
       # "./data/kinship-friends.txt",
       # "./data/activities.txt",
       # "./data/feelings.txt",
    ]

    all_test_files=["./data/statements.error.txt"]
    print(f'\nRUNNING {len(all_test_files)} FILES\n\n')

    for test_file in all_test_files:
        print(test_file)
        test_triples_in_file(test_file)
