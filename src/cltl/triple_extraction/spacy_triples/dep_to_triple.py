import spacy

def predicateInfoToTriple (pred_info:dict, predicate: str):
    triple = None
    if pred_info.get('head') and pred_info.get('tail'):
        triple = {'predicate': {'label': predicate, 'type': []},
                  'subject': {'label': pred_info.get('head'), 'type': []},
                  'object': {'label': pred_info.get('tail'), 'type': []}
                  }

    return triple


def get_subj_obj_triples_with_spacy(nlp, utterance:str, SPEAKER: str, HEARER: str):
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
        if token.i==token.head.i:
            #### this is a root, so we consider it a predicate
            predicates[token.i] = dict()
            predicates[token.i]['head'] = None
            predicates[token.i]['tail'] = None
    #print(predicates)
    for token in doc:
        if token.dep_ in rels:
            if predicates.get(token.head.i):
                head_id = token.head.i
                if head_id not in predicates:
                    predicates[head_id] = dict()
                    predicates[head_id]['head']=None
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
    return triples, zip(speaker_tokens, speaker_mentions), zip(hearer_tokens, hearer_mentions), zip(subject_tokens, subject_mentions), zip(object_tokens, object_mentions)

def get_subj_amod_triples_with_spacy(nlp, utterance:str, SPEAKER: str, HEARER: str):

    """
    extract predicates with:
    -subject
    -object

    :param spacy.tokens.doc.Doc doc: spaCy object after processing text

    :rtype: list
    :return: list of tuples (predicate, subject, object)
    """
    print('get_subj_amod_triples_with_spacy')
    rels ={'nsubj', 'nsubjpass', 'acomp'}

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
        if token.i==token.head.i:
            #### this is a root, so we consider it a predicate
            predicates[token.i] = dict()
            predicates[token.i]['head'] = None
            predicates[token.i]['tail'] = None

    for token in doc:
        if token.dep_ in rels:
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
    return triples, zip(speaker_tokens, speaker_mentions), zip(hearer_tokens, hearer_mentions), zip(subject_tokens, subject_mentions), zip(object_tokens, object_mentions)


def get_subj_attr_triples_with_spacy(nlp, utterance:str, SPEAKER: str, HEARER: str):
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
        if token.i==token.head.i:
            #### this is a root, so we consider it a predicate
            predicates[token.i] = dict()
            predicates[token.i]['head'] = None
            predicates[token.i]['tail'] = None

    for token in doc:
        if token.dep_ in rels:
            if predicates.get(token.head.i):
                head_id = token.head.i
                if token.dep_ == 'nsubj' or token.dep == 'intj':
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
                if token.dep_ == 'attr' or token.dep == 'appos':
                    if (token.text.lower() == 'i'):
                        predicates[head_id]['tail'] = SPEAKER
                        speaker_tokens.append(token)
                        speaker_mentions.append(SPEAKER)
                    elif (token.text.lower() == 'you'):
                        predicates[head_id]['tail'] = HEARER
                        hearer_tokens.append(token)
                        hearer_mentions.append(HEARER)
                    elif token.pos_ == "PROPN" or token.pos_ == 'NOUN' or token.pos_ == 'ADJ':
                        predicates[head_id]['tail'] = token.lemma_
                        subject_tokens.append(token)
                        subject_mentions.append(token.lemma_)
    for pred_token, pred_info in predicates.items():
        predicate = doc[pred_token].lemma_
        triple = predicateInfoToTriple(pred_info, predicate)
        if triple and not triple in triples:
            triples.append(triple)

    print('Triples subj - pred - attr', triples)
    return triples, zip(speaker_tokens, speaker_mentions), zip(hearer_tokens, hearer_mentions), zip(subject_tokens, subject_mentions), zip(object_tokens, object_mentions)


def get_subj_prep_pobj_triples_with_spacy(nlp, utterance:str, SPEAKER: str, HEARER: str):
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
        if token.i==token.head.i:
            #### this is a root, so we consider it a predicate
            predicates[token.i] = dict()
            predicates[token.i]['head'] = None
            predicates[token.i]['tail'] = None

    for token in doc:
        if token.dep_ in rels:
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
    return triples, zip(speaker_tokens, speaker_mentions), zip(hearer_tokens, hearer_mentions), zip(subject_tokens, subject_mentions), zip(object_tokens, object_mentions)

