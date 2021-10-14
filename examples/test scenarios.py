from cltl.language.api import Chat, UtteranceHypothesis


def load_scenarios(filepath):
    '''
    :param filepath: path to the test file
    :return: dictionary which contains the initial statement, a set of questions, and the golden standard reply
    '''
    file = open(filepath, "r")
    test = file.readlines()
    scenarios = []

    for sample in test:
        if sample == '\n':
            break
        scenario = {'statement': sample.split(' - ')[0], 'questions': [], 'reply': sample.split(' - ')[2]}
        for el in sample.split(' - ')[1].split(','):
            scenario['questions'].append(el)

        scenarios.append(scenario)

    return scenarios


def test_scenario(statement, questions, gold):
    '''
    :param statement: one or several statements separated by a comma, to be stored in the brain
    :param questions: set of questions regarding the stored statement
    :param gold: gold standard reply
    :return: number of correct replies
    '''
    correct = 0
    reply = None
    chat = Chat("Lenka")

    # one or several statements are added to the brain
    print(f'"\n\n---------------------------------------------------------------\nSTATEMENTS\n')
    if ',' in statement:
        for stat in statement.split(','):
            chat.add_utterance([UtteranceHypothesis(stat, 1.0)])
            chat.last_utterance.analyze()
    else:
        chat.add_utterance([UtteranceHypothesis(statement, 1.0)])
        chat.last_utterance.analyze()

    print(chat.last_utterance.triple)

    # brain is queried and a reply is generated and compared with golden standard
    print(f'"\n\n---------------------------------------------------------------\nQUESTIONS\n')
    for question in questions:
        chat.add_utterance([UtteranceHypothesis(question, 1.0)])
        chat.last_utterance.analyze()

        if reply is None:
            print(('MISMATCH RESPONSE ', reply, gold.lower().strip()))
        elif '-' in reply:
            reply = reply.replace('-', ' ')
        elif reply.lower().strip() != gold.lower().strip():
            print(('MISMATCH RESPONSE ', reply.lower().strip(), gold.lower().strip()))
        else:
            correct += 1

    return correct


def test_scenarios():
    '''
    This functions opens the scenarios test file and runs the test for all the scenarios
    :return: number of correct and number of incorrect replies
    '''
    scenarios = load_scenarios("./data/scenarios.txt")
    correct = 0
    total = 0
    for sc in scenarios:
        correct += test_scenario(sc['statement'], sc['questions'], sc['reply'])
        total += len(sc['questions'])

    print((f'\n\nCORRECT: ', correct, ',\tINCORRECT: ', total - correct))


if __name__ == "__main__":
    '''
    test files with triples are formatted like so "test sentence : subject predicate complement" 
    multi-word-expressions have dashes separating their elements, and are marked with apostrophes if they are a collocation
    test files with scenarios are formatted like so "statement - question1, question2, etc - reply"
    '''

    test_scenarios()
