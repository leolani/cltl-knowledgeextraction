# from src.brain import LongTermMemory

from cltl.combot.backend.api.discrete import UtteranceType
from cltl.language.api import Chat, UtteranceHypothesis


def load_golden_triples(filepath):
    '''
    :param filepath: path to the test file with gold standard
    :return: set with test suite and a set with golden standard
    '''
    file = open(filepath, "r")

    test = file.readlines()
    test_suite = []
    gold = []

    for sample in test:
        triple = {}
        if sample == '\n':
            break

        test_suite.append(sample.split(':')[0])
        triple['subject'] = sample.split(':')[1].split()[0].lower()
        triple['predicate'] = sample.split(':')[1].split()[1].lower()
        if len(sample.split(':')[1].split()) > 2:
            triple['complement'] = sample.split(':')[1].split()[2].lower()
        else:
            triple['complement'] = ''

        if len(sample.split(':')) > 2:
            triple['perspective'] = {}
            triple['perspective']['certainty'] = float(sample.split(':')[2].split()[0])
            triple['perspective']['polarity'] = float(sample.split(':')[2].split()[1])
            triple['perspective']['sentiment'] = float(sample.split(':')[2].split()[2])

        for el in triple:
            if triple[el] == '?':
                triple[el] = ''

        gold.append(triple)

    return test_suite, gold


def compare_triples(triple, gold):
    '''
    :param triple: triple extracted by the system
    :param gold: golden triple to compare with
    :return: number of correct elements in a triple
    '''
    correct = 0

    if str(triple.predicate) == gold['predicate']:
        correct += 1
    else:
        print(('MISMATCH: ', triple.predicate, gold['predicate']))

    if str(triple.subject) == gold['subject']:
        correct += 1
    else:
        print(('MISMATCH: ', triple.subject, gold['subject']))

    if str(triple.complement) == gold['complement']:
        correct += 1
    else:
        print(('MISMATCH: ', triple.complement, gold['complement']))

    return correct


def test_with_triples(path):
    '''
    This function loads the test suite and gold standard and prints the mismatches between the system analysis of the test suite,
    including perspective if it is added, as well as the number of correctly and incorrectly extracted triple elements
    :param path: filepath of test file
    '''
    chat = Chat("Lenka")
    # WARNING! this deletes everything in the brain, must only be used for testing
    brain = LongTermMemory(clear_all=True)

    index = 0
    correct = 0
    incorrect = 0
    issues = {}
    test_suite, gold = load_golden_triples(path)

    for utterance in test_suite:
        chat.add_utterance([UtteranceHypothesis(utterance, 1.0)])
        chat.last_utterance.analyze()

        if chat.last_utterance.triple == None:
            print((chat.last_utterance, 'ERROR'))
            incorrect += 3
            index += 1
            issues[chat.last_utterance.transcript] = 'NOT PARSED'
            continue

        t = compare_triples(chat.last_utterance.triple, gold[index])
        if t < 3:
            issues[chat.last_utterance.transcript] = t
        correct += t
        incorrect += (3 - t)

        if chat.last_utterance.type == UtteranceType.QUESTION:
            brain_response = brain.query_brain(chat.last_utterance)
            # reply = reply_to_question(brain_response)
            # print(reply)

        else:
            if 'perspective' in gold[index]:
                perspective = chat.last_utterance.perspective
                extracted_perspective = {'polarity': perspective.polarity, 'certainty': perspective.certainty,
                                         'sentiment': perspective.sentiment}
                for key in extracted_perspective:
                    if float(extracted_perspective[key]) != gold[index]['perspective'][key]:
                        print(
                            ('MISMATCH PERSPECTIVE ', key, extracted_perspective[key], gold[index]['perspective'][key]))
                        incorrect += 1
                        issues[chat.last_utterance.transcript] = [extracted_perspective[key],
                                                                  gold[index]['perspective'][key]]
                    else:
                        correct += 1

        index += 1

    print((correct, incorrect))
    print(('issues ', issues))

    return


if __name__ == "__main__":
    '''
    test files with triples are formatted like so "test sentence : subject predicate complement" 
    multi-word-expressions have dashes separating their elements, and are marked with apostrophes if they are a collocation
    test files with scenarios are formatted like so "statement - question1, question2, etc - reply"
    '''

    all_test_files = ["./data/wh-questions.txt", "./data/verb-questions.txt",
                      "./data/statements.txt", "./data/perspective.txt"]

    for test_file in all_test_files:
        test_with_triples(test_file)
