"""
THIS SCRIPT TESTS SCENARIOS FOR TWO-AGENT INTERACTION.
THE FIRST PART CONSISTS OF ONE OR MORE STATEMENTS, FOLLOWED BY ONE OR MORE QUESTIONS RELATED TO SAID STATEMENTS.
THIS SCRIPT IS SUPPOSED TO EVALUATE THE RESPONSES TO THE QUESTIONS. HOWEVER, LANGUAGE GENERATION IS NOT INCLUDED IN
THIS PACKAGE SO THE BEHAVIOUR CANNOT BE COMPARED.
"""

import json
import logging
from datetime import datetime

from cltl.triple_extraction import logger
from cltl.triple_extraction.api import Chat
from cltl.triple_extraction.cfg_analyzer import CFGAnalyzer
from test_utils import log_report

logger.setLevel(logging.ERROR)


def load_scenarios(filepath):
    """
    :param filepath: path to the test file
    :return: dictionary which contains the initial statement, a set of questions, and the golden standard reply
    """
    file = open(filepath, "r")
    test = file.readlines()
    scenarios = []

    for sample in test:
        if sample == '\n':
            break

        # set statement, questions and replies
        scenario = {'statement': sample.split(' - ')[0].split(','),
                    'questions': sample.split(' - ')[1].split(','),
                    'reply': sample.split(' - ')[2]}

        scenarios.append(scenario)

    return scenarios


def test_scenario(statements, questions, gold, resultfile):
    """
    :param statements: one or several statements separated by a comma, to be stored in the brain
    :param questions: set of questions regarding the stored statement
    :param gold: gold standard reply
    :return: number of correct replies
    """

    log_report(f'\n\n---------------------------------------------------------------', to_file=resultfile)

    chat = Chat("Leolani", "Lenka")
    analyzer = CFGAnalyzer()

    # one or several statements are added to the brain
    log_report(f'\nSTATEMENTS\n', to_file=resultfile)
    for statement in statements:
        chat.add_utterance(statement)
        analyzer.analyze(chat.last_utterance)

        log_report(f"Utterance: {chat.last_utterance}", to_file=resultfile)
        log_report(f"Triple:      \t{json.dumps(chat.last_utterance.triples)}", to_file=resultfile)

    # brain is queried and a reply is generated and compared with golden standard
    log_report(f'\nQUESTIONS\n', to_file=resultfile)
    for question in questions:
        chat.add_utterance(question)
        analyzer.analyze(chat.last_utterance)

        log_report(f"Question:   \t{chat.last_utterance}", to_file=resultfile)
        log_report(f"Triple:            \t{json.dumps(chat.last_utterance.triples)}", to_file=resultfile)
        log_report(f"Expected response: \t{gold.lower().strip()}\n", to_file=resultfile)


def test_scenarios(resultfile):
    """
    This functions opens the scenarios test file and runs the test for all the scenarios
    :return: number of correct and number of incorrect replies
    """
    scenarios = load_scenarios("./data/scenarios.txt")
    tot_statements = 0
    tot_questions = 0

    log_report(f'\nRUNNING {len(scenarios)} SCENARIOS\n\n\n', to_file=resultfile)

    for sc in scenarios:
        test_scenario(sc['statement'], sc['questions'], sc['reply'], resultfile)
        tot_statements += len(sc['statement'])
        tot_questions += len(sc['questions'])

    log_report(f'\n\n\n---------------------------------------------------------------\nTOTAL\n', to_file=resultfile)
    log_report(f'\nTOTAL SCENARIOS: {len(scenarios)}\tSTATEMENTS: {tot_statements}\tQUESTIONS: {tot_questions}',
               to_file=resultfile)


if __name__ == "__main__":
    '''
    test files with scenarios are formatted like so "statement - question1, question2, etc - reply"
    multi-word-expressions have dashes separating their elements, and are marked with apostrophes if they are a 
    collocation
    '''
    # Set up logging file
    current_date = str(datetime.today().date())
    resultfilename = f"evaluation_reports/evaluation_CFGSC_{current_date}.txt"
    resultfile = open(resultfilename, "w")

    test_scenarios(resultfile)
