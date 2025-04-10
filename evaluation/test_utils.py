import json
import pandas as pd
import os
from collections import defaultdict
from datetime import datetime
from cltl.triple_extraction.api import Chat, DialogueAct


def log_report(text, to_print=True, to_file=None):
    if to_file:
        to_file.write(f"\n{text}")
    if to_print:
        print(text)


def report(analyzer_name, test_suite, path, results, issues, resultfile, verbose=False):
    not_parsed = results['not_parsed']
    correct = results['correct']
    incorrect = results['incorrect']
    correct_subjects = results['correct_subjects']
    incorrect_subjects = results['incorrect_subjects']
    correct_predicates = results['correct_predicates']
    incorrect_predicates = results['incorrect_predicates']
    correct_objects = results['correct_objects']
    incorrect_objects = results['incorrect_objects']
    correct_perspective = results['correct_perspective']
    incorrect_perspective = results['incorrect_perspective']
    correct_certainty = results['correct_certainty']
    correct_polarity = results['correct_polarity']
    correct_sentiment = results['correct_sentiment']
    incorrect_certainty = results['incorrect_certainty']
    incorrect_polarity = results['incorrect_polarity']
    incorrect_sentiment = results['incorrect_sentiment']

    triple_precision = precision(incorrect+correct, correct)
    subject_precision = precision(correct_subjects+incorrect_subjects, correct_subjects)
    predicate_precision = precision(correct_predicates+incorrect_predicates, correct_predicates)
    objects_precision = precision(correct_objects+incorrect_objects, correct_objects)
    perspective_precision = precision(correct_perspective+incorrect_perspective, correct_perspective)
    elements_precision = precision(correct_subjects+correct_predicates+correct_objects+incorrect_subjects+incorrect_predicates+incorrect_objects, correct_subjects+correct_predicates+correct_objects)
    certainty_precision = precision(correct_certainty+incorrect_certainty, correct_certainty)
    polarity_precision = precision(correct_polarity+incorrect_polarity, correct_polarity)
    sentiment_precision = precision(correct_sentiment+incorrect_sentiment, correct_sentiment)

    # triple_recall = recall(len(test_suite), correct)
    # subject_recall = recall(len(test_suite), correct_subjects)
    # predicate_recall = recall(len(test_suite), correct_predicates)
    # objects_recall = recall(len(test_suite), correct_objects)
    # perspective_recall = recall(len(test_suite), correct_perspective)
    # elements_recall = recall(3*len(test_suite), correct_subjects+correct_predicates+correct_objects)

    result_dict = {"analyzer": analyzer_name}
    result_dict.update({"test_file": path})
    result_dict.update({"nr_utterances":len(test_suite)})
    result_dict.update({"no_triples":not_parsed})
    result_dict.update({"correct_triples": correct})
    result_dict.update({"incorrect_triples": incorrect})
    result_dict.update({"triple_precision": triple_precision})
    result_dict.update({"total triple elements": 3*len(test_suite)})
    result_dict.update({"correct triple elements": correct_subjects+correct_predicates+correct_objects})
    result_dict.update({"incorrect triple elements": incorrect_subjects+incorrect_predicates+incorrect_objects})
    result_dict.update({"precision triple elements": elements_precision})
    result_dict.update({"correct_subjects": correct_subjects})
    result_dict.update({"incorrect_subjects": incorrect_subjects})
    result_dict.update({"subjects_precision": subject_precision})
    result_dict.update({"correct_objects": correct_objects})
    result_dict.update({"incorrect_objects": incorrect_objects})
    result_dict.update({"objects_precision": objects_precision})
    result_dict.update({"correct_predicates": correct_predicates})
    result_dict.update({"incorrect_predicates": incorrect_predicates})
    result_dict.update({"predicates_precision": predicate_precision})
    result_dict.update({"correct_perspectives": correct_perspective})
    result_dict.update({"incorrect_perspectives": incorrect_perspective})
    result_dict.update({"perspectives_precision": perspective_precision})
    result_dict.update({"correct_certainty": correct_certainty})
    result_dict.update({"incorrect_certainty": incorrect_certainty})
    result_dict.update({"certainty_precision": certainty_precision})
    result_dict.update({"correct_polarity": correct_polarity})
    result_dict.update({"incorrect_polarity": incorrect_polarity})
    result_dict.update({"polarity_precision": polarity_precision})
    result_dict.update({"correct_sentiment": correct_sentiment})
    result_dict.update({"incorrect_sentiment": incorrect_sentiment})
    result_dict.update({"sentiment_precision": sentiment_precision})



    # result_dict.update({"triple_recall": triple_recall})
    # result_dict.update({"recall triple elements": elements_recall})
    # result_dict.update({"subjects_recall": subject_recall})
    # result_dict.update({"objects_recall": objects_recall})
    # result_dict.update({"predicates_recall": predicate_recall})
    # result_dict.update({"perspectives_recall": perspective_recall})

    log_report(f'\n\n\n---------------------------------------------------------------\nSUMMARY\n', to_file=resultfile)
    log_report(f'\nRAN {len(test_suite)} UTTERANCES FROM FILE {path}\n', to_file=resultfile)

    log_report(f'\nUTTERANCE WITHOUT TRIPLES: {not_parsed}', to_file=resultfile)
    log_report(f'\nCORRECT TRIPLES: {correct}\t\t\tINCORRECT TRIPLES: {incorrect}'
               f'\t\t\tACCURACY: {triple_precision:.2f}%', to_file=resultfile)
    log_report(f'\nCORRECT SUBJECTS: {correct_subjects}\t\t\tINCORRECT SUBJECTS: {incorrect_subjects}'
               f'\t\t\tACCURACY: {subject_precision:.2f}%', to_file=resultfile)
    log_report(f'\nCORRECT PREDICATES: {correct_predicates}\t\t\tINCORRECT PREDICATES: {incorrect_predicates}'
               f'\t\t\tACCURACY: {predicate_precision:.2f}%', to_file=resultfile)
    log_report(f'\nCORRECT OBJECTS: {correct_objects}\t\t\tINCORRECT OBJECTS: {incorrect_objects}'
               f'\t\t\tACCURACY: {objects_precision:.2f}%', to_file=resultfile)
    log_report(f'\nCORRECT PERSPECTIVES: {correct_perspective}\t\t\tINCORRECT PERSPECTIVES: {incorrect_perspective}'
               f'\t\t\tACCURACY: {perspective_precision:.2f}%', to_file=resultfile)

    if verbose:
        log_report(f"\nISSUES ({len(issues)} UTTERANCES): "
                   f"{json.dumps(issues, indent=4, sort_keys=True, separators=(', ', ': '))}", to_file=resultfile)
    return result_dict

def recall(total, observed):
    if total == 0:
        recall = 0
    else:
        recall = observed / total * 100
        # accuracy = 100-error_rate

    return recall

def precision(total, correct):
    if total == 0:
        precision = 0
    else:
        precision = correct / total * 100
        # accuracy = 100-error_rate

    return precision


def compare_elementwise(triple, gold, resultfile, verbose=True):
    """
    :param triple: triple extracted by the system
    :param gold: golden triple to compare with
    :return: number of correct elements in a triple
    """
    # correct = 0
    matches = {'triple': {}, 'perspective': {}}

    for key in triple:
        if key not in gold.keys():
            print('Key not in gold.keys in compare_elementwise', key, gold.keys())
            continue

        if type(triple[key]) == dict:
            # This is a triple
            if 'label' in triple[key]:
                match_result = triple[key]['label'].lower() == gold[key]
                matches['triple'][key] = int(match_result)

                # Report
                if verbose:
                    if not match_result:
                        log_report(f"Mismatch in triple {key}: {triple[key]['label'].lower()} != {gold[key]}",
                                   to_file=resultfile)
                    if match_result:
                        log_report(f"Match triple {key}: {triple[key]} == {gold[key]}", to_file=resultfile)
            else:
                print('ERROR', key, triple[key])
        elif type(triple[key]) == float:
            # This is a perspective
            match_result = triple[key] == gold[key]
            matches['perspective'][key] = match_result

            # Report
            if verbose:
                if not match_result:
                    log_report(f"Mismatch in perspective {key}: {triple[key]} != {gold[key]}", to_file=resultfile)
        else:
            print('Unknown value type in compare_elementwise', type(triple[key]))
    return matches


def load_golden_triples(filepath):
    """
    :param filepath: path to the test file with gold standard
    :return: set with test suite and a set with golden standard
    """
    file = open(filepath, "r")
    test = file.readlines()
    test_suite = []

    for sample in test:
        if sample == '\n':
            break

        try:
            # set utterance, triple and perspective
            # ignore perspectives that are added to the end of the statements separated with a second colon, e.g. they are not going to the university: they go-to the-university: not
            item = {'utterance': sample.split(':')[0], 'triple': {'subject': sample.split(':')[1].split()[0].lower(),
                                                                  'predicate': sample.split(':')[1].split()[1].lower(),
                                                                  'object': sample.split(':')[1].split()[2].lower()}}

            # set perspective if available
            if len(sample.split(':')) > 2:
                perspectives = sample.split(':')[2].split()
                if len(perspectives) == 3:
                    item['perspective'] = {'certainty': float(sample.split(':')[2].split()[0]),
                                           'polarity': float(sample.split(':')[2].split()[1]),
                                           'sentiment': float(sample.split(':')[2].split()[2])}

            # cleanup
            for k, v in item['triple'].items():
                if v == '?':
                    item['triple'][k] = ''

            test_suite.append(item)

        except:
            print(sample)

    return test_suite

def print_triple(triple):
    print = {'subject': triple['subject']['label'], 'predicate': triple['predicate']['label'], 'object':triple['object']['label']}
    return print

def test_triples(item, results, issues, resultfile, analyzer,
                 speakers={'agent': 'leolani', 'speaker': 'lenka'}, is_question=False, is_conversation=False, verbose=True):
    """
    Create a chat with the given speakers, add utterances in 'item' and analyze the last utterance
    Collect statistics on extracted triple elements
    """

    log_report(f'\n---------------------------------------------------------------\n', to_file=resultfile)

    # create chat and add utterance
    chat = Chat(agent=speakers['agent'], speaker=speakers['speaker'])

    # Check if item contains several utterances and add them
    if '<eos>' in item['utterance']:
        previous_utterances = item['utterance'].split('<eos>')
        item['utterance'] = previous_utterances[-1]
        previous_utterances = previous_utterances[:-1]

        # Determine speaker based on how long the dialogue history is (we must always end with agent, as the utterance to be analyzed is from the speaker)
        for i, p_utt in enumerate(previous_utterances):
            sp = speakers['speaker'] if (len(previous_utterances) % 2) == (i % 2) else speakers['agent']
            chat.add_utterance(p_utt, sp)
        log_report(f'\n{item["utterance"]}\n', to_file=resultfile)

    # Add last utterance, checking if it is a question
    if is_question:
        chat.add_utterance(item['utterance'], speakers['speaker'], [DialogueAct.QUESTION])
    else:
        chat.add_utterance(item['utterance'], speakers['speaker'], [DialogueAct.STATEMENT])

    # analyze utterance
    if type(analyzer).__name__ in ['CFGAnalyzer', 'spacyAnalyzer', 'OIEAnalyzer']:
        analyzer.analyze(chat)
    elif type(analyzer).__name__ in ['StanzaQuestionAnalyzer', 'ConversationalAnalyzer']:
       analyzer.analyze_in_context(chat)
    elif type(analyzer).__name__ in ['LLMAnalyzer']:
        if is_conversation:
            analyzer.analyze_in_context(chat)
        else:
            analyzer.analyze_last_utterance(chat)
    elif type(analyzer).__name__ in ['ConversationalQuestionAnalyzer']:
        analyzer.analyze_question_in_context(chat)

    # No triple was extracted, so we missed three items (s, p, o)
    if not chat.last_utterance.triples:
        # Log issues
        issues[chat.last_utterance.transcript]['parsing'] = 'NOT PARSED'
        issues[chat.last_utterance.transcript]['triple'] = f"{chat.last_utterance.transcript}: " \
                                                           f"{item['triple']['subject']} " \
                                                           f"{item['triple']['predicate']} " \
                                                           f"{item['triple']['object']}"
        results['not_parsed'] += 1
        results['incorrect'] += 1
        results['incorrect_subjects'] += 1
        results['incorrect_predicates'] += 1
        results['incorrect_objects'] += 1

        # Report
        log_report(f"\nUtterance: \t{chat.last_utterance}", to_file=resultfile)
        log_report(f"PARSE ERROR", to_file=resultfile)

        return results, issues

    # A triple was extracted so we compare it elementwise
    else:
        # Compare all extracted triples, select the one with the most correct elements
        triples_matches = [compare_elementwise(extracted_triple, item['triple'], resultfile, verbose)
                           for extracted_triple in chat.last_utterance.triples]
        triples_scores = [sum(triple_match['triple'].values()) for triple_match in triples_matches]
        score_best_triple = max(triples_scores)
        idx_best_triple = triples_scores.index(score_best_triple)

        # add to statistics
        results['correct_subjects'] += triples_matches[idx_best_triple]['triple']['subject']
        results['incorrect_subjects'] += 1 - triples_matches[idx_best_triple]['triple']['subject']
        results['correct_predicates'] += triples_matches[idx_best_triple]['triple']['predicate']
        results['incorrect_predicates'] += 1 - (triples_matches[idx_best_triple]['triple']['predicate'])
        results['correct_objects'] += triples_matches[idx_best_triple]['triple']['object']
        results['incorrect_objects'] += 1 - (triples_matches[idx_best_triple]['triple']['object'])

        if score_best_triple == 3:
            results['correct'] += 1

        elif score_best_triple < 3:
            results['incorrect'] += 1
            # Log issues
            issues[chat.last_utterance.transcript]['triple'] = f"{chat.last_utterance.transcript}: " \
                                                               f"{item['triple']['subject']} " \
                                                               f"{item['triple']['predicate']} " \
                                                               f"{item['triple']['object']}"

        # Report
        log_report(f"\nUtterance: \t{chat.last_utterance}", to_file=resultfile)
        log_report(f"Predicted Triple:  \t{print_triple(chat.last_utterance.triples[idx_best_triple])}", to_file=resultfile)
        log_report(f"Expected triple:   \t{item['triple']}", to_file=resultfile)

        # Compare perspectives if available
        if 'perspective' in item.keys():
            print(chat.last_utterance.triples)
            print(chat.last_utterance.triples[idx_best_triple])
            best_persp = compare_elementwise(chat.last_utterance.triples[idx_best_triple]['perspective'],
                                             item['perspective'], resultfile, verbose)
            score_best_pesp = sum(best_persp['perspective'].values())

            # add to statistics
            results['correct_perspective'] += score_best_pesp
            results['incorrect_perspective'] += 3 - score_best_pesp
            results['correct_certainty'] += best_persp['perspective']['certainty']
            results['incorrect_certainty'] += 1 - best_persp['perspective']['certainty']
            results['correct_polarity'] += best_persp['perspective']['polarity']
            results['incorrect_polarity'] += 1 - best_persp['perspective']['polarity']
            results['correct_sentiment'] += best_persp['perspective']['sentiment']
            results['incorrect_sentiment'] += 1 - best_persp['perspective']['sentiment']

            if score_best_pesp < 3:
                # Log issues
                issues[chat.last_utterance.transcript]['perspective'] = item['perspective']

            log_report(f"Predicted perspective:   \t{chat.last_utterance.triples[idx_best_triple]['perspective']}", to_file=resultfile)
            log_report(f"Expected perspective:   \t{item['perspective']}", to_file=resultfile)

        return results, issues


def test_triples_in_file(analyzer_name, path, analyzer, resultfile,
                         speakers={'agent': 'leolani', 'speaker': 'lenka'}, is_question=False, verbose=True):
    """
    This function loads the test suite and gold standard and prints the mismatches between the system analysis of the
    test suite, including perspective if it is added, as well as the number of correctly and incorrectly extracted
    triple elements
    :param path: filepath of test file
    """
    results = {'not_parsed': 0, 'correct': 0, 'incorrect': 0,
               'correct_subjects': 0, 'incorrect_subjects': 0,
               'correct_predicates': 0, 'incorrect_predicates': 0,
               'correct_objects': 0, 'incorrect_objects': 0,
               'correct_perspective': 0, 'incorrect_perspective': 0,
               'correct_certainty':0, 'incorrect_certainty':0,
               'correct_polarity':0, 'incorrect_polarity':0,
               'correct_sentiment':0, 'incorrect_sentiment':0
               }
    issues = defaultdict(dict)
    test_suite = load_golden_triples(path)

    log_report(f'\nRUNNING {len(test_suite)} UTTERANCES FROM FILE {path}\n', to_file=resultfile)
    for index, item in enumerate(test_suite):
        print (index, "out of", len(test_suite))
        results, issues = test_triples(item, results, issues, resultfile, analyzer,
                                       speakers=speakers, is_question=is_question, verbose=verbose)

    # print report
    result_dict = report(analyzer_name, test_suite, path, results, issues, resultfile, verbose=verbose)
    print(results)
    return result_dict

def get_overview(path):

    current_date = str(datetime.today().date())
    overviewfile = os.path.join(path, f"overview_{current_date}.csv")
   # overviewfile = os.path.join(path, f"CONVSToverview_{current_date}.csv")
    df = pd.DataFrame()
    for file in os.listdir(path):
        if not "evaluation_CONVST" in file and file.endswith(".json"):
            filepath= os.path.join(path, file)
            print(filepath)
            df_t = pd.read_json(filepath)
            df = pd.concat([df,df_t])
    df.to_csv(overviewfile)


if __name__ == "__main__":
    path = "evaluation_reports/2025-04-09/"
    get_overview(path)