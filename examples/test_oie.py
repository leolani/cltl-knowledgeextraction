from cltl.triple_extraction.api import Chat
from cltl.triple_extraction.cfg_analyzer import CFGAnalyzer
from cltl.triple_extraction.oie_analyzer import OIEAnalyzer
from cltl.triple_extraction.utils.helper_functions import utterance_to_capsules
from test_triples import load_golden_triples


def test_triples_in_file(path):
    """
    This function loads the test suite and gold standard and prints the mismatches between the system analysis of the
    test suite, including perspective if it is added, as well as the number of correctly and incorrectly extracted
    triple elements
    :param path: filepath of test file
    """

    test_suite = load_golden_triples(path)
    print(f'\nRUNNING {len(test_suite)} UTTERANCES FROM FILE {path}\n')

    chat = Chat("Lenka")

    analyzer_1 = OIEAnalyzer()
    analyzer_2 = CFGAnalyzer()

    for item in test_suite:
        print(f'\n---------------------------------------------------------------\n')

        chat.add_utterance(item['utterance'])

        analyzer_1.analyze(chat.last_utterance)
        capsules = utterance_to_capsules(chat.last_utterance)
        print(f"\nTriples:            \t{capsules}\n")

        analyzer_2.analyze(chat.last_utterance)
        capsules = utterance_to_capsules(chat.last_utterance)
        print(f"\nTriples:            \t{capsules}\n")


if __name__ == "__main__":
    '''
    test files with triples are formatted like so "test sentence : subject predicate object" 
    multi-word-expressions have dashes separating their elements, and are marked with apostrophes if they are a 
    collocation
    '''

    test_file = "./data/statements.txt"

    print(f'\nRUNNING {len(test_file)} STATEMENTS\n\n')

    test_triples_in_file(test_file)
