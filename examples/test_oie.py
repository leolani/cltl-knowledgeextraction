import logging
from datetime import datetime
from time import sleep
import json
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
    analyzer_name ="openIE"

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
    analyzer = OIEAnalyzer()
    log_report(f'\nRUNNING {len(all_test_files)} FILES\n\n', to_file=resultfile)

    jsonresults = []
    for test_file in all_test_files:
        result_dict = test_triples_in_file(analyzer_name,test_file, analyzer, resultfile, verbose=False)
        jsonresults.append(result_dict)
        sleep(10)
    resultfile.close()
    with open (resultjson, 'w') as outfile:
        json.dump(jsonresults, outfile)
        outfile.close()


    # OIE CORRECT  TRIPLE  ELEMENTS: 58  INCORRECT TRIPLE ELEMENTS: 206
