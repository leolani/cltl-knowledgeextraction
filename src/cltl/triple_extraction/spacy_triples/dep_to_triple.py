def predicateInfoToTriple(pred_info: dict, predicate: str):
    triple = None
    if pred_info.get('head') and pred_info.get('tail'):
        triple = {'predicate': {'label': predicate, 'type': []},
                  'subject': {'label': pred_info.get('head'), 'type': []},
                  'object': {'label': pred_info.get('tail'), 'type': []}
                  }

    return triple


# Recursive function that takes the token id of the head to get all tokens that directly or indirectly depend on it given a spaCy sentence object
# There is an additional parameter exclude_id to indicate which dependent constituent should be excluded.
# The result is a list of tokens

def get_dependent_tokens(head_id, exclude_id, sent):
    tokens = []
    for token in sent:
        ### check if this token is not the same as the head token itself nor the excluded token
        if token.i != head_id and token.i != exclude_id:
            head = token.head
            ### check of this token is indeed dependent on the head token
            if (head_id == head.i):
                ### we want this token and put it in the result list
                tokens.append(token.i)
                ### we recursively call the function again with our new token to see if there are other tokens that depend on the new token
                nested_tokens = get_dependent_tokens(token.i, exclude_id, sent)
                ### if we have a result, we extend the result list with the deeper tokens
                if nested_tokens:
                    tokens.extend(nested_tokens)
    return tokens


# Input prarameter is a spaCy sentence
def get_predicate_subject_complement_phrases(doc, sent):
    """
    extract predicates with:
    -subject phrase
    -complement phrase

    :param spacy.tokens.Sent sent: spaCy object after processing text

    :rtype: list
    :return: list of tuples (predicate, subject, complement)
    """

    ### result list that is returned
    output = []

    ### we use a dictionary to collect all predicates and their corresponding subjects if any
    predicates = {}

    ### We first get the token that has a nsubj dependency with the main verb
    for token in sent:
        if (token.dep_ == 'nsubj'):
            predicates[token.head.i] = token.i

    ### Note that the next loop is not executed if there are no predicates with such a subject.
    for pred_token, pred_info in predicates.items():
        ## We get the subject identifier for this predicate
        subject_id = pred_info
        ### We get all the tokens that make up the subject phrase
        subject_tokens = get_dependent_tokens(subject_id, pred_token, sent)
        subject_tokens.extend([subject_id])
        ### We sort the tokens to get them in the right order
        subject_tokens.sort()
        ### We get the full phrase from the subject tokens
        subject_phrase = ""
        for token in subject_tokens:
            subject_phrase += " " + doc[token].text

        ### We get all the tokens that make up the complement phrase, we exclude the subject
        complement_tokens = get_dependent_tokens(pred_token, subject_id, sent)
        ### We sort the phrase to get the tokens in the right order
        complement_tokens.sort()

        if complement_tokens:
            complement_phrase = ""
            for token in complement_tokens:
                complement_phrase += " " + doc[token].text
            one_row = (doc[pred_token].lemma_,
                       subject_phrase,
                       complement_phrase
                       )
            output.append(one_row)

    return output


def get_subclause(nlp, utterance: str):
    doc = nlp(utterance)
    predicates = {}
    for token in doc:
        if token.dep_ == "xcomp":
            ### subject raising
            #### this is a root, so we consider it a predicate
            predicates[token.i] = dict()
            predicates[token.i]['head'] = None
            predicates[token.i]['tail'] = None
        elif token.dep_ == "ccomp":
            #### full clause
            predicates[token.i] = dict()
            predicates[token.i]['head'] = None
            predicates[token.i]['tail'] = None
    return predicates


def get_subj_obj_triples_with_spacy(nlp, utterance: str, SPEAKER: str, HEARER: str):
    """
    extract predicates with:
    -subject
    -object

    :param spacy.tokens.doc.Doc doc: spaCy object after processing text

    :rtype: list
    :return: list of tuples (predicate, subject, object)
    """
    print('get_subj_obj_triples_with_spacy')
    rels = {'nsubj', 'dobj', 'xcomp'}
    doc = nlp(utterance)

    triples = []

    predicates = {}

    subject_tokens = []
    subject_mentions = []
    object_tokens = []
    object_mentions = []

    speaker_mentions = []
    hearer_mentions = []
    speaker_tokens = []
    hearer_tokens = []

    for token in doc:
        if token.dep_ == "ROOT":
            #### this is a root, so we consider it a predicate
            predicates[token.i] = dict()
            predicates[token.i]['head'] = None
            predicates[token.i]['tail'] = None
    # print(predicates)
    for token in doc:
        if predicates.get(token.head.i):
            head_id = token.head.i
            if head_id not in predicates:
                predicates[head_id] = dict()
                predicates[head_id]['head'] = None
                predicates[head_id]['tail'] = None

            # print(token.pos_)
            if token.dep_ == 'nsubj':
                if (token.text.lower() == 'i'):
                    predicates[head_id]['head'] = SPEAKER
                    speaker_tokens.append(token)
                    speaker_mentions.append(token.text)
                elif (token.text.lower() == 'you'):
                    predicates[head_id]['head'] = HEARER
                    hearer_tokens.append(token)
                    hearer_mentions.append(token.text)
                elif token.pos_ == "PROPN" or token.pos_ == 'NOUN':
                    predicates[head_id]['head'] = token.lemma_
                    subject_tokens.append(token)
                    subject_mentions.append(token.text)
            if token.dep_ == 'dobj' or token.dep == 'xcomp':
                if (token.text.lower() == 'i'):
                    predicates[head_id]['tail'] = SPEAKER
                    speaker_tokens.append(token)
                    speaker_mentions.append(token.text)
                elif (token.text.lower() == 'you'):
                    predicates[head_id]['tail'] = HEARER
                    hearer_tokens.append(token)
                    hearer_mentions.append(token.text)
                elif token.pos_ == "PROPN" or token.pos_ == 'NOUN' or token.pos_ == 'ADJ':
                    predicates[head_id]['tail'] = token.lemma_
                    subject_tokens.append(token)
                    subject_mentions.append(token.text)
    for pred_token, pred_info in predicates.items():
        predicate = doc[pred_token].lemma_
        triple = predicateInfoToTriple(pred_info, predicate)
        if triple and not triple in triples:
            triples.append(triple)
    print('Triples subj - pred - obj', triples)
    return triples, zip(speaker_tokens, speaker_mentions), zip(hearer_tokens, hearer_mentions), zip(subject_tokens,
                                                                                                    subject_mentions), zip(
        object_tokens, object_mentions)


def get_subj_amod_triples_with_spacy(nlp, utterance: str, SPEAKER: str, HEARER: str):
    """
    extract predicates with:
    -subject
    -object

    :param spacy.tokens.doc.Doc doc: spaCy object after processing text

    :rtype: list
    :return: list of tuples (predicate, subject, object)
    """
    print('get_subj_amod_triples_with_spacy')
    rels = {'nsubj', 'nsubjpass', 'acomp'}

    doc = nlp(utterance)

    triples = []

    predicates = {}

    subject_tokens = []
    subject_mentions = []
    object_tokens = []
    object_mentions = []
    speaker_mentions = []
    hearer_mentions = []
    speaker_tokens = []
    hearer_tokens = []

    for token in doc:
        if token.dep_ == "ROOT":
            #### this is a root, so we consider it a predicate
            predicates[token.i] = dict()
            predicates[token.i]['head'] = None
            predicates[token.i]['tail'] = None

    for token in doc:
        if predicates.get(token.head.i):
            head_id = token.head.i
            if token.dep_ == 'nsubj' or token.dep_ == 'nsubjpass':
                if (token.text.lower() == 'i'):
                    predicates[head_id]['head'] = SPEAKER
                    speaker_tokens.append(token)
                    speaker_mentions.append(token.text)
                elif (token.text.lower() == 'you'):
                    predicates[head_id]['head'] = HEARER
                    hearer_tokens.append(token)
                    hearer_mentions.append(token.text)
                elif token.pos_ == "PROPN":
                    predicates[head_id]['head'] = token.lemma_
                    subject_tokens.append(token)
                    subject_mentions.append(token.text)
            if token.dep_ == 'acomp' or token.dep == 'auxpass':
                predicates[head_id]['tail'] = token.lemma_
    for pred_token, pred_info in predicates.items():
        predicate = doc[pred_token].lemma_
        triple = predicateInfoToTriple(pred_info, predicate)
        if triple and not triple in triples:
            triples.append(triple)
    print('Triples subj - aux - amod', triples)
    return triples, zip(speaker_tokens, speaker_mentions), zip(hearer_tokens, hearer_mentions), zip(subject_tokens,
                                                                                                    subject_mentions), zip(
        object_tokens, object_mentions)


def get_subj_attr_triples_with_spacy(nlp, utterance: str, SPEAKER: str, HEARER: str):
    """
    extract predicates with:
    -subject
    -object

    :param spacy.tokens.doc.Doc doc: spaCy object after processing text

    :rtype: list
    :return: list of tuples (predicate, subject, object)
    """
    print('get_subj_attr_triples_with_spacy')
    rels = {'nsubj', 'intj', 'appos' 'attr'}

    doc = nlp(utterance)

    triples = []

    predicates = {}

    subject_tokens = []
    subject_mentions = []
    object_tokens = []
    object_mentions = []

    speaker_mentions = []
    hearer_mentions = []
    speaker_tokens = []
    hearer_tokens = []

    for token in doc:
        # print(token.i, token.text, token.head, token.dep_)
        if token.dep_ == "ROOT":
            #### this is a root, so we consider it a predicate
            predicates[token.i] = dict()
            predicates[token.i]['head'] = None
            predicates[token.i]['tail'] = None
    for token in doc:
        if predicates.get(token.head.i):
            head_id = token.head.i

            if token.dep_ == 'nsubj' or token.dep_ == 'intj':
                if (token.text.lower() == 'i'):
                    predicates[head_id]['head'] = SPEAKER
                    speaker_tokens.append(token)
                    speaker_mentions.append(token.text)
                elif (token.text.lower() == 'you'):
                    predicates[head_id]['head'] = HEARER
                    hearer_tokens.append(token)
                    hearer_mentions.append(token.text)
                elif token.pos_ == "PROPN" or token.pos_ == 'NOUN':
                    predicates[head_id]['head'] = token.lemma_
                    subject_tokens.append(token)
                    subject_mentions.append(token.text)
            if token.dep_ == 'attr' or token.dep_ == 'appos':
                if (token.text.lower() == 'i'):
                    predicates[head_id]['tail'] = SPEAKER
                    speaker_tokens.append(token)
                    speaker_mentions.append(token.text)
                elif (token.text.lower() == 'you'):
                    predicates[head_id]['tail'] = HEARER
                    hearer_tokens.append(token)
                    hearer_mentions.append(token.text)
                elif token.pos_ == "PROPN" or token.pos_ == 'NOUN' or token.pos_ == 'ADJ':
                    predicates[head_id]['tail'] = token.lemma_
                    subject_tokens.append(token)
                    subject_mentions.append(token.text)

    for pred_token, pred_info in predicates.items():
        predicate = doc[pred_token].lemma_
        print(predicate, pred_info)
        triple = predicateInfoToTriple(pred_info, predicate)
        if triple and not triple in triples:
            triples.append(triple)

    print('Triples subj - pred - attr', triples)
    return triples, zip(speaker_tokens, speaker_mentions), zip(hearer_tokens, hearer_mentions), zip(subject_tokens,
                                                                                                    subject_mentions), zip(
        object_tokens, object_mentions)


def get_subj_prep_pobj_triples_with_spacy(nlp, utterance: str, SPEAKER: str, HEARER: str):
    """
    extract predicates with:
    -subject
    -object

    :param spacy.tokens.doc.Doc doc: spaCy object after processing text

    :rtype: list
    :return: list of tuples (predicate, subject, object)
    """
    print('get_subj_prep_pobj_triples_with_spacy')
    rels = {'nsubj', 'nsubjpass', 'prep', 'pobj'}

    doc = nlp(utterance)

    triples = []

    predicates = {}
    acomp = []

    subject_tokens = []
    subject_mentions = []
    object_tokens = []
    object_mentions = []

    speaker_mentions = []
    hearer_mentions = []
    speaker_tokens = []
    hearer_tokens = []

    for token in doc:
        if token.dep_ == "ROOT":
            #### this is a root, so we consider it a predicate
            predicates[token.i] = dict()
            predicates[token.i]['head'] = None
            predicates[token.i]['tail'] = None

    for token in doc:
        if predicates.get(token.head.i):
            head_id = token.head.i
            if token.dep_ == 'nsubj':
                if (token.text.lower() == 'i'):
                    predicates[head_id]['head'] = SPEAKER
                    speaker_tokens.append(token)
                    speaker_mentions.append(token.text)
                elif (token.text.lower() == 'you'):
                    predicates[head_id]['head'] = HEARER
                    hearer_tokens.append(token)
                    hearer_mentions.append(token.text)
                elif token.pos_ == "PROPN" or token.pos_ == 'NOUN':
                    predicates[head_id]['head'] = token.lemma_
                    subject_tokens.append(token)
                    subject_mentions.append(token.text)
            elif token.dep_ == 'prep':
                predicates[head_id]['prep'] = token.lemma_
                for token_dep in doc:
                    if token_dep.dep_ == 'pobj' and token_dep.head.i == token.i:
                        # print(token_dep.head.i, token.i)
                        #### We now need to get the token that has a "pobj" dependency to this prep
                        if (token_dep.text.lower() == 'i'):
                            predicates[head_id]['tail'] = SPEAKER
                            speaker_tokens.append(token_dep)
                            speaker_mentions.append(token_dep.text)
                        elif (token_dep.text.lower() == 'you'):
                            predicates[head_id]['tail'] = HEARER
                            hearer_tokens.append(token_dep)
                            hearer_mentions.append(token_dep.text)
                        elif token_dep.pos_ == "PROPN" or token_dep.pos_ == 'NOUN' or token_dep.pos_ == 'ADJ':
                            predicates[head_id]['tail'] = token_dep.lemma_
                            subject_tokens.append(token_dep)
                            subject_mentions.append(token_dep.text)
        for pred_token, pred_info in predicates.items():
            predicate = doc[pred_token].lemma_ + "-" + pred_info.get('prep', str(None))
            triple = predicateInfoToTriple(pred_info, predicate)
            if triple and not triple in triples:
                triples.append(triple)
    print('Triples subj - pred - prep-obj', triples)
    return triples, zip(speaker_tokens, speaker_mentions), zip(hearer_tokens, hearer_mentions), zip(subject_tokens,
                                                                                                    subject_mentions), zip(
        object_tokens, object_mentions)
