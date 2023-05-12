"""
THIS SCRIPT TESTS THE TRIPLE-QUERY EXTRACTION. IT LOOPS THROUGH FOUR TXT FILES (WH-QUESTIONS AND VERB-QUESTIONS)
WHICH CONTAIN SINGLE QUESTIONS AND THEIR IDEAL EXTRACTED TRIPLE.
"""

import json
from collections import defaultdict

from test_triples import compare_elementwise_triple
from test_triples import load_golden_triples

from cltl.triple_extraction.api import Chat
from cltl.question_extraction.stanza_question_analyzer import StanzaQuestionAnalyzer


def test_triples(item, correct, incorrect, issues, errorf, analyzer:StanzaQuestionAnalyzer):
    chat = Chat("leolani", "lenka")

    chat.add_utterance(item['utterance'])
    analyzer.analyze(item['utterance'])
    chat.last_utterance._triples = analyzer.triples

    # No triple was extracted, so we missed three items (s, p, o)
    if not chat.last_utterance.triples:
        print((chat.last_utterance, 'ERROR'))
        incorrect += 3
        issues[chat.last_utterance.transcript]['parsing'] = 'NOT PARSED'
        error_string = chat.last_utterance.transcript + ": " + item['triple']['subject'] + " " + item['triple'][
            'predicate'] + " " + item['triple']['object'] + "\n"
        errorf.write(error_string)
        issues[chat.last_utterance.transcript]['triple'] = error_string
        return correct, incorrect, issues

    # A triple was extracted so we compare it elementwise
    else:
        # Compare all extracted triples, select the one with the most correct elements
        triples_scores = [compare_elementwise_triple(extracted_triple, item['triple'])
                          for extracted_triple in chat.last_utterance.triples]

        score_best_triple = max(triples_scores)
        idx_best_triple = triples_scores.index(score_best_triple)

        # add to statistics
        correct += score_best_triple
        incorrect += (3 - score_best_triple)
        if score_best_triple < 3:
            issues[chat.last_utterance.transcript]['triple'] = (3 - score_best_triple)
            error_string = chat.last_utterance.transcript + ": " + item['triple']['subject'] + " " + item['triple'][
                'predicate'] + " " + item['triple']['object'] + "\n"
            errorf.write(error_string)
        # Report
        if score_best_triple==3:
            print("CORRECT")
        else:
            print("INCORRECT")
        print(f"\nUtterance: \t{chat.last_utterance}")
        print(f"Triple:            \t{chat.last_utterance.triples[idx_best_triple]}")
        print(f"Expected triple:   \t{item['triple']}")

        return correct, incorrect, issues


def test_triples_in_file(path, analyzer):
    """
    This function loads the test suite and gold standard and prints the mismatches between the system analysis of the
    test suite, including perspective if it is added, as well as the number of correctly and incorrectly extracted
    triple elements
    :param path: filepath of test file
    """
    correct = 0
    incorrect = 0
    issues = defaultdict(dict)
    test_suite = load_golden_triples(path)
    errorf = open(path + ".error.txt", "w")
    print(f'\nRUNNING {len(test_suite)} UTTERANCES FROM FILE {path}\n')

    for item in test_suite:
        print(f'\n---------------------------------------------------------------\n')
        correct, incorrect, issues = test_triples(item, correct, incorrect, issues, errorf, analyzer)
    errorf.close()

    print(f'\n\n\n---------------------------------------------------------------\nSUMMARY\n')
    print(f'\nRAN {len(test_suite)} UTTERANCES FROM FILE {path}\n')
    print(f'\nCORRECT TRIPLE ELEMENTS: {correct}\t\t\tINCORRECT TRIPLE ELEMENTS: {incorrect}')
    print(f"ISSUES ({len(issues)} UTTERANCES): {json.dumps(issues, indent=4, sort_keys=True, separators=(', ', ': '))}")


if __name__ == "__main__":
    '''
    test files with triples are formatted like so "test sentence : subject predicate object" 
    multi-word-expressions have dashes separating their elements, and are marked with apostrophes if they are a 
    collocation
    '''
    analyzer = StanzaQuestionAnalyzer()
    all_test_files = [
       # "./data/wh-questions.txt",
        "./data/verb-questions.txt"
    ]

    print(f'\nRUNNING {len(all_test_files)} FILES\n\n')

    for test_file in all_test_files:
        test_triples_in_file(test_file, analyzer)



# RAN 66 UTTERANCES FROM FILE ./data/wh-questions.txt
#
#
# CORRECT TRIPLE ELEMENTS: 132			INCORRECT TRIPLE ELEMENTS: 66
# CFG: # CORRECT TRIPLE ELEMENTS: 179			INCORRECT TRIPLE ELEMENTS: 19
# ISSUES (21 UTTERANCES): {
#     "what day is your birthday": {
#         "triple": 3
#     },
#     "what is my favorite TV show": {
#         "parsing": "NOT PARSED",
#         "triple": "what is my favorite TV show: lenka favorite-tv-show-is \n"
#     },
#     "what is your brother's name": {
#         "triple": 3
#     },
#     "what is your dog's name": {
#         "triple": 3
#     },
#     "when are you going to Mexico": {
#         "triple": 2
#     },
#     "when did Selene come": {
#         "parsing": "NOT PARSED",
#         "triple": "when did Selene come: selene come \n"
#     },
#     "when did you go to school": {
#         "triple": 2
#     },
#     "when is your father's birthday": {
#         "triple": 3
#     },
#     "where can I go": {
#         "parsing": "NOT PARSED",
#         "triple": "where can I go: lenka can-go \n"
#     },
#     "where did you go yesterday": {
#         "triple": 1
#     },
#     "where is my friend": {
#         "triple": 3
#     },
#     "where is selene from": {
#         "parsing": "NOT PARSED",
#         "triple": "where is selene from: selene be-from \n"
#     },
#     "where is your best friend": {
#         "triple": 3
#     },
#     "where is your friend": {
#         "triple": 3
#     },
#     "where was Selene born": {
#         "parsing": "NOT PARSED",
#         "triple": "where was Selene born: selene born \n"
#     },
#     "where were you born": {
#         "parsing": "NOT PARSED",
#         "triple": "where were you born: leolani born \n"
#     },
#     "which is your favorite color": {
#         "triple": 3
#     },
#     "who are your colleagues": {
#         "triple": 3
#     },
#     "who does Selene know": {
#         "parsing": "NOT PARSED",
#         "triple": "who does Selene know: selene know \n"
#     },
#     "who is your best friend": {
#         "triple": 3
#     },
#     "who will come to school": {
#         "triple": 1
#     }
# }

# CORRECT TRIPLE ELEMENTS: 179			INCORRECT TRIPLE ELEMENTS: 19
# ISSUES (7 UTTERANCES): {
#     "where is my friend": {
#         "triple": 2
#     },
#     "where is your friend": {
#         "triple": 2
#     },
#     "where was Selene born": {
#         "parsing": "NOT PARSED"
#     },
#     "where were you born": {
#         "parsing": "NOT PARSED"
#     },
#     "who are your colleagues": {
#         "triple": 3
#     },
#     "who is your best friend": {
#         "triple": 2
#     },
#     "who will come to school": {
#         "triple": 1
#     }
# }


######## VERB QUESTIONS
# CORRECT TRIPLE ELEMENTS: 122			INCORRECT TRIPLE ELEMENTS: 67
#### CFG results
# CORRECT TRIPLE ELEMENTS: 172			INCORRECT TRIPLE ELEMENTS: 17
# ISSUES (26 UTTERANCES): {
#     "am I your best friend": {
#         "parsing": "NOT PARSED",
#         "triple": "am I your best friend: leolani-best-friend be lenka\n"
#     },
#     "are you a girl": {
#         "triple": 1
#     },
#     "are you afraid of dogs": {
#         "triple": 1
#     },
#     "are your parents from the netherlands": {
#         "triple": 1
#     },
#     "can I call you": {
#         "parsing": "NOT PARSED",
#         "triple": "can I call you: lenka can-call leolani\n"
#     },
#     "can I make a cake": {
#         "parsing": "NOT PARSED",
#         "triple": "can I make a cake: lenka can-make a-cake\n"
#     },
#     "can my friend talk to you": {
#         "triple": 2
#     },
#     "can you sing": {
#         "triple": 2
#     },
#     "can you talk to me": {
#         "triple": 2
#     },
#     "can you tell me what is a dog": {
#         "parsing": "NOT PARSED",
#         "triple": "can you tell me what is a dog: a-dog be \n"
#     },
#     "can't you come to university": {
#         "triple": 2
#     },
#     "did lana read a book": {
#         "parsing": "NOT PARSED",
#         "triple": "did lana read a book: lana read a-book\n"
#     },
#     "did you go to school yesterday": {
#         "triple": 1
#     },
#     "did you talk with Selene": {
#         "triple": 2
#     },
#     "didn't you see Selene": {
#         "triple": 1
#     },
#     "do you know what a dog is": {
#         "parsing": "NOT PARSED",
#         "triple": "do you know what a dog is: a-dog be \n"
#     },
#     "does Selene know Suzana": {
#         "parsing": "NOT PARSED",
#         "triple": "does Selene know Suzana: selene know suzana\n"
#     },
#     "does john enjoy watching movies": {
#         "parsing": "NOT PARSED",
#         "triple": "does john enjoy watching movies: john enjoy watching-movies\n"
#     },
#     "does john live in the building": {
#         "triple": 1
#     },
#     "does selene know suzana": {
#         "parsing": "NOT PARSED",
#         "triple": "does selene know suzana: selene know suzana\n"
#     },
#     "have you ever been to Paris": {
#         "triple": 1
#     },
#     "haven't you been in New York": {
#         "triple": 2
#     },
#     "is purple your favorite color": {
#         "parsing": "NOT PARSED",
#         "triple": "is purple your favorite color: leolani favorite-color-is purple\n"
#     },
#     "is your best friend Selene": {
#         "parsing": "NOT PARSED",
#         "triple": "is your best friend Selene: leolani-best-friend be selene\n"
#     },
#     "is your favorite food pizza": {
#         "triple": 2
#     },
#     "is your friend called susie": {
#         "triple": 1
#     }
# }

#### CFG results
# CORRECT TRIPLE ELEMENTS: 172			INCORRECT TRIPLE ELEMENTS: 17
# ISSUES (9 UTTERANCES): {
#     "am I your best friend": {
#         "triple": 2
#     },
#     "can my friend talk to you": {
#         "triple": 2
#     },
#     "can you talk to me": {
#         "triple": 2
#     },
#     "can't you come to university": {
#         "triple": 2
#     },
#     "did you talk with Selene": {
#         "triple": 2
#     },
#     "didn't you see Selene": {
#         "triple": 1
#     },
#     "haven't you been in New York": {
#         "triple": 1
#     },
#     "is purple your favorite color": {
#         "triple": 3
#     },
#     "will you go to Paris": {
#         "triple": 1
#     }
# }
