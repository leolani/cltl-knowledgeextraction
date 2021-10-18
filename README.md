# cltl-knowledgeextraction

A knowledge extraction service (aka Leolani's Triple Extractor package). This service performs Natural Language
Understanding through Grammars natural language textual data and outputs structured data.

### Description

This package allows extracting structured information, in the form of SPO triples, from natural language textual data.
It features:

* Upon initialization, an Utterance is parsed with the CFG and analyzed with the help of the Analyzer class.
* If an Utterance is a statement, it also has a Perspective object which consists of a polarity, certainty, sentiment
  and emotion value.
* The Analyzer class consists of a hierarchy of classes, topmost class is the abstract general class Analyzer, which is
  separated into two abstract classes StatementAnalyzer and QuestionAnalyzer, which consist of the concrete classes
  GeneralStatementAnalyzer, WhQuestionAnalyzer and VerbQuestionAnalyzer. These three get the utterance constituents as
  input (as parsed with the CFG) and map them to triples.

#### Triple extraction

The triples consist of subject, predicate and object alongside with their semantic types. In case of a statement, the
triple is accompanied by a perspective. In the case of a question the triple is incomplete. Below are a few examples of
the triples which are the output of analyzers:

* `“My sister enjoys eating cakes” lenka-sister_enjoy_eating-cakes `

* ` “What does my sister enjoy?” lenka-sister_enjoy_? `

The elements of the triple are separated with underscore; while dash is used to separate elements of multiword
expressions. When a multiword expression is actually a collocation, the multiword expression is marked with apostrophes
during the analysis (e.g. ”mexico-city”)to ensure that subparts of collocations are not analyzed separately.

Basic rules that the analyzer follows are:

* predicates are lemmatized verbs, with possible prepositions connected to the verb
    - `“live-in”, “come-from”, etc`
* modal verbs are analyzed using the lexicon and their modality is stored as one of the perspective values
    - `“might-come”- {'polarity': 1, 'certainty': '0.5', 'sentiment': 0}`
* negation is removed after processing and stored within the perspective object as polarity
    - `I think selene doesn't like cheese = “selene_like_cheese” - {'polarity': -1, '
      certainty': '0.75', 'sentiment': ’0.75'}`
    - `(I think selene hates cheese = “selene_hate_cheese” - {'polarity': 1, 'certainty': '0.75', 'sentiment': '-1'}`
* properties end with “-is”(this way it is quite easy for NLG)
    - `My favorite color is green = lenka_favorite-color-is_green`
* words that refer to a person are grouped together in the subject unless the verb is just “be”, in this case they are
  processed like properties (“sister-is”)
    - `My best friend is Selene = lenka_best-friend-is_selene `
    - `My best friend’s name is Selene = lenka-best-friend_name-is_selene `
* adjectives, determiners and numbers are joined with the noun
    - `“a-dog”, “the-blue-shirt”, etc.`

#### Pipeline

Below is a short summary of NLP that happens during the utterance analysis:

1. Removing usual openers such as “excuse me” or “leolani, can you tell me”, etc.
1. Tokenization and replacing contractions with long variants of aux verbs
1. POS tagging (NLTK and Stanford + would be good to add an additional tagger to use when the two have a mismatch)
1. CFG parsing using the grammar which is manually designed
1. Analyzer class maps the output of CFG parsing to the subject-predicate-object triple, following the rules which are
   mentioned above
1. Lemmatization using NLTK
1. Modal verbs are analyzed using the lexicon and this is stored within Perspective
1. Checking whether some of the multi-word elements are actually collocations such as New York or ice-cream (these
   should be processed as one word)
1. Getting semantic types of each element of the triple, and its subparts, using the manually made lexicon, WordNet
   lexname, Stanford NER

#### Sample output

Here is a sample output for sentence `“I have three white cats”`:

```json
{
  "subject": {
    "text": "Lenka",
    "type": [
      "person"
    ]
  },
  "predicate": {
    "text": "have",
    "type": [
      "verb.possession"
    ]
  },
  "object": {
    "text": "three-white-cats",
    "type": [
      "adj.all",
      "noun.animal",
      'numeral:3'
    ]
  },
  "utterance type": "STATEMENT",
  "perspective": {
    "polarity": 1,
    "certainty": 1,
    "sentiment": 0
  }
}

```

## Getting started

### Prerequisites

This repository uses Python >= 3.7

Be sure to run in a virtual python environment (e.g. conda, venv, mkvirtualenv, etc.)

### Installation

1. In the root directory of this repo run

    ```bash
    pip install -e .
    python -c "import nltk; nltk.download('wordnet'); nltk.download('punkt')"
    ```

### Usage

For using this repository as a package different project and on a different virtual environment, you may

- install a published version from PyPI:

    ```bash
    pip install cltl.triple_extractor
    ```

- or, for the latest snapshot, run:

    ```bash
    pip install git+git://github.com/leolani/cltl-knowledgeextraction.git@main
    ```

Then you can import it in a python script as:

```python
    from cltl.triple_extraction.api import Chat, UtteranceHypothesis

    chat = Chat("Lenka")
    chat.add_utterance([UtteranceHypothesis("I have three white cats", 1.0)])
    chat.last_utterance.analyze()
```

### Examples

Please take a look at the example scripts provided to get an idea on how to run and use this package. Each example has a
comment at the top of the script describing the behaviour of the script.

For these example scripts, you need

1. To change your current directory to ./examples/

1. Run some examples (e.g. python test_with_triples.py)

