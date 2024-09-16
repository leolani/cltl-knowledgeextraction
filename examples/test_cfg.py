"""
THIS SCRIPT TESTS THE TRIPLE (AND PERSPECTIVE) EXTRACTION. IT LOOPS THROUGH FOUR TXT FILES (STATEMENTS, PERSPECTIVES,
WH-QUESTIONS AND VERB-QUESTIONS) WHICH CONTAIN SINGLE UTTERANCES AND THEIR IDEAL EXTRACTED TRIPLE.
THIS SCRIPT PROCESSES EACH UTTERANCE AND COMPARES THE TRIPLE EXTRACTED WITH THE IDEAL EXTRACTION, ELEMENTWISE.
THEREFORE EACH UTTERANCE MAY HAVE THREE COMPARISONS (SPO) OR MORE (IF COUNTING THE PERSPECTIVE).
TRIPLE ELEMENTS ARE ONLY COMPARED AT A LABEL LEVEL, NO TYPE INFORMATION IS TAKEN INTO ACCOUNT.
"""

import logging
from datetime import datetime

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
    resultfilename = f"evaluation_reports/evaluation_CFG_{current_date}.txt"
    resultfile = open(resultfilename, "w")

    # Select files to test
    all_test_files = [
        "./data/statements.txt",
        "./data/verb-questions.txt",
        "./data/wh-questions.txt",
        # "./data/perspective.txt",
        # "./data/kinship-friends.txt",
        # "./data/activities.txt",
        # "./data/feelings.txt",
        # "./data/locations.txt",
        # "./data/professions.txt"
    ]

    # Analyze utterances
    analyzer = CFGAnalyzer()
    log_report(f'\nRUNNING {len(all_test_files)} FILES\n\n', to_file=resultfile)
    for test_file in all_test_files:
        test_triples_in_file(test_file, analyzer, resultfile, verbose=False)
    resultfile.close()

    '''
    d.d. 20/01/2023
    CORRECT TRIPLE ELEMENTS: 225			INCORRECT TRIPLE ELEMENTS: 39
    ISSUES (19 UTTERANCES):
    
    CORRECT TRIPLE ELEMENTS: 187			INCORRECT TRIPLE ELEMENTS: 77
ISSUES (37 UTTERANCES)
    '''
