"""
THIS SCRIPT TESTS THE TRIPLE (AND PERSPECTIVE) EXTRACTION. IT LOOPS THROUGH FOUR TXT FILES (STATEMENTS, PERSPECTIVES,
WH-QUESTIONS AND VERB-QUESTIONS) WHICH CONTAIN SINGLE UTTERANCES AND THEIR IDEAL EXTRACTED TRIPLE.
THIS SCRIPT PROCESSES EACH UTTERANCE AND COMPARES THE TRIPLE EXTRACTED WITH THE IDEAL EXTRACTION, ELEMENTWISE.
THEREFORE EACH UTTERANCE MAY HAVE THREE COMPARISONS (SPO) OR MORE (IF COUNTING THE PERSPECTIVE).
TRIPLE ELEMENTS ARE ONLY COMPARED AT A LABEL LEVEL, NO TYPE INFORMATION IS TAKEN INTO ACCOUNT.
"""

import logging
from collections import defaultdict
from datetime import datetime
import json
from cltl.triple_extraction import logger

from cltl.triple_extraction.conversational_llama_analyzer import LlamaAnalyzer
from test_utils import log_report, report, test_triples

logger.setLevel(logging.ERROR)

MULTILINGUAL = True

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
            elif sample.startswith("personachat") or sample.startswith("daily_dialogs"):
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
                    if perspective == "negative":
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


def test_triples_in_file(analyzer_name, path, analyzer, resultfile,
                         speakers={'agent': 'leolani', 'speaker': 'lenka'}, is_question=False, verbose=True):
    """
    This function loads the test suite and gold standard and prints the mismatches between the system analysis of the
    test suite, including perspective if it is added, as well as the number of correctly and incorrectly extracted
    triple elements
    :param path: filepath of test file
    """
    results = {'not_parsed': 0, 'correct': 0, 'incorrect': 0,
               'correct_subjects': 0, 'incorrect_subjects': 0,
               'correct_predicates': 0, 'incorrect_predicates': 0,
               'correct_objects': 0, 'incorrect_objects': 0,
               'correct_perspective': 0, 'incorrect_perspective': 0}
    issues = defaultdict(dict)
    test_suite = load_golden_conversation_triples(path)

    log_report(f'\nRUNNING {len(test_suite)} UTTERANCES FROM FILE {path}\n', to_file=resultfile)
    for idx, item in enumerate(test_suite):
        print ('Item', idx, "out of", len(test_suite))
        results, issues = test_triples(item, results, issues, resultfile, analyzer,
                                       speakers=speakers, is_question=is_question, verbose=verbose)

    # print report
    result_dict = report(analyzer_name, test_suite, path, results, issues, resultfile, verbose=verbose)
    print(results)
    return result_dict

# def test_triples_in_file(path, analyzer, resultfile,
#                          speakers={'agent': 'leolani', 'speaker': 'lenka'}, verbose=True):
#     """
#     This function loads the test suite and gold standard and prints the mismatches between the system analysis of the
#     test suite, including perspective if it is added, as well as the number of correctly and incorrectly extracted
#     triple elements
#     :param path: filepath of test file
#     """
#     results = {'not_parsed': 0, 'correct': 0, 'incorrect': 0,
#                'correct_subjects': 0, 'incorrect_subjects': 0,
#                'correct_predicates': 0, 'incorrect_predicates': 0,
#                'correct_objects': 0, 'incorrect_objects': 0,
#                'correct_perspective': 0, 'incorrect_perspective': 0}
#     issues = defaultdict(dict)
#     test_suite = load_golden_conversation_triples(path)
#
#     log_report(f'\nRUNNING {len(test_suite)} UTTERANCES FROM FILE {path}\n', to_file=resultfile)
#     for item in test_suite:
#         results, issues = test_triples(item, results, issues, resultfile, analyzer, speakers=speakers, verbose=verbose)
#     # report
#     report(test_suite, path, results, issues, resultfile, verbose=verbose)


if __name__ == "__main__":
    '''
    test files with triples are formatted like so "test sentence : subject predicate object" 
    multi-word-expressions have dashes separating their elements, and are marked with apostrophes if they are a 
    collocation
    '''
    # Test with monolingual model or multilingual
    path = '/Users/piek/Desktop/d-Leolani/leolani-models/conversational_triples/22_04_27'
   # path = f'./../resources/conversational_triples/{"albert-base-v2" if not MULTILINGUAL else "google-bert"}'
    path = '/Users/piek/Desktop/d-Leolani/leolani-models/conversational_triples/2024-03-11'

    base_model = 'albert-base-v2' if not MULTILINGUAL else 'google-bert/bert-base-multilingual-cased'
    lang = 'en' #if not MULTILINGUAL else 'nl'

    # Set up logging file
    current_date = str(datetime.today().date())

    analyzer_name ="LLM"
    QWEN_MODEL = "qwen2.5"
    LLAMA_MODEL = "llama3.2"
    #MODEL = LLAMA_MODEL
    MODEL = QWEN_MODEL
    resultfilename = f"evaluation_reports/evaluation_CONVST_{analyzer_name}_{MODEL}_{current_date}.txt"
    resultjson = f"evaluation_reports/evaluation_CONVST_{analyzer_name}_{MODEL}_{current_date}.json"
    analyzer_name += "_" + MODEL
    resultfile = open(resultfilename, "w")
    # Select files to test
    all_test_files = [
        #"./data/conversation_test_examples/test_answer_ellipsis.txt",
        "./data/conversation_test_examples/test_coordination.txt",
        "./data/conversation_test_examples/test_coreference.txt",
        "./data/conversation_test_examples/test_declarative_statements.txt",
        "./data/conversation_test_examples/test_declarative_statements_negated.txt",
        "./data/conversation_test_examples/test_explicit_no_answers.txt",
        "./data/conversation_test_examples/test_explicit_yes_answers.txt",
        #"./data/conversation_test_examples/test_full.txt",
        # "./data/conversation_test_examples/test_implicit_negation.txt", #TODO not able to read data
        "./data/conversation_test_examples/test_single_utterances.txt"
    ]
    # Analyze utterances

    all_test_files = [
#        "./data/conversation_test_examples/test_answer_ellipsis.txt"
        "./data/conversation_test_examples/test_test.txt"
    ]
    # Analyze utterances
    analyzer = LlamaAnalyzer(model_name=MODEL,temperature=0.1, keep_alive=20)
    log_report(f'\nRUNNING {len(all_test_files)} FILES\n\n', to_file=resultfile)
    speakers = {'agent': 'speaker2', 'speaker': 'speaker1'}

    jsonresults = []
    for test_file in all_test_files:
        is_question = False
        if "question" in test_file:
            is_question = True
        result_dict = test_triples_in_file(analyzer_name=analyzer_name, path=test_file, analyzer=analyzer, speakers=speakers, is_question=is_question, resultfile=resultfile, verbose=True)
        jsonresults.append(result_dict)
    resultfile.close()

    with open (resultjson, 'w') as outfile:
        json.dump(jsonresults, outfile)
        outfile.close()