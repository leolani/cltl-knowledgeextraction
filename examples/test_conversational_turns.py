"""
THIS SCRIPT TESTS THE TRIPLE (AND PERSPECTIVE) EXTRACTION. IT LOOPS THROUGH FOUR TXT FILES (STATEMENTS, PERSPECTIVES,
WH-QUESTIONS AND VERB-QUESTIONS) WHICH CONTAIN SINGLE UTTERANCES AND THEIR IDEAL EXTRACTED TRIPLE.
THIS SCRIPT PROCESSES EACH UTTERANCE AND COMPARES THE TRIPLE EXTRACTED WITH THE IDEAL EXTRACTION, ELEMENTWISE.
THEREFORE EACH UTTERANCE MAY HAVE THREE COMPARISONS (SPO) OR MORE (IF COUNTING THE PERSPECTIVE).
TRIPLE ELEMENTS ARE ONLY COMPARED AT A LABEL LEVEL, NO TYPE INFORMATION IS TAKEN INTO ACCOUNT.
"""

import json
from collections import defaultdict

from test_triples import compare_elementwise_triple, compare_elementwise_perspective
from test_triples import load_golden_triples

#from cltl.commons.discrete import UtteranceType
#from cltl.triple_extraction.analyzer import Analyzer
from cltl.triple_extraction.api import Chat
from cltl.triple_extraction.conversational_analyzer import ConversationalAnalyzer
from cltl.triple_extraction.utils.triple_normalization import TripleNormalizer


def test_triples(speaker1, speaker2, item, correct, incorrect, issues, errorf, analyzer:ConversationalAnalyzer):
    chat = Chat(speaker1, speaker2)

#for sure . what else do you like ?<eos>school keeps me pretty busy , what about you ?<eos>spending a lot of time running and getting resources for my new job

    chat.add_utterance(item['utterance'])
    analyzer.analyze_in_context(chat)

    # No triple was extracted, so we missed three items (s, p, o)
    if not chat.last_utterance.triples:
        print((chat.last_utterance, 'ERROR'))
        incorrect += 3
        issues[chat.last_utterance.transcript]['parsing'] = 'NOT PARSED'
        error_string = chat.last_utterance.transcript + ": " + item['triple']['subject'] + " " + item['triple'][
            'predicate'] + " " + item['triple']['object'] + "\n"
        errorf.write(error_string)
        issues[chat.last_utterance.transcript]['triple'] = error_string
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
            error_string = chat.last_utterance.transcript + ": " + item['triple']['subject'] + " " + item['triple'][
                'predicate'] + " " + item['triple']['object'] + "\n"
            errorf.write(error_string)
        # Report
        print(f"\nUtterance: \t{chat.last_utterance}")
        print(f"Triple:            \t{chat.last_utterance.triples[idx_best_triple]}")
        print(f"Expected triple:   \t{item['triple']}")

        # Compare perspectives if available
        if 'perspective' in item.keys():
            score_best_pesp = compare_elementwise_perspective(
                chat.last_utterance.triples[idx_best_triple]['perspective'],
                item['perspective'])

            correct += score_best_pesp
            incorrect += (3 - score_best_pesp)
            if score_best_pesp < 3:
                issues[chat.last_utterance.transcript]['perspective'] = (3 - score_best_pesp)

            print(f"Expected perspective:   \t{item['perspective']}")

        return correct, incorrect, issues


'''
personachat-valid-000544
for sure . what else do you like ?<eos>school keeps me pretty busy , what about you ?<eos>spending a lot of time running and getting resources for my new job
speaker1,spending,a lot of time,positive

personachat-valid-000556
i donate to locks of love if that counts<eos>that is great ! ok , now another random question what is your biggest fear ?<eos>spiders . . . i absolutely hate and fear them
speaker1 's biggest fear,is,spiders,positive
'''
def load_golden_conversation_triples(filepath):
    """
    :param filepath: path to the test file with gold standard
    :return: set with test suite and a set with golden standard
    """
    file = open(filepath, "r")
    test = file.readlines()
    test_suite = []
    personachat_id = ""
    conversation = ""
    triple = ""

    for sample in test:
        try:
            if sample == '\n':
                personachat_id = ""
                conversation = ""
                triple = ""
                continue
            elif sample.startswith("personachat"):
                personachat_id = sample
            elif personachat_id and not conversation:
                conversation = sample
            elif personachat_id and conversation and not triple:
                triple = sample
                item = {'utterance': conversation,
                        'triple': {'subject': triple.split(',')[0].lower(),
                                   'predicate': triple.split(',')[1].lower(),
                                   'object': triple.split(',')[2].lower()}}
                if len(triple.split(',')) > 2:
                    perspective = triple.split(",")[3]
                    polarity = 1.0
                    certainty = 1.0
                    sentiment = 1.0
                    if perspective=="negative":
                        polarity = 0.0
                    elif perspective == "uncertain":
                        certainty = 0.75
                    item['perspective'] = {'certainty': certainty,
                                           'polarity': polarity,
                                           'sentiment': sentiment}
                # cleanup
                for k, v in item['triple'].items():
                    if v == '?':
                        item['triple'][k] = ''

                test_suite.append(item)

        except:
            print(sample)

    return test_suite

def test_triples_in_file(path, analyzer, speaker1, speaker2):
    """
    This function loads the test suite and gold standard and prints the mismatches between the system analysis of the
    test suite, including perspective if it is added, as well as the number of correctly and incorrectly extracted
    triple elements
    :param path: filepath of test file
    """
    correct = 0
    incorrect = 0
    issues = defaultdict(dict)
    test_suite = load_golden_conversation_triples(path)
    errorf = open(path + ".error.txt", "w")
    print(f'\nRUNNING {len(test_suite)} UTTERANCES FROM FILE {path}\n')

    for item in test_suite:
        print(f'\n---------------------------------------------------------------\n')
        correct, incorrect, issues = test_triples(speaker1, speaker2, item, correct, incorrect, issues, errorf, analyzer)
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
    model = "/Users/piek/Desktop/d-Leolani/resources/models/2022-04-27"
    analyzer = ConversationalAnalyzer(model)
    all_test_files = [
        "./data/conversation_test_examples/test_answer_ellipsis.txt",
        # "./data/conversation_test_examples/test_coordination.txt",
        # "./data/conversation_test_examples/test_coreference.txt",
        # "./data/conversation_test_examples/test_declarative_statements.txt",
        # "./data/conversation_test_examples/test_declarative_statements+negated.txt",
        # "./data/conversation_test_examples/test_no_answers.txt",
        # "./data/conversation_test_examples/test_yes_answers.txt",
        # "./data/conversation_test_examples/test_full.txt",
        # "./data/conversation_test_examples/test_implicit_negation.txt",
        # "./data/conversation_test_examples/test_single_utterances.txt"
    ]

    '''
    '''
    print(f'\nRUNNING {len(all_test_files)} FILES\n\n')
    speaker1 = "HUMAN"
    speaker2 = "LEOLANI"
    analyzer._extractor._speaker1 = speaker1
    analyzer._extractor._speaker2 = speaker2

    for test_file in all_test_files:
        test_triples_in_file(test_file, analyzer, speaker1, speaker2)

