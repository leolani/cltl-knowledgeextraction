import json
from collections import defaultdict

from cltl.triple_extraction.api import Chat
from cltl.triple_extraction.cfg_analyzer import CFGAnalyzer
from cltl.triple_extraction.oie_analyzer import OIEAnalyzer
from cltl.triple_extraction.utils.helper_functions import utterance_to_capsules
from test_triples import compare_elementwise
from test_triples import load_golden_triples


def evaluate_triples(chat, item, correct, incorrect, issues):
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


def test_triples_in_file_report(path):
    """
    This function loads the test suite and gold standard and prints the mismatches between the system analysis of the
    test suite, including perspective if it is added, as well as the number of correctly and incorrectly extracted
    triple elements
    :param path: filepath of test file
    """
    correct_1 = 0
    incorrect_1 = 0
    issues_1 = defaultdict(dict)

    correct_2 = 0
    incorrect_2 = 0
    issues_2 = defaultdict(dict)

    test_suite = load_golden_triples(path)
    print(f'\nRUNNING {len(test_suite)} UTTERANCES FROM FILE {path}\n')

    chat = Chat("Leolani", "Lenka")

    a1 = "OIE"
    a2 = "CFG"
    analyzer_1 = OIEAnalyzer()
    analyzer_2 = CFGAnalyzer()

    for item in test_suite:
        print(f'\n---------------------------------------------------------------\n')

        chat.add_utterance(item['utterance'])

        analyzer_1.analyze(chat.last_utterance)
        correct_1, incorrect_1, issues_1 = evaluate_triples(chat, item, correct_1, incorrect_1, issues_1)

        analyzer_2.analyze(chat.last_utterance)
        correct_2, incorrect_2, issues_2 = evaluate_triples(chat, item, correct_2, incorrect_2, issues_2)

    print(f'\n\n\n---------------------------------------------------------------\nSUMMARY\n')
    print(f'\nRAN {len(test_suite)} UTTERANCES FROM FILE {path}\n')
    print(f'\n{a1} CORRECT TRIPLE ELEMENTS: {correct_1}\t\t\tINCORRECT TRIPLE ELEMENTS: {incorrect_1}')
    print(f'\n{a2} CORRECT TRIPLE ELEMENTS: {correct_2}\t\t\tINCORRECT TRIPLE ELEMENTS: {incorrect_2}')

    print(
        f"ISSUES {a1} ({len(issues_1)} UTTERANCES): {json.dumps(issues_1, indent=4, sort_keys=True, separators=(', ', ': '))}")
    print(
        f"ISSUES {a2} ({len(issues_2)} UTTERANCES): {json.dumps(issues_2, indent=4, sort_keys=True, separators=(', ', ': '))}")


def test_triples_in_file(path):
    """
    This function loads the test suite and gold standard and prints the mismatches between the system analysis of the
    test suite, including perspective if it is added, as well as the number of correctly and incorrectly extracted
    triple elements
    :param path: filepath of test file
    """

    test_suite = load_golden_triples(path)
    print(f'\nRUNNING {len(test_suite)} UTTERANCES FROM FILE {path}\n')

    chat = Chat("Leolani", "Lenka")

    analyzer_1 = OIEAnalyzer()
    analyzer_2 = CFGAnalyzer()

    for item in test_suite:
        print(f'\n---------------------------------------------------------------\n')

        chat.add_utterance(item['utterance'])

        analyzer_1.analyze(chat.last_utterance)
        capsules = utterance_to_capsules(chat.last_utterance)
        print(f"\nTriples:            \t{capsules}\n")

        analyzer_2.analyze(chat.last_utterance)
        capsules = utterance_to_capsules(chat.last_utterance)
        print(f"\nTriples:            \t{capsules}\n")


if __name__ == "__main__":
    '''
    test files with triples are formatted like so "test sentence : subject predicate object" 
    multi-word-expressions have dashes separating their elements, and are marked with apostrophes if they are a 
    collocation
    '''

    test_file = "./data/statements.txt"
    # OIE CORRECT  TRIPLE  ELEMENTS: 58  INCORRECT TRIPLE ELEMENTS: 206
    # CFG CORRECT TRIPLE ELEMENTS: 237 INCORRECT TRIPLE ELEMENTS: 27
    print(f'\nRUNNING {len(test_file)} STATEMENTS\n\n')

    # test_triples_in_file(test_file)
    test_triples_in_file_report(test_file)
