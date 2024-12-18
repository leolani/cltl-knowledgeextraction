import itertools
import logging
from typing import List
import json
from cltl.commons.discrete import UtteranceType, Polarity, Certainty
from cltl.triple_extraction.conversational_triples.utils import pronoun_to_speaker_name
from langchain_ollama import ChatOllama
from cltl.triple_extraction.analyzer import Analyzer
from cltl.triple_extraction.api import Chat, DialogueAct, Utterance
# to use ollama pull the model from the terminal in the venv: ollama pull <model-name>
#LLAMA_MODEL = "llama3.2:1b"
LLAMA_MODEL = "llama3.2"
logger = logging.getLogger(__name__)

qwords_en = ["what", "when", "where", "who", "why", "how"]
whowords = ["who", "wie"]
qverbs_en = ["do", "does", "did", "have", "has", "is", "are", "were", "was", "tell", "give", "show", "provide", "list"]
qwords_nl = ["wat", "wanneer", "waar", "waarom", "hoe"]
qverbs_nl = ["kan", "kun", "wil", "ben", "is", "zijn", "waren", "moet", "ga", "zal", "gaan", "gingen"]

#_INSTRUCT: {'role':'system', 'content':'You will receive input from an agent that is not well-formulated. Rephrase this input to simple English as if coming from you. If it contains names, then use these names in the paraphrase. Do not switch "you" and "I" when generating the paraphrase from the input. You in the input is the user and I in the input is you. Be concise and do NOT include or repeat the instructions in the paraphrase.'}

# _INSTRUCT = {'role':'system', 'content':'You will analyze a dialogue and break it down into triples consisting of a subject, predicate,and object. Each triple should capture the essence of interactions between speakers. \
#                                          Additionally, annotate each triple with:  \
# - Sentiment (-1 for negative, 0 for neutral, 1 for positive) \
# - Polarity (-1 for negation, 0 for neutral/questioning, 1 for affirmation) \
# - Certainty (a scale between 0 for uncertain and 1 for certain) \
# Ensure that predicates are semantically meaningful. Separate multi-word items with an underscore. \
# Save it as a JSON with this format: \
# {"dialogue": [{"sender": "human", "text": "I am from  find my order. It was supposed to arrive yesterday.", "triples": [ { "subject": "I", "predicate": "cannot_find", "object": "my_order", "sentiment": -1, "polarity": -1, "certainty": 1n},\
#             {"subject": "It", "predicate": "was_supposed_to_arrive", "object": "yesterday", "sentiment": -1, "polarity": 1, "certainty": 0.7 }]},\
# {"sender": "agent","text": "I will help you with that.", "triples": [ {"subject": "I", "predicate": "will_help", "object": "you_with_that", "sentiment": 1, "polarity": 1, "certainty": 1}]}]}\
#                                         Do not output any other text than the JSON'
#}

_INSTRUCT = {'role':'system', 'content':'You will analyze a dialogue and break it down into triples consisting of a subject, predicate,and object. \
Each triple should capture the essence of interactions between speakers. \
Replace the predicate by its lemma, for example "is" and "am" should become "be". Remove auxiliary verbs such as "be", "have", "can", "might" from predicates. \
If the object starts with a preposition, concatenate the preposition to the predicate separated by a hyphen, for example "be-from".\
Additionally, annotate each triple with:  \
- Sentiment (-1 for negative, 0 for neutral, 1 for positive) \
- Polarity (-1 for negation, 0 for neutral/questioning, 1 for affirmation) \
- Certainty (a scale between 0 for uncertain and 1 for certain) \
Ensure that predicates are semantically meaningful. Separate multi-word items with an underscore. \
Save it as a JSON with this format: \
{"dialogue": [{"sender": "human", "text": "I am from Amsterdam.", "triples": [ { "subject": "I", "predicate": "be_from", "object": "Amsterdam", "sentiment": 0, "polarity": 1, "certainty": 1}]},\
{"dialogue": [{"sender": "human", "text": "lana is reading a book.", "triples": [ { "subject": "lana", "predicate": "read", "object": "a-book", "sentiment": 0, "polarity": 1, "certainty": 1}]},\
{"dialogue": [{"sender": "human", "text": "You hate dogs.", "triples": [ { "subject": "You", "predicate": "hate", "object": "dogs", "sentiment": -1, "polarity": 1, "certainty": 0.7}]},\
{"dialogue": [{"sender": "human", "text": "Selene does not like cheese.", "triples": [ { "subject": "Selene", "predicate": "like", "object": "cheese", "sentiment": -1, "polarity": -1, "certainty": 0.5}]},\
{"sender": "human","text": " Who likes cats?", "triples": [ {"subject": "", "predicate": "like", "object": "cats", "sentiment": 1, "polarity": 1, "certainty": 0.1}]},\
{"sender": "human","text": " Wen did Selene come?", "triples": [ {"subject": "Selene", "predicate": "come", "object": "", "sentiment": 1, "polarity": 1, "certainty": 0.1}]},\
{"sender": "human","text": " Where can I go?", "triples": [ {"subject": "I", "predicate": "go", "object": "", "sentiment": 1, "polarity": 1, "certainty": 0.1}]},\
{"sender": "human","text": " Who likes cats?", "triples": [ {"subject": "", "predicate": "like", "object": "cats", "sentiment": 1, "polarity": 1, "certainty": 0.1}]},\
{"sender": "human","text": " Are cats pets?", "triples": [ {"subject": "cats", "predicate": "be", "object": "pets", "sentiment": 1, "polarity": 1, "certainty": 0.1}]}]}\
{"sender": "human","text": " Do you like cats?", "triples": [ {"subject": "you", "predicate": "like", "object": "cats", "sentiment": 1, "polarity": 1, "certainty": 0.1}]}]}\
                                        Do not output any other text than the JSON.'

}

#user_prompt = f"Analyze the following conversation with ID {conversation_id}: {conversation_text}"

class LlamaAnalyzer(Analyzer):
    def __init__(self, model_name: str, temperature: float = 0.1, instruct= _INSTRUCT):
        """
        Parameters
        ----------
        model_path: str
            Path to the model
        dialogue_acts: List[DialogueAct]
            Dialogue acts for which triple extraction should be performed
        """
        super().__init__()

        self._instruct = instruct
        self._model = model_name
        self._llm = ChatOllama(
            model=self._model,
            temperature=temperature,
            # other params ...
        )
        self._chat = None

    def analyze(self, utterance):
        """
        Analyzer factory function

        Determines the type of utterance, extracts the RDF triple and perspective attaching them to the last utterance

        Parameters
        ----------
        utterance: Utterance
            utterance to be analyzed

        """
        raise NotImplementedError("Analyzing a single utterance is deprecated, use analayze_in_context instead!")

    def analyze(self, utterance):
        """
        Analyzer factory function

        Determines the type of utterance, extracts the RDF triple and perspective attaching them to the last utterance

        Parameters
        ----------
        utterance: Utterance
            utterance to be analyzed

        """
        raise NotImplementedError("Analyzing a single utterance is deprecated, use analayze_in_context instead!")

    def analyze_in_context(self, chat):
        """
        Analyzer factory function

        Find appropriate Analyzer for this utterance

        Parameters
        ----------
        utterance: Utterance
            utterance to be analyzed

        """

        triples = []
        input = {"role":"user", "content":chat.last_utterance.transcript}
        prompt = [self._instruct, input]
        response = self._llm.invoke(prompt)
        try:
            content = json.loads(response.content)
            if "dialogue" in content:
                dialogue = content["dialogue"]
                for field in dialogue:
                    if "triples" in field:
                       # print(field["triples"])
                        triples.extend(field["triples"])
        except:
            logger.debug("ERROR parsing JSON",response.content)
        for triple_value in triples:
            triple = self._convert_triple(triple_value, chat.last_utterance.utterance_speaker, chat.speaker, chat.agent)
            if triple:
                chat.last_utterance.triples.append(triple)



    def _convert_triple(self, triple_value, speaker, human, agent):
        #{"subject": "I", "predicate": "love_dogs", "object": "also", "sentiment": 0, "polarity": 0, "certainty": 1n}
        if len(triple_value) < 3:
            return None
        triple = None

        if 'subject' in triple_value and 'predicate' in triple_value and 'object' in triple_value and\
            not triple_value['subject']==None and not triple_value['predicate'] ==None and not triple_value['object']==None:
           # not triple_value['subject']=='' and not triple_value['predicate'] =='' and not triple_value['object']=='' and\
            ### Fix pronouns to names
            triple_value['subject'] = pronoun_to_speaker_name(triple_value['subject'], speaker, human, agent)
            triple_value['object'] = pronoun_to_speaker_name(triple_value['object'], speaker, human, agent)
            if triple_value['subject'].startswith("_"):
                triple_value['subject']=triple_value['subject'][1:]
            if triple_value['subject'].endswith("_"):
                triple_value['subject']=triple_value['subject'][:-1]
            if triple_value['object'].startswith("_"):
                triple_value['object']=triple_value['object'][1:]
            if triple_value['object'].endswith("_"):
                triple_value['object']=triple_value['object'][:-1]
            triple = {"subject": {"label": triple_value['subject'].lower(), "type": [], "uri": None},
                          "predicate": {"label": triple_value['predicate'].lower(), "type": [], "uri": None},
                          "object": {"label": triple_value['object'].lower(), "type": [], "uri": None}
                          }
            triple["perspective"] = {"polarity": triple_value["polarity"],"certainty": triple_value['certainty'], "sentiment": triple_value['sentiment']}
        return triple

    def _chat_to_conversation(self, chat):
        utterances_by_speaker = [(speaker, " ".join(utt.transcript for utt in utterances)) for speaker, utterances
                                 in itertools.groupby(chat.utterances, lambda utt: utt.utterance_speaker)]
        utterances_by_speaker = utterances_by_speaker[-3:]
        speakers = list(zip(*utterances_by_speaker))[0]
        turns = list(zip(*utterances_by_speaker))[1]
        conversation = ("<eos>" * min(2, (3 - len(utterances_by_speaker)))) + "<eos>".join(turns)

        ##### This should be based on the chat object and not some obscure order
        # speaker1 = speakers[-1] if speakers else None
        # if len(speakers) > 1:
        #     speaker2 = speakers[-2]
        # else:
        #     speaker2 = chat.agent if speaker1 == chat.speaker else chat.speaker

        return speakers, conversation, chat.speaker, chat.agent

if __name__ == "__main__":
    '''
    test files with triples are formatted like so "test sentence : subject predicate object" 
    multi-word-expressions have dashes separating their elements, and are marked with apostrophes if they are a 
    collocation
    '''

    analyzer = LlamaAnalyzer(
        model_name=LLAMA_MODEL,temperature=0.1)
    agent = "Leolani"
    human = "Lenka"
    utterances = [{"speaker": human, "utterance": "I love cats.", "dialogue_act": DialogueAct.STATEMENT},
                  {"speaker": agent, "utterance": "Do you also love dogs?", "dialogue_act": DialogueAct.QUESTION},
                  {"speaker": human, "utterance": "No I do not.", "dialogue_act": DialogueAct.STATEMENT}]
    chat = Chat("Leolani", "Lenka")
    for utterance in utterances:
        chat.add_utterance(transcript=utterance["utterance"], utterance_speaker=utterance["speaker"],
                           dialogue_acts=utterance["dialogue_act"])
        analyzer.analyze_in_context(chat)
    for utterance in chat.utterances:
        print(utterance)
        print('Final triples', utterance.triples)
