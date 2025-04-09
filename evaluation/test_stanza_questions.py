"""
THIS SCRIPT TESTS THE TRIPLE-QUERY EXTRACTION. IT LOOPS THROUGH FOUR TXT FILES (WH-QUESTIONS AND VERB-QUESTIONS)
WHICH CONTAIN SINGLE QUESTIONS AND THEIR IDEAL EXTRACTED TRIPLE.
"""

import logging
from datetime import datetime

from cltl.question_extraction.stanza_question_analyzer import StanzaQuestionAnalyzer
from cltl.triple_extraction import logger
from test_utils import test_triples_in_file

logger.setLevel(logging.ERROR)

if __name__ == "__main__":
    '''
    test files with triples are formatted like so "test sentence : subject predicate object" 
    multi-word-expressions have dashes separating their elements, and are marked with apostrophes if they are a 
    collocation
    '''
    # Set up logging file
    current_date = str(datetime.today().date())
    resultfilename = f"evaluation_reports/evaluation_STANZAQ_{current_date}.txt"
    resultfile = open(resultfilename, "w")

    # Select files to test
    all_test_files = [
        "./data/wh-questions.txt",
        "./data/verb-questions.txt"
    ]

    # Analyze utterances
    analyzer = StanzaQuestionAnalyzer()
    print(f'\nRUNNING {len(all_test_files)} FILES\n\n')
    for test_file in all_test_files:
        test_triples_in_file(test_file, analyzer, resultfile, is_question=True, verbose=False)

# RAN 66 UTTERANCES FROM FILE ./data/wh-questions.txt
# CORRECT TRIPLE ELEMENTS: 132			INCORRECT TRIPLE ELEMENTS: 66
######## VERB QUESTIONS
# CORRECT TRIPLE ELEMENTS: 122			INCORRECT TRIPLE ELEMENTS: 67
