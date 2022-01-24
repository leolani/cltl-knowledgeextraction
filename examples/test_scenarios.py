"""
THIS SCRIPT TESTS SCENARIOS FOR TWO-AGENT INTERACTION.
THE FIRST PART CONSISTS OF ONE OR MORE STATEMENTS, FOLLOWED BY ONE OR MORE QUESTIONS RELATED TO SAID STATEMENTS.
THIS SCRIPT IS SUPPOSED TO EVALUATE THE RESPONSES TO THE QUESTIONS. HOWEVER, LANGUAGE GENERATION IS NOT INCLUDED IN
THIS PACKAGE SO THE BEHAVIOUR CANNOT BE COMPARED.
"""

from cltl.triple_extraction.api import Chat, UtteranceHypothesis
from cltl.triple_extraction.cfg_analyzer import CFGAnalyzer


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


def test_scenario(statements, questions, gold):
    """
    :param statements: one or several statements separated by a comma, to be stored in the brain
    :param questions: set of questions regarding the stored statement
    :param gold: gold standard reply
    :return: number of correct replies
    """

    print(f'\n\n---------------------------------------------------------------')
    correct = 0
    reply = None

    chat = Chat("Lenka")
    analyzer = CFGAnalyzer()

    # one or several statements are added to the brain
    print(f'\nSTATEMENTS\n')
    for statement in statements:
        chat.add_utterance([UtteranceHypothesis(statement, 1.0)])
        analyzer.analyze(chat.last_utterance)

        print(f"Utterance: {chat.last_utterance}")
        print(f"Triple:      \t{chat.last_utterance.triple}")
        print(f"Perspective: \t{chat.last_utterance.perspective}\n")

    # brain is queried and a reply is generated and compared with golden standard
    print(f'\nQUESTIONS\n')
    for question in questions:
        chat.add_utterance([UtteranceHypothesis(question, 1.0)])
        analyzer.analyze(chat.last_utterance)

        print(f"Question:   \t{chat.last_utterance}")
        print(f"Triple:            \t{chat.last_utterance.triple}")
        print(f"Response:          \t{reply}")
        print(f"Expected response: \t{gold.lower().strip()}\n")

        if reply is None or (reply.lower().strip() != gold.lower().strip()):
            continue
        else:
            correct += 1

    return correct


def test_scenarios():
    """
    This functions opens the scenarios test file and runs the test for all the scenarios
    :return: number of correct and number of incorrect replies
    """
    scenarios = load_scenarios("./data/scenarios.txt")
    correct = 0
    total = 0

    print(f'\nRUNNING {len(scenarios)} SCENARIOS\n\n\n')

    for sc in scenarios:
        correct += test_scenario(sc['statement'], sc['questions'], sc['reply'])
        total += len(sc['questions'])

    print(f'\n\n\n---------------------------------------------------------------\nTOTAL\n')
    print(f'\nCORRECT RESPONSES: {correct}\tINCORRECT RESPONSES: {total - correct}')


if __name__ == "__main__":
    '''
    test files with scenarios are formatted like so "statement - question1, question2, etc - reply"
    multi-word-expressions have dashes separating their elements, and are marked with apostrophes if they are a 
    collocation
    '''

    test_scenarios()
