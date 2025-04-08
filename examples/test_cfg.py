"""
THIS SCRIPT TESTS THE TRIPLE (AND PERSPECTIVE) EXTRACTION. IT LOOPS THROUGH FOUR TXT FILES (STATEMENTS, PERSPECTIVES,
WH-QUESTIONS AND VERB-QUESTIONS) WHICH CONTAIN SINGLE UTTERANCES AND THEIR IDEAL EXTRACTED TRIPLE.
THIS SCRIPT PROCESSES EACH UTTERANCE AND COMPARES THE TRIPLE EXTRACTED WITH THE IDEAL EXTRACTION, ELEMENTWISE.
THEREFORE EACH UTTERANCE MAY HAVE THREE COMPARISONS (SPO) OR MORE (IF COUNTING THE PERSPECTIVE).
TRIPLE ELEMENTS ARE ONLY COMPARED AT A LABEL LEVEL, NO TYPE INFORMATION IS TAKEN INTO ACCOUNT.
"""

import logging
import os
from datetime import datetime
import json

from cltl.triple_extraction import logger
from cltl.triple_extraction.cfg_analyzer import CFGAnalyzer
from test_utils import test_triples_in_file, log_report

logger.setLevel(logging.ERROR)

if __name__ == "__main__":
    '''
    test files with triples are formatted like so "test sentence : subject predicate object" 
    multi-word-expressions have dashes separating their elements, and are marked with apostrophes if they are a 
    collocation
    '''
    # Set up logging file
    current_date = str(datetime.today().date())
    analyzer_name ="CFG"
    report_folder = os.path.join("evaluation_reports", current_date)
    if not os.path.exists(report_folder):
        os.mkdir(report_folder)
#    resultfilename = f"evaluation_reports/evaluation_{analyzer_name}_{current_date}.txt"
#    resultjson = f"evaluation_reports/evaluation_{analyzer_name}_{current_date}.json"
    resultfilename = f"{report_folder}/evaluation_{analyzer_name}_{current_date}.txt"
    resultjson = f"{report_folder}/evaluation_{analyzer_name}_{current_date}.json"
    resultfile = open(resultfilename, "w")

    # Select files to test
    all_test_files = [
        "./data/statements.txt",
        "./data/verb-questions.txt",
        "./data/wh-questions.txt",
        "./data/perspective.txt",
        # "./data/kinship-friends.txt",
        # "./data/activities.txt",
        # "./data/feelings.txt",
        # "./data/locations.txt",
        # "./data/professions.txt"
    ]
    #all_test_files = ["./data/professions.txt.error.txt"]
    # Analyze utterances
    analyzer = CFGAnalyzer()
    log_report(f'\nRUNNING {len(all_test_files)} FILES\n\n', to_file=resultfile)
    jsonresults = []

    for test_file in all_test_files:
        is_question = False
        if "question" in test_file:
            is_question = True
        result_dict = test_triples_in_file(analyzer_name=analyzer_name, path=test_file, analyzer=analyzer, is_question=is_question, resultfile=resultfile, verbose=True)
        jsonresults.append(result_dict)
    resultfile.close()
    with open (resultjson, 'w') as outfile:
        json.dump(jsonresults, outfile)
        outfile.close()

    '''
    d.d. 20/01/2023
    CORRECT TRIPLE ELEMENTS: 225			INCORRECT TRIPLE ELEMENTS: 39
    ISSUES (19 UTTERANCES):
    
    CORRECT TRIPLE ELEMENTS: 187			INCORRECT TRIPLE ELEMENTS: 77
ISSUES (37 UTTERANCES)

    d.d. 16 - 09 - 2024

RAN 88 UTTERANCES FROM FILE ./data/statements.txt
UTTERANCE WITHOUT TRIPLES: 2
CORRECT TRIPLES: 25			INCORRECT TRIPLES: 63			RECALL: 28.41%
CORRECT SUBJECTS: 34			INCORRECT SUBJECTS: 54			RECALL: 38.64%
CORRECT PREDICATES: 50			INCORRECT PREDICATES: 38			RECALL: 56.82%
CORRECT OBJECTS: 59			INCORRECT OBJECTS: 29			RECALL: 67.05%
CORRECT PERSPECTIVES: 0			INCORRECT PERSPECTIVES: 0			RECALL: 0.00%

RAN 63 UTTERANCES FROM FILE ./data/verb-questions.txt
UTTERANCE WITHOUT TRIPLES: 0
CORRECT TRIPLES: 29			INCORRECT TRIPLES: 34			RECALL: 46.03%
CORRECT SUBJECTS: 55			INCORRECT SUBJECTS: 8			RECALL: 87.30%
CORRECT PREDICATES: 33			INCORRECT PREDICATES: 30			RECALL: 52.38%
CORRECT OBJECTS: 50			INCORRECT OBJECTS: 13			RECALL: 79.37%
CORRECT PERSPECTIVES: 0			INCORRECT PERSPECTIVES: 0			RECALL: 0.00%

RAN 66 UTTERANCES FROM FILE ./data/wh-questions.txt
UTTERANCE WITHOUT TRIPLES: 2
CORRECT TRIPLES: 25			INCORRECT TRIPLES: 41			RECALL: 37.88%
CORRECT SUBJECTS: 43			INCORRECT SUBJECTS: 23			RECALL: 65.15%
CORRECT PREDICATES: 28			INCORRECT PREDICATES: 38			RECALL: 42.42%
CORRECT OBJECTS: 57			INCORRECT OBJECTS: 9			RECALL: 86.36%
CORRECT PERSPECTIVES: 0			INCORRECT PERSPECTIVES: 0			RECALL: 0.00%
    '''
