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
from test_triples import load_golden_triples
from test_triples import compare_elementwise, compare_elementwise_triple, compare_elementwise_perspective

def test_triples(item, correct, incorrect, issues, errorf):
    chat = Chat("Lenka")
    analyzer = spacyAnalyzer()

    chat.add_utterance(item['utterance'])
    analyzer.analyze(chat.last_utterance, "lenka", "leolani")

    # No triple was extracted, so we missed three items (s, p, o)
    if not chat.last_utterance.triples:
        print((chat.last_utterance, 'ERROR'))
        incorrect += 3
        issues[chat.last_utterance.transcript]['parsing'] = 'NOT PARSED'
        error_string = chat.last_utterance.transcript + ": " + item['triple']['subject'] + " " + item['triple'][
            'predicate'] + " " + item['triple']['object'] + "\n"
        errorf.write(error_string)
        return correct, incorrect, issues

    # A triple was extracted so we compare it elementwise
    else:
        # Compare all extracted triples, select the one with the most correct elements
        triples_scores = [compare_elementwise_triple(extracted_triple, item['triple'])
                          for extracted_triple in chat.last_utterance.triples]

        score_best_triple = max(triples_scores)
        idx_best_triple = triples_scores.index(score_best_triple)

        # add to statistics
        correct += score_best_triple
        incorrect += (3 - score_best_triple)
        if score_best_triple < 3:
            issues[chat.last_utterance.transcript]['triple'] = (3 - score_best_triple)
            error_string = chat.last_utterance.transcript+": "+item['triple']['subject']+" "+item['triple']['predicate']+" "+item['triple']['object']+"\n"
            errorf.write(error_string)
        # Report
        print(f"\nUtterance: \t{chat.last_utterance}")
        print(f"Triple:            \t{chat.last_utterance.triples[idx_best_triple]}")
        print(f"Expected triple:   \t{item['triple']}")

        # Compare perspectives if available
        if 'perspective' in item.keys():
            score_best_pesp = compare_elementwise_perspective(chat.last_utterance.triples[idx_best_triple]['perspective'],
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
    errorf = open(path+".error.txt", "w")
    print(f'\nRUNNING {len(test_suite)} UTTERANCES FROM FILE {path}\n')

    for item in test_suite:
        print(f'\n---------------------------------------------------------------\n')
        correct, incorrect, issues = test_triples(item, correct, incorrect, issues, errorf)
    errorf.close()

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
        "./data/wh-questions.txt",
        "./data/verb-questions.txt",
        "./data/statements.txt",
        "./data/perspective.txt"
    ]

    all_test_files = ["./data/statements.txt"]
    #SPACY CORRECT TRIPLE ELEMENTS: 87			INCORRECT TRIPLE ELEMENTS: 177

    print(f'\nRUNNING {len(all_test_files)} FILES\n\n')

    for test_file in all_test_files:
        test_triples_in_file(test_file)
