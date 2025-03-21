import json
import threading
import urllib.error
import urllib.parse
import urllib.request
from datetime import date

import nltk
from cltl.commons.discrete import UtteranceType
from cltl.commons.language_helpers import lexicon_lookup, lexicon
from nltk import pos_tag
from nltk import tree as ntree
from nltk.data import find

from . import wordnet_utils as wu

thread_local = threading.local()


def load_wnl():
    if not hasattr(thread_local, "wnl"):
        # Set the data path for NLTK and load the lemmatizer in each thread
        nltk.data.path.append(find('corpora/wordnet2022'))

        thread_local.wnl = nltk.WordNetLemmatizer()

    return thread_local.wnl


def trim_dash(triple):
    """
    :param triple: a set with three elements (subject, predicate, object)
    :return: clean triple with extra dashes removed
    """
    for el in triple:
        if triple[el]:
            if type(triple[el])==str:
                if triple[el].startswith('-'):
                    triple[el] = triple[el][1:]
                if triple[el].endswith('-'):
                    triple[el] = triple[el][:-1]
    return triple


def fix_pronouns(pronoun, speaker, human, agent):
    """
    :param pronoun: personal ronoun which is said in the sentence
    :param speaker: the original speaker get_pos_in_tree an utterance
    :return: disambiguated first or second person pronoun
    In the case of third person pronouns - guesses or asks questions
    * plural *
    """

    entry = lexicon_lookup(pronoun.lower(), lexicon)

    if entry and 'person' in entry:
        if entry['person'] == 'first':
                return speaker
        elif entry['person'] == 'second':
            if speaker == human:
                return agent
            elif speaker == agent:
                return human
        else:
            # print('disambiguate third person')
            return pronoun
    elif pronoun=='i':
        return speaker
    elif pronoun.lower()=='you':
        if speaker == human:
            return agent
        elif speaker == agent:
            return human
    else:
        return pronoun


def lemmatize(word, tag=''):
    """
    This function uses the WordNet lemmatizer
    :param word: word to be lemmatized
    :param tag: POS tag of word
    :return: word lemma
    """
    # Create and use the WordNetLemmatizer in each thread
    lem = ''
    if len(word.split()) > 1:
        for el in word.split():
            lem += load_wnl().lemmatize(el) + ' '
        return lem.strip()
    if tag != '':
        return load_wnl().lemmatize(word, tag)
    return load_wnl().lemmatize(word)


def get_triple_element_type(element, forest):
    """
    :param element: text of one element from the triple
    :param forest: parsed tree
    :return: dictionary with semantic types of the element or sub-elements
    """

    types = {}

    # Multiword element
    if '-' in element:
        text = element.replace(" ", "-")

        # Try to get type from DBpedia
        uris = get_uris(text.strip())
        if len(uris) > 1:
            # entities with more than 1 uri from DBpedia are NE and collocations
            return 'NE-col'

        # Try to get types from wordnet
        lexname = get_lexname_in_tree(text, forest)
        if lexname:
            # collocations which exist in WordNet
            return lexname + '-col'

        # if entity does not exist in DBP or WN it is considered composite. Get type per word
        for el in element.split('-'):
            types[el] = get_word_type(el, forest)

    # Single word
    else:
        types[element] = get_word_type(element, forest)

    return types


def get_triple_element_type_without_pos(element):
    """
    :param element: text of one element from the triple
    :return: dictionary with semantic types of the element or sub-elements
    """

    types = {}

    # Multiword element
    if '-' in element:
        text = element.replace(" ", "-")

        # Try to get type from DBpedia
        uris = get_uris(text.strip())
        if len(uris) > 1:
            # entities with more than 1 uri from DBpedia are NE and collocations
            return 'NE-col'

        # Try to get types from wordnet
        lexname = get_lexname_in_tree(text)
        if lexname:
            # collocations which exist in WordNet
            return lexname + '-col'

        # if entity does not exist in DBP or WN it is considered composite. Get type per word
        for el in element.split('-'):
            types[el] = get_word_type_without_forest(el)

    # Single word
    else:
        types[element] = get_word_type_without_forest(element)

    return types

def get_word_type(word, forest):
    """
    :param word: one word from triple element
    :param forest: parsed syntax tree
    :return: semantic type of word
    """

    if word == '':
        return ''

    lexname = get_lexname_in_tree(word, forest)
    if lexname is not None:
        return lexname

    # words which don't have a lexname are looked up in the lexicon
    entry = lexicon_lookup(word)
    if entry is not None:
        if 'proximity' in entry:
            return 'deictic:' + entry['proximity'] + ',' + entry['number']
        if 'person' in entry:
            return 'pronoun:' + entry['person']
        if 'root' in entry:
            return 'modal:' + str(entry['root'])
        if 'definite' in entry:
            return 'article:' + entry
        if 'integer' in entry:
            return 'numeral:' + entry['integer']

    # for words which are not in the lexicon nor have a lexname,
    # the sem.type is derived from the POS tag
    types = {'NN': 'agent', 'V': 'verb', 'IN': 'prep', 'TO': 'prep', 'MD': 'modal'}
    pos = get_pos_tag(forest, word)
    if pos in types:
        return types[pos]

def get_word_type_without_forest(word):
    """
    :param word: one word from triple element
    :return: semantic type of word
    """

    if word == '':
        return ''

    lexname = get_lexname_in_tree(word)
    if lexname is not None:
        return lexname

    # words which don't have a lexname are looked up in the lexicon
    entry = lexicon_lookup(word)
    if entry is not None:
        if 'proximity' in entry:
            return 'deictic:' + entry['proximity'] + ',' + entry['number']
        if 'person' in entry:
            return 'pronoun:' + entry['person']
        if 'root' in entry:
            return 'modal:' + str(entry['root'])
        if 'definite' in entry:
            return 'article:' + entry
        if 'integer' in entry:
            return 'numeral:' + entry['integer']
    return None



def get_lexname_in_tree(word, forest):
    """
    :param word: word for which we want a WordNe lexname
    :param forest: parsed forest of the sentence, to extract the POS tag
    :return: lexname of the word
    https://wordnet.princeton.edu/documentation/lexnames5wn
    """
    if word == '':
        return None

    # Get POS tag
    pos_label = get_pos_tag(forest[0], word)

    # Try to get types from wordnet
    synset = wu.get_synsets(word, pos_label)
    if synset:
        type = wu.get_lexname(synset[0])
        return type

def get_lexname_in_tree_without_forest(word):
    """
    :param word: word for which we want a WordNe lexname
    :param forest: parsed forest of the sentence, to extract the POS tag
    :return: lexname of the word
    https://wordnet.princeton.edu/documentation/lexnames5wn
    """
    if word == '':
        return None

    # Try to get types from wordnet
    synset = wu.get_synsets(word, 'N')
    if synset:
        type = wu.get_lexname(synset[0])
        return type

def get_pos_in_tree(tree, word):
    """
    This function extracts POS tag of a word from the parsed syntax tree
    :param tree: syntax tree gotten from initial CFG parsing
    :param word: word whose POS tag we want
    :return: POS tag of the word
    """
    label = ''
    for el in tree:
        for node in el:
            if type(node) == ntree.Tree:
                for subtree in node.subtrees():
                    for n in subtree:
                        if n == word:
                            label = str(subtree.label())
                            return label
    return label


def get_pos_tag(forest, word):
    """
    This function extract POS tags from either the tree or the word alone
    :param forest: syntax tree gotten from initial CFG parsing
    :param word: word whose POS tag we want
    :return: POS tag of the word
    """
    pos_label = get_pos_in_tree(forest, word)
    pos_label = pos_tag([word])[0][1] if pos_label == '' else pos_label

    return pos_label


def dbp_query(q, base_url, format="application/json"):
    """
    :param q: query for DBpedia
    :param base_url: URL to connect to DBpedia
    :param format: format for query, typically json
    :return: json with DBpedia responses
    """
    params = {
        "default-graph": "",
        "should-sponge": "soft",
        "query": q,
        "debug": "on",
        "timeout": "",
        "format": format,
        "save": "display",
        "fname": ""
    }

    querypart = urllib.parse.urlencode(params)
    response = urllib.request.urlopen(base_url, querypart).read()
    return json.loads(response)


def get_uris(string):
    """
    :param string: string which we are querying for
    :return: set of URIS from DBpedia for the queried string
    """
    query = """PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                SELECT ?pred WHERE {
                  ?pred rdfs:label """ + "'" + string + "'" + """@en .
                }
                ORDER BY ?pred"""

    try:
        results = dbp_query(query, "http://dbpedia.org/sparql")
        uris = []
        for x in results['results']['bindings']:
            uris.append(x['pred']['value'])
    except:
        uris = []

    return uris


def utterance_to_capsules(utterance):
    """
    Transform an Utterance into a list of capsules
    :param utterance:
    :return:
    """
    capsules = []

    for triple in utterance.triples:
        capsule = {"chat": utterance.chat.id,
                   "turn": utterance.turn,
                   "author": utterance.chat_speaker,
                   "utterance": utterance.transcript,
                   "utterance_type": triple['utterance_type'],
                   "position": "0-" + str(len(utterance.transcript)),
                   ###
                   "subject": triple['subject'],
                   "predicate": triple['predicate'],
                   "object": triple['object'],
                   "perspective": triple["perspective"],
                   ###
                   "context_id": None,
                   "date": utterance.datetime.isoformat(),
                   "place": "",
                   "place_id": None,
                   "country": "",
                   "region": "",
                   "city": "",
                   "objects": [],
                   "people": []
                   }

        capsules.append(capsule)

    return capsules


def element_to_json(v):
    if type(v) in [str, int, float] or v is None:
        pass
    elif isinstance(v, date):
        v = v.isoformat()
    elif isinstance(v, UtteranceType):
        v = v.name
    elif isinstance(v, list):
        v = [element_to_json(el) for el in v]
    elif isinstance(v, dict):
        v = {inner_k: element_to_json(inner_v) for inner_k, inner_v in v.items()}
    else:
        v = {inner_k: element_to_json(inner_v) for inner_k, inner_v in v.__dict__.items()}

    return v


def triple_to_json(triple):
    return {k: element_to_json(v) for k, v in triple.items()}


def deduplicate_triples(triples):
    # TODO make more efficient
    sorted_triples = []
    for triple in triples:
        sorted_triple = dict(sorted(triple.items()))
        sorted_triples.append(sorted_triple)

    json_triples = []
    for triple in sorted_triples:
        triple_as_json = json.dumps(triple_to_json(triple))
        json_triples.append(triple_as_json)

    unique_triples = []
    for triple in set(json_triples):
        unique_triples.append(json.loads(triple))

    return unique_triples


def add_deduplicated(triple, list_json_triples):
    """Adds a triple to a list, only if it is not there. Return list and bool indicating whether an addition was made"""
    addition = False

    sorted_triple = dict(sorted(triple.items()))
    triple_as_json = json.dumps(triple_to_json(triple))

    if triple_as_json in list_json_triples:
        pass
    else:
        list_json_triples.append(json.loads(triple_as_json))
        addition = True

    return list_json_triples, addition


def get_simple_triple(triple):
    simple_triple = {'subject': triple['subject']['label'].replace(" ", "-").replace('---', '-'),
                     'predicate': triple['predicate']['label'].replace(" ", "-").replace('---', '-'),
                     'object': triple['object']['label'].replace(" ", "-").replace('---', '-'),
                     'perspective': extract_perspective()}
    return simple_triple

def extract_perspective():
    """
    This function extracts perspective from statements
    :param predicate: statement predicate
    :param utterance_info: product of statement analysis thus far
    :return: perspective dictionary consisting of sentiment, certainty, and polarity value
    """
    certainty = 1  # Possible
    polarity = 1  # Positive
    sentiment = 0  # Underspecified
    emotion = 0  # Underspecified
    perspective = {'sentiment': float(sentiment), 'certainty': float(certainty), 'polarity': float(polarity),
                   'emotion': float(emotion)}
    return perspective

