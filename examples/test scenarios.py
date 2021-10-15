from cltl.language.api import Chat, UtteranceHypothesis


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
    :param statement: one or several statements separated by a comma, to be stored in the brain
    :param questions: set of questions regarding the stored statement
    :param gold: gold standard reply
    :return: number of correct replies
    """
    correct = 0
    reply = None

    chat = Chat("Lenka")

    # one or several statements are added to the brain
    print(f'\n\n---------------------------------------------------------------\nSTATEMENTS')
    for statement in statements:
        chat.add_utterance([UtteranceHypothesis(statement, 1.0)])
        chat.last_utterance.analyze()

        print(f"\nUtterance: {chat.last_utterance}")
        print(f"Triple:      \t{chat.last_utterance.triple}")
        print(f"Perspective: \t{chat.last_utterance.perspective}")

    # brain is queried and a reply is generated and compared with golden standard
    print(f'\n\nQUESTIONS')
    for question in questions:
        chat.add_utterance([UtteranceHypothesis(question, 1.0)])
        chat.last_utterance.analyze()

        print(f"\nQuestion:   \t{chat.last_utterance}")
        print(f"Triple:            \t{chat.last_utterance.triple}")
        print(f"Response:          \t{reply}")
        print(f"Expected response: \t{gold.lower().strip()}")

        if reply is None or (reply.lower().strip() != gold.lower().strip()):
            pass
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
