# cltl-knowledgeextraction

A knowledge extraction service (aka Leolani's Triple Extractor package). This service is designed to extract knowledge from conversation as structured data in the form of so-called triples of the form: subject, predicate object. E.g.:

```
Input: For a couple of years I lived in Amsterdam
Triple: (SPEAKER, live-in, Amsterdam)
````

There are several types of analyzers:

* ContextFreeGrammar (CFG, English only): a rule-based triple extractor that uses a context-free grammar, a lexicon and Part-of-Speech taggers to detect triples in conversational status. It takes single utterances as input.
* ConversationalAnalyzer: (English only and Multilingual): BERT models (ALBERT for English and mBERT for other languages) finetuned for IOB style triple extraction. It takes sequences of three utterances: "speaker turn -agent turn -speaker turn" as a context to detect the triples.
* Stanford OIE (English): trained on Wikipedia data
* SpacyDependency (Multilingual): patterns of spacy dependency relations are converted to triple.

The extractors do not require a predefined schema to detect triples but are limited in terms of the patterns they can detect.

## Table of contents

* [Description](#description)
  + [Triple extraction implementations](#triple-extraction-implementations)
    - [CFGAnalyzer](#cfganalyzer)
    - [ConversationalAnalyzer](#conversationalanalyzer)
      * [Models](#models)
    - [SpacyAnalyzer](#spacyanalyzer)
    - [OIEAnalyzer](#oieanalyzer)
  + [Question extraction implementations](#question-extraction-implementations)
    - [CFGQuestionAnalyzer](#cfgquestionanalyzer)
    - [ConversationalQuestionAnalyzer](#conversationalquestionanalyzer)
    - [StanzaQuestionAnalyzer](#stanzaquestionanalyzer)
  + [Sample output](#sample-output)
* [Getting started](#getting-started)
  + [Prerequisites](#prerequisites)
  + [Installation](#installation)
  + [Usage](#usage)
* [Examples](#examples)
* [Contributing](#contributing)
* [License](#license)
* [Authors](#authors)

## Description

This package extracts structured information, in the form of SPO triples, from natural language text:

* An Utterance is analyzed with the help of the Analyzer class. It extracts structured data in the form of a list of
  triples, where each triple has a subject, predicate and object.
* If an Utterance is a statement, it also has a Perspective object which consists of a polarity, certainty, sentiment
  and emotion value.
* The Analyzer class is the API for triple/question extractors. 

### Triple extraction implementations

The triples consist of subject, predicate and object alongside with their semantic types. Below is an example of the triples which is the output of one of the analyzers:

* `“My sister enjoys eating cakes” lenka-sister_enjoy_eating-cakes `

The elements of the triple are separated with underscore; while dash is used to separate elements of multiword
expressions. When a multiword expression is actually a collocation, the multiword expression is marked with apostrophes
during the analysis (e.g. ”mexico-city”) to ensure that subparts of collocations are not analyzed separately.
implementations

#### CFGAnalyzer

Basic rules that the CFGAnalyzer follows are:

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

Below is a short summary of NLP that happens during the CFG utterance analysis:

1. Tokenization and replacing contractions with long variants of aux verbs
1. POS tagging (NLTK and Stanford + would be good to add an additional tagger to use when the two have a mismatch)
1. CFG parsing using the grammar which is manually designed
1. Analyzer class maps the output of CFG parsing to the subject-predicate-object triple, following the rules which are
   mentioned above
1. Lemmatization using NLTK
1. Modal verbs are analyzed using the lexicon and this is stored within Perspective
1. Checking whether the multi-word elements are actually collocations such as New York or ice-cream (these should be
   processed as one word)
1. Getting semantic types of each element of the triple, and its subparts, using the manually made lexicon, WordNet
   lexname, Stanford NER

#### ConversationalAnalyzer

Extract triples taking the conversational context into account. It takes the consequetive turns from two speakers as input to detect triples:

```
Speaker1: I watched a lot of movies
Speaker 2: What movies do you like?
Speaker 1: Science fiction movies
```
```
Triple: Speaker 1, likes, science fiction movies
```

This extractor is more tuned to way in which people exchange knowledge in conversation. The training data is created from TopicalChat and DailyDialog data that were annotated with IOB tags for subject, predicate and object tokens as well as for negation and uncertainty. 

The finetuned models can be downloaded from ResearchDrive and need to be installed locally.

##### Models

* finetuned ALBERT model, English only: downloaded
from [ResearchDrive](https://vu.data.surfsara.nl/index.php/s/WpL1vFChlQpkbqW).
* finetuned multilingual mBERT, all mBERT languages: downloaded from: [ResearchDrive](https://vu.data.surfsara.nl/index.php/s/xL9fPrqIq8bs6NH).

The downloaded files must be placed in a folder `resources/conversational_triples/`

#### SpacyAnalyzer

Extract triples based on dependancy parsing, according
to [spacy's implementation](https://spacy.io/api/dependencyparser). This does not extract perspective values.

#### OIEAnalyzer

Extract triples based on the Open Information Extraction framework, according
to [Stanford's implementation](https://nlp.stanford.edu/software/openie.html). This does not extract perspective values.

### Question extraction implementations

The triples consist of subject, predicate and object alongside with their semantic types. In the case of a question the
triple is incomplete. Below is an example of the triples which are the output of analyzers:

* ` “What does my sister enjoy?” lenka-sister_enjoy_? `

#### CFGQuestionAnalyzer

This follows the same rules and processes as the [CFGAnalyzer](#cfganalyzer)

#### ConversationalQuestionAnalyzer

Similar to the [ConversationalAnalyzer](#conversationalanalyzer)

#### StanzaQuestionAnalyzer

Extract questions based on constituency parsing, according
to [Stanza's implementation](https://stanfordnlp.github.io/stanza/constituency.html)

### Sample output

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
      "noun.animal"
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
    python -c "import nltk; nltk.download('wordnet'); nltk.download('punkt'); nltk.download('averaged_perceptron_tagger')"
    python -m spacy download en_core_web_sm 
    ```

2. In case you want to use this package in the EventBus infrastructure, then install using:
    ```bash
    pip install -e .[service]
    python -c "import nltk; nltk.download('wordnet'); nltk.download('punkt'); nltk.download('averaged_perceptron_tagger')"
    python -m spacy download en_core_web_sm 
    ```

3. In case you want to run the OpenIE function from StanfordCoreNLP, you need to download "stanford-corenlp-4.1.0" and
   unpack it in the folder
   ~/.stanfordnlp_resources.

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
from cltl.triple_extraction.api import Chat
from cltl.triple_extraction.cfg_analyzer import CFGAnalyzer
from cltl.triple_extraction.utils.helper_functions import utterance_to_capsules

chat = Chat("Leolani", "Lenka")
analyzer = CFGAnalyzer()

chat.add_utterance("I have three white cats")
analyzer.analyze_in_context(chat)
capsules = utterance_to_capsules(chat.last_utterance)
```

## Examples

Please take a look at the example scripts provided to get an idea on how to run and use this package. Each example has a
comment at the top of the script describing the behaviour of the script.

For these example scripts, you need

1. To change your current directory to ./examples/

1. Run some examples (e.g. python test_with_triples.py)

## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any
contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License.
See [`LICENSE`](https://github.com/leolani/cltl-knowledgeextraction/blob/main/LICENCE) for more information.

## Authors

* [Selene Báez Santamaría](https://selbaez.github.io/)
* [Thomas Baier](https://www.linkedin.com/in/thomas-baier-05519030/)
* [Piek Vossen](https://github.com/piekvossen)
