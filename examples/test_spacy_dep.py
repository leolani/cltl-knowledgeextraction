"""
THIS SCRIPT TESTS THE TRIPLE (AND PERSPECTIVE) EXTRACTION. IT LOOPS THROUGH FOUR TXT FILES (STATEMENTS, PERSPECTIVES,
WH-QUESTIONS AND VERB-QUESTIONS) WHICH CONTAIN SINGLE UTTERANCES AND THEIR IDEAL EXTRACTED TRIPLE.
THIS SCRIPT PROCESSES EACH UTTERANCE AND COMPARES THE TRIPLE EXTRACTED WITH THE IDEAL EXTRACTION, ELEMENTWISE.
THEREFORE EACH UTTERANCE MAY HAVE THREE COMPARISONS (SPO) OR MORE (IF COUNTING THE PERSPECTIVE).
TRIPLE ELEMENTS ARE ONLY COMPARED AT A LABEL LEVEL, NO TYPE INFORMATION IS TAKEN INTO ACCOUNT.
"""

import logging
from datetime import datetime
import json
from cltl.triple_extraction import logger
from cltl.triple_extraction.spacy_analyzer import spacyAnalyzer
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
    analyzer_name ="spaCy"

    resultfilename = f"evaluation_reports/evaluation_{analyzer_name}_{current_date}.txt"
    resultjson = f"evaluation_reports/evaluation_{analyzer_name}_{current_date}.json"

    resultfile = open(resultfilename, "w")

    # Select files to test
    all_test_files = [
        "./data/statements.txt",
        "./data/verb-questions.txt",
        "./data/wh-questions.txt",
        "./data/perspective.txt",
        "./data/kinship-friends.txt",
        "./data/activities.txt",
        "./data/feelings.txt",
        "./data/locations.txt",
        "./data/professions.txt"
    ]

    # Analyze utterances
    analyzer = spacyAnalyzer()
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

    # SPACY CORRECT TRIPLE ELEMENTS: 87			INCORRECT TRIPLE ELEMENTS: 177
