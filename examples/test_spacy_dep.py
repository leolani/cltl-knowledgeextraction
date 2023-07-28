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
from cltl.triple_extraction.spacy_analyzer import spacyAnalyzer
from test_triples import compare_elementwise_triple, compare_elementwise_perspective
from test_triples import load_golden_triples
from test_utils import test_triples, recall


# def test_triples(item, correct, incorrect, issues, errorf):
#     chat = Chat("Leolani", "Lenka")
#     analyzer = spacyAnalyzer()
#
#     chat.add_utterance(item['utterance'])
#     analyzer.analyze(chat.last_utterance, "lenka", "leolani")
#
#     # No triple was extracted, so we missed three items (s, p, o)
#     if not chat.last_utterance.triples:
#         print((chat.last_utterance, 'ERROR'))
#         incorrect += 3
#         issues[chat.last_utterance.transcript]['parsing'] = 'NOT PARSED'
#         error_string = chat.last_utterance.transcript + ": " + item['triple']['subject'] + " " + item['triple'][
#             'predicate'] + " " + item['triple']['object'] + "\n"
#         errorf.write(error_string)
#         return correct, incorrect, issues
#
#     # A triple was extracted so we compare it elementwise
#     else:
#         # Compare all extracted triples, select the one with the most correct elements
#         triples_scores = [compare_elementwise_triple(extracted_triple, item['triple'])
#                           for extracted_triple in chat.last_utterance.triples]
#
#         score_best_triple = max(triples_scores)
#         idx_best_triple = triples_scores.index(score_best_triple)
#
#         # add to statistics
#         correct += score_best_triple
#         incorrect += (3 - score_best_triple)
#         if score_best_triple < 3:
#             issues[chat.last_utterance.transcript]['triple'] = (3 - score_best_triple)
#             error_string = chat.last_utterance.transcript + ": " + item['triple']['subject'] + " " + item['triple'][
#                 'predicate'] + " " + item['triple']['object'] + "\n"
#             errorf.write(error_string)
#         # Report
#         print(f"\nUtterance: \t{chat.last_utterance}")
#         print(f"Triple:            \t{chat.last_utterance.triples[idx_best_triple]}")
#         print(f"Expected triple:   \t{item['triple']}")
#
#         # Compare perspectives if available
#         if 'perspective' in item.keys():
#             score_best_pesp = compare_elementwise_perspective(
#                 chat.last_utterance.triples[idx_best_triple]['perspective'],
#                 item['perspective'])
#
#             correct += score_best_pesp
#             incorrect += (3 - score_best_pesp)
#             if score_best_pesp < 3:
#                 issues[chat.last_utterance.transcript]['perspective'] = (3 - score_best_pesp)
#
#             print(f"Expected perspective:   \t{item['perspective']}")
#
#         return correct, incorrect, issues


def test_triples_in_file(path):
    """
    This function loads the test suite and gold standard and prints the mismatches between the system analysis of the
    test suite, including perspective if it is added, as well as the number of correctly and incorrectly extracted
    triple elements
    :param path: filepath of test file
    """
    results = {'correct': 0, 'incorrect': 0, 'correct_subjects': 0, 'incorrect_subjects': 0, 'correct_predicates': 0,
               'incorrect_predicates': 0, 'correct_objects': 0, 'incorrect_objects': 0, 'correct_perspective': 0,
               'incorrect_perspective': 0}

    issues = defaultdict(dict)
    test_suite = load_golden_triples(path)
    errorf = open(path + ".error.txt", "w")
    print(f'\nRUNNING {len(test_suite)} UTTERANCES FROM FILE {path}\n')
    analyzer = spacyAnalyzer()

    for item in test_suite:
        print(f'\n---------------------------------------------------------------\n')
        results, issues = test_triples(item, results, issues, errorf, analyzer)
    errorf.close()

    correct = results['correct']
    incorrect = results['incorrect']
    correct_subjects = results['correct_subjects']
    incorrect_subjects = results['incorrect_subjects']
    correct_predicates = results['correct_predicates']
    incorrect_predicates = results['incorrect_predicates']
    correct_objects = results['correct_objects']
    incorrect_objects = results['incorrect_objects']
    correct_perspective = results['correct_perspective']
    incorrect_perspective = results['incorrect_perspective']
    triple_recall = recall(len(test_suite), correct)
    subject_recall = recall(len(test_suite), correct_subjects)
    predicate_recall = recall(len(test_suite), correct_predicates)
    objects_recall = recall(len(test_suite), correct_objects)
    perspective_recall = recall(len(test_suite)*3, incorrect_perspective)


    print(f'\n\n\n---------------------------------------------------------------\nSUMMARY\n')
    print(f'\nRAN {len(test_suite)} UTTERANCES FROM FILE {path}\n')
    print(f'\nCORRECT TRIPLES: {correct}\t\t\tINCORRECT TRIPLES: {incorrect}\t\t\tRECALL: {triple_recall:.2f}%')
    print(f'\nCORRECT SUBJECTS: {correct_subjects}\t\t\tINCORRECT SUBJECTS: {incorrect_subjects}\t\t\tRECALL: '
          f'{subject_recall:.2f}%')
    print(f'\nCORRECT PREDICATES: {correct_predicates}\t\t\tINCORRECT PREDICATES: {incorrect_predicates}\t\t\tRECALL: '
          f'{predicate_recall:.2f}%')
    print(f'\nCORRECT OBJECTS: {correct_objects}\t\t\tINCORRECT OBJECTS: {incorrect_objects}\t\t\tRECALL: '
          f'{objects_recall:.2f}%')
    print(f'\nCORRECT PERSPECTIVES: {correct_perspective}\t\t\tINCORRECT PERSPECTIVES: {incorrect_perspective}\t\t\t'
          f'RECALL: {perspective_recall:.2f}%')
    print(f"ISSUES ({len(issues)} UTTERANCES): {json.dumps(issues, indent=4, sort_keys=True, separators=(', ', ': '))}")


if __name__ == "__main__":
    '''
    test files with triples are formatted like so "test sentence : subject predicate object" 
    multi-word-expressions have dashes separating their elements, and are marked with apostrophes if they are a 
    collocation
    '''

    all_test_files = [
        "./data/wh-questions.txt",
        "./data/verb-questions.txt",
        "./data/statements.txt",
        "./data/perspective.txt"
    ]

    all_test_files = ["./data/statements.txt"]
    # SPACY CORRECT TRIPLE ELEMENTS: 87			INCORRECT TRIPLE ELEMENTS: 177

    print(f'\nRUNNING {len(all_test_files)} FILES\n\n')

    for test_file in all_test_files:
        test_triples_in_file(test_file)
