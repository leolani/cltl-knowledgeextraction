from cltl.triple_extraction.api import Chat


def compare_elementwise(triple, gold):
    """
    :param triple: triple extracted by the system
    :param gold: golden triple to compare with
    :return: number of correct elements in a triple
    """
    # correct = 0
    matches = {'triple': {}, 'perspective': {}}

    for key in triple:
        if key not in gold.keys():
            continue

        if type(triple[key]) == dict:
            match_result = triple[key]['label'].lower() == gold[key]
            matches['triple'][key] = int(match_result)
            if not match_result:
                print(f"Mismatch in triple {key}: {triple[key]['label'].lower()} != {gold[key]}")
            if match_result:
                print(f"Match triple {key}: {triple[key]} == {gold[key]}")
                # matches['score'] += 1

        elif type(triple[key]) == float:
            match_result = triple[key] == gold[key]
            matches['predicate'][key] = match_result
            if not match_result:
                print(f"Mismatch in perspective {key}: {triple[key]} != {gold[key]}")

    return matches


def recall(total, observed):
    recall = observed/total*100
    # accuracy = 100-error_rate

    return recall

def test_triples(item, results, issues, error_file, analyzer):
    chat = Chat("Leolani", "Lenka")
    # analyzer = CFGAnalyzer()

    chat.add_utterance(item['utterance'])
    if type(analyzer).__name__ in ['CFGAnalyzer', 'spacyAnalyzer', 'OIEAnalyzer']:
        analyzer.analyze(chat.last_utterance)
    elif type(analyzer).__name__ in ['StanzaQuestionAnalyzer', 'ConversationalAnalyzer']:
        analyzer.analyze_in_context(chat)

    # No triple was extracted, so we missed three items (s, p, o)
    if not chat.last_utterance.triples:
        print((chat.last_utterance, 'ERROR'))
        results['incorrect'] += 1
        issues[chat.last_utterance.transcript]['parsing'] = 'NOT PARSED'
        error_string = chat.last_utterance.transcript + ": " + item['triple']['subject'] + " " + item['triple'][
            'predicate'] + " " + item['triple']['object'] + "\n"
        error_file.write(error_string)
        issues[chat.last_utterance.transcript]['triple'] = error_string
        results['incorrect_subjects'] += 1
        results['incorrect_predicates'] += 1
        results['incorrect_objects'] += 1
        return results, issues

    # A triple was extracted so we compare it elementwise
    else:
        # Compare all extracted triples, select the one with the most correct elements
        triples_matches = [compare_elementwise(extracted_triple, item['triple'])
                           for extracted_triple in chat.last_utterance.triples]
        triples_scores = [sum(triple_match['triple'].values()) for triple_match in triples_matches]

        score_best_triple = max(triples_scores)
        idx_best_triple = triples_scores.index(score_best_triple)

        # add to statistics
        # correct += score_best_triple
        results['correct_subjects'] += triples_matches[idx_best_triple]['triple']['subject']
        results['incorrect_subjects'] += 1-triples_matches[idx_best_triple]['triple']['subject']
        results['correct_predicates'] += triples_matches[idx_best_triple]['triple']['predicate']
        results['incorrect_predicates'] += 1-(triples_matches[idx_best_triple]['triple']['predicate'])
        results['correct_objects'] += triples_matches[idx_best_triple]['triple']['object']
        results['incorrect_objects'] += 1-(triples_matches[idx_best_triple]['triple']['object'])
        # incorrect += (3 - score_best_triple)
        if score_best_triple < 3:
            issues[chat.last_utterance.transcript]['triple'] = (3 - score_best_triple)
            error_string = chat.last_utterance.transcript + ": " + item['triple']['subject'] + " " + item['triple'][
                'predicate'] + " " + item['triple']['object'] + "\n"
            error_file.write(error_string)

        # Report
        if score_best_triple==3:
            print("CORRECT")
            results['correct'] += 1
        else:
            print("INCORRECT")
            results['incorrect'] += 1
        print(f"\nUtterance: \t{chat.last_utterance}")
        print(f"Triple:            \t{chat.last_utterance.triples[idx_best_triple]}")
        print(f"Expected triple:   \t{item['triple']}")

        # Compare perspectives if available
        if 'perspective' in item.keys():
            best_persp = compare_elementwise(chat.last_utterance.triples[idx_best_triple]['perspective'],
                                                  item['perspective'])
            score_best_pesp = sum(best_persp['perspective'].values())

            # correct += score_best_pesp
            # incorrect += (3 - score_best_pesp[''])
            results['correct_perspective'] += score_best_pesp
            results['incorrect_perspective'] += 3-score_best_pesp
            if score_best_pesp < 3:
                issues[chat.last_utterance.transcript]['perspective'] = (3 - score_best_pesp)

            print(f"Expected perspective:   \t{item['perspective']}")

        return results, issues