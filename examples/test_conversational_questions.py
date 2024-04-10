"""
THIS SCRIPT TESTS THE TRIPLE (AND PERSPECTIVE) EXTRACTION. IT LOOPS THROUGH FOUR TXT FILES (STATEMENTS, PERSPECTIVES,
WH-QUESTIONS AND VERB-QUESTIONS) WHICH CONTAIN SINGLE UTTERANCES AND THEIR IDEAL EXTRACTED TRIPLE.
THIS SCRIPT PROCESSES EACH UTTERANCE AND COMPARES THE TRIPLE EXTRACTED WITH THE IDEAL EXTRACTION, ELEMENTWISE.
THEREFORE EACH UTTERANCE MAY HAVE THREE COMPARISONS (SPO) OR MORE (IF COUNTING THE PERSPECTIVE).
TRIPLE ELEMENTS ARE ONLY COMPARED AT A LABEL LEVEL, NO TYPE INFORMATION IS TAKEN INTO ACCOUNT.
"""
import logging
from datetime import datetime

from cltl.question_extraction.conversational_question_analyzer import ConversationalQuestionAnalyzer
from cltl.triple_extraction import logger
from test_utils import test_triples_in_file, log_report

logger.setLevel(logging.ERROR)

MULTILINGUAL = False

if __name__ == "__main__":
    '''
    test files with triples are formatted like so "test sentence : subject predicate object" 
    multi-word-expressions have dashes separating their elements, and are marked with apostrophes if they are a 
    collocation
    '''

    # Test with monolingual model or multilingual
    # path = '/Users/piek/Desktop/d-Leolani/leolani-models/conversational_triples/22_04_27'
    path = f'./../resources/conversational_triples/{"albert-base-v2" if not MULTILINGUAL else "google-bert"}'
    base_model = 'albert-base-v2' if not MULTILINGUAL else 'google-bert/bert-base-multilingual-cased'
    lang = 'en' if not MULTILINGUAL else 'nl'

    # Set up logging file
    current_date = str(datetime.today().date())
    resultfilename = f"evaluation_reports/evaluation_CONVSQ_{base_model.replace('/', '_')}_{current_date}.txt"
    resultfile = open(resultfilename, "w")

    # Select files to test
    all_test_files = [
        "./data/wh-questions.txt",
        # "./data/verb-questions.txt", # TODO error on objects starting with apostrophe
    ]

    # Analyze utterances
    analyzer = ConversationalQuestionAnalyzer(model_path=path, base_model=base_model, lang=lang)
    log_report(f'\nRUNNING {len(all_test_files)} FILES\n\n', to_file=resultfile)
    for test_file in all_test_files:
        test_triples_in_file(test_file, analyzer, resultfile, is_question=True, verbose=False)
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
