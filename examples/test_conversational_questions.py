"""
THIS SCRIPT TESTS THE TRIPLE (AND PERSPECTIVE) EXTRACTION. IT LOOPS THROUGH FOUR TXT FILES (STATEMENTS, PERSPECTIVES,
WH-QUESTIONS AND VERB-QUESTIONS) WHICH CONTAIN SINGLE UTTERANCES AND THEIR IDEAL EXTRACTED TRIPLE.
THIS SCRIPT PROCESSES EACH UTTERANCE AND COMPARES THE TRIPLE EXTRACTED WITH THE IDEAL EXTRACTION, ELEMENTWISE.
THEREFORE EACH UTTERANCE MAY HAVE THREE COMPARISONS (SPO) OR MORE (IF COUNTING THE PERSPECTIVE).
TRIPLE ELEMENTS ARE ONLY COMPARED AT A LABEL LEVEL, NO TYPE INFORMATION IS TAKEN INTO ACCOUNT.
"""

from datetime import datetime
import json
from collections import defaultdict

from test_triples import compare_elementwise_triple, compare_elementwise_perspective
from test_triples import load_golden_triples

#from cltl.commons.discrete import UtteranceType
#from cltl.triple_extraction.analyzer import Analyzer
from cltl.triple_extraction.api import Chat, DialogueAct
from cltl.question_extraction.conversational_question_analyzer import ConversationalQuestionAnalyzer


def test_triples(item, correct, nr_tripled_utt, incorrect, issues, errorf, analyzer:ConversationalQuestionAnalyzer):
    chat = Chat(agent="leolani", speaker="lenka")

    chat.add_utterance(item['utterance'], 'lenka', DialogueAct.QUESTION)
    analyzer.analyze_question_in_context(chat)

    # No triple was extracted, so we missed three items (s, p, o)
    if not chat.last_utterance.triples:
        print((chat.last_utterance, 'ERROR'))
        incorrect += 3
        issues[chat.last_utterance.transcript]['parsing'] = 'NO TRIPLES EXTRACTED'
        error_string = item['triple']['subject'] + " " + item['triple'][
            'predicate'] + " " + item['triple']['object']
        errorf.write(error_string)
        issues[chat.last_utterance.transcript]['triple'] = error_string
        return correct, incorrect, nr_tripled_utt, issues

    # A triple was extracted so we compare it elementwise
    else:
        nr_tripled_utt +=1
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
            error_string =  item['triple']['subject'] + " " + item['triple'][
                'predicate'] + " " + item['triple']['object']
            for extracted_triple in chat.last_utterance.triples:
                error_string += ", extracted_triple"+ ": " + str(extracted_triple['subject']["label"]) + " " \
                                + str(extracted_triple['predicate']["label"]) + " " \
                                + str(extracted_triple['object']["label"])
            errorf.write(error_string)
            issues[chat.last_utterance.transcript]['triple'] = error_string
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

    return correct, incorrect, nr_tripled_utt, issues

def test_triples_in_file(path, analyzer, resultfile):
    """
    This function loads the test suite and gold standard and prints the mismatches between the system analysis of the
    test suite, including perspective if it is added, as well as the number of correctly and incorrectly extracted
    triple elements
    :param path: filepath of test file
    """
    correct = 0
    incorrect = 0
    nr_tripled_utt = 0
    issues = defaultdict(dict)
    test_suite = load_golden_triples(path)
    errorf = open(path + ".error.txt", "w")
    resultfile.write(f'\nRUNNING {len(test_suite)} UTTERANCES FROM FILE {path}\n')

    print(f'\nRUNNING {len(test_suite)} UTTERANCES FROM FILE {path}\n')

    for item in test_suite:
        print(f'\n---------------------------------------------------------------\n')
        correct, incorrect, nr_tripled_utt, issues = test_triples(item, correct, nr_tripled_utt, incorrect, issues, errorf, analyzer)
    errorf.close()

    print(f'\n\n\n---------------------------------------------------------------\nSUMMARY\n')
    print(f'\nRAN {len(test_suite)} UTTERANCES FROM FILE {path}\n')
    print(f'\nCORRECT TRIPLE ELEMENTS: {correct}\t\t\tINCORRECT TRIPLE ELEMENTS: {incorrect}')
    print(f'\nUTTERANCES WITH TRIPLES: {nr_tripled_utt}\t\t\tUTTERANCE WITHOUT TRIPLES: {len(test_suite)-nr_tripled_utt}')
    print(f"ISSUES ({len(issues)} UTTERANCES): {json.dumps(issues, indent=4, sort_keys=True, separators=(', ', ': '))}")
    resultfile.write(f'\nMODEL: {analyzer._extractor._base_model}\n')
    resultfile.write(f'\nCORRECT TRIPLE ELEMENTS: {correct}\t\t\tINCORRECT TRIPLE ELEMENTS: {incorrect}\n')
    resultfile.write(f'\nUTTERANCES WITH TRIPLES: {nr_tripled_utt}\t\t\tUTTERANCE WITHOUT TRIPLES: {len(test_suite)-nr_tripled_utt}\n')
    resultfile.write(
        f"ISSUES ({len(issues)} UTTERANCES): {json.dumps(issues, indent=4, sort_keys=True, separators=(', ', ': '))}\n")


if __name__ == "__main__":
    '''
    test files with triples are formatted like so "test sentence : subject predicate object" 
    multi-word-expressions have dashes separating their elements, and are marked with apostrophes if they are a 
    collocation
    '''


    # Test with monolingual model
    # path = '/Users/piek/Desktop/d-Leolani/leolani-models/conversational_triples/22_04_27'
    # base_model='albert-base-v2'
    # lang='en'

    # Test with multilingual model
    path='/Users/piek/Desktop/d-Leolani/leolani-models/conversational_triples/2024-03-11'
    base_model='google-bert/bert-base-multilingual-cased'
    lang="en"
    current_date = datetime.today()
    resultfilename= "data/evaluation_CONVQ_"+base_model.replace("/","_")+str(current_date.date())+".csv"

    resultfile = open(resultfilename, "w")

    analyzer = ConversationalQuestionAnalyzer(model_path=path, base_model=base_model, lang=lang)
    #analyzer.__init__(model)
    all_test_files = [
        "./data/wh-questions.txt",
       #  "./data/verb-questions.txt",
    ]

    print(f'\nRUNNING {len(all_test_files)} FILES\n\n')

    for test_file in all_test_files:
        test_triples_in_file(test_file, analyzer, resultfile)

    resultfile.close()

    '''
Results using ALBERT
RAN 63 UTTERANCES FROM FILE ./data/verb-questions.txt

CORRECT TRIPLE ELEMENTS: 113			INCORRECT TRIPLE ELEMENTS: 76

UTTERANCES WITH TRIPLES: 45			UTTERANCE WITHOUT TRIPLES: 18

ISSUES (28 UTTERANCES):

Results using Multilingual BERT

RAN 63 UTTERANCES FROM FILE ./data/verb-questions.txt


CORRECT TRIPLE ELEMENTS: 130			INCORRECT TRIPLE ELEMENTS: 59

UTTERANCES WITH TRIPLES: 55			UTTERANCE WITHOUT TRIPLES: 8


RAN 66 UTTERANCES FROM FILE ./data/wh-questions.txt


CORRECT TRIPLE ELEMENTS: 86			INCORRECT TRIPLE ELEMENTS: 112

UTTERANCES WITH TRIPLES: 43			UTTERANCE WITHOUT TRIPLES: 23

ISSUES (36 UTTERANCES): {

Multilingual Model

RAN 66 UTTERANCES FROM FILE ./data/wh-questions.txt


CORRECT TRIPLE ELEMENTS: 39			INCORRECT TRIPLE ELEMENTS: 159

UTTERANCES WITH TRIPLES: 21			UTTERANCE WITHOUT TRIPLES: 45
ISSUES (41 UTTERANCES): {

    '''

