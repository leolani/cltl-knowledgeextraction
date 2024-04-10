import logging
from datetime import datetime
from time import sleep

from cltl.triple_extraction import logger
from cltl.triple_extraction.oie_analyzer import OIEAnalyzer
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
    resultfilename = f"evaluation_reports/evaluation_OIE_{current_date}.txt"
    resultfile = open(resultfilename, "w")

    # Select files to test
    all_test_files = [
        "./data/statements.txt",
        "./data/perspective.txt",
        "./data/kinship-friends.txt",
        "./data/activities.txt",
        "./data/feelings.txt",
        "./data/locations.txt",
        "./data/professions.txt"
    ]
    # Analyze utterances
    analyzer = OIEAnalyzer()
    log_report(f'\nRUNNING {len(all_test_files)} FILES\n\n', to_file=resultfile)
    for test_file in all_test_files:
        test_triples_in_file(test_file, analyzer, resultfile, verbose=False)
        sleep(10)
    resultfile.close()

    # OIE CORRECT  TRIPLE  ELEMENTS: 58  INCORRECT TRIPLE ELEMENTS: 206
