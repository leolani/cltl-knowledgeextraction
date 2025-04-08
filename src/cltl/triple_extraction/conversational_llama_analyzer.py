import itertools
import logging
from typing import List
import json
from cltl.commons.discrete import UtteranceType, Polarity, Certainty
from cltl.triple_extraction.conversational_triples.utils import pronoun_to_speaker_name
from langchain_ollama import ChatOllama
from openai import OpenAI

from cltl.triple_extraction.prompts.prompts import STATEMENT, QUESTION, CONVERSATION_SHORT, CONVERSATION_LONG, tools
from cltl.triple_extraction.analyzer import Analyzer
from cltl.triple_extraction.api import Chat, DialogueAct, Utterance
# to use ollama pull the model from the terminal in the venv: ollama pull <model-name>
#LLAMA_MODEL = "llama3.2:1b"
LLAMA_MODEL = "llama3.2"
QWEN_MODEL = "qwen2.5"
logger = logging.getLogger(__name__)
#from ollama.keep_alive import KeepAlive

qwords_en = ["what", "when", "where", "who", "whom", "why", "how"]
whowords = ["who", "wie"]
qverbs_en = ["do", "does", "did", "have", "has", "is", "are", "were", "was", "tell", "give", "show", "provide", "list"]
qwords_nl = ["wat", "wie","wanneer", "waar", "waarom", "waardoor", "waarnaar", "waarin", "waarover", "hoe"]
qverbs_nl = ["kan", "kun", "wil", "ben", "is", "zijn", "waren", "moet", "ga", "zal", "gaan", "gingen"]
prepositions_en = ["in", "on", "into", "from", "at", "under", "for", "of", "to", "about"]
prepositions_nl = ["in", "op", "naar", "van", "bij", "onder", "voor", "naast", "te", "over"]

class LlamaAnalyzer(Analyzer):
    def __init__(self, model_name: str, temperature: float = 0.1,
                 s_instruct= STATEMENT.INSTRUCT, q_instruct = QUESTION.INSTRUCT, c_instruct = CONVERSATION_SHORT.INSTRUCT,
                 keep_alive=10, llama_server= "http://localhost", port= "9001"):
        """
        Parameters
        ----------
        model_path: str
            Path to the model
        dialogue_acts: List[DialogueAct]
            Dialogue acts for which triple extraction should be performed
        """
        super().__init__()

        self._q_instruct = q_instruct
        self._s_instruct = s_instruct
        self._c_instruct = c_instruct
        self._model = model_name
        url = llama_server+ ":"+port+"/v1"
        self._llama_client = OpenAI(base_url=url, api_key="not-needed")
        self._temperature = temperature
        self._keep_alive = keep_alive
        self._llm = ChatOllama(
            model=self._model,
            temperature=self._temperature,
            keep_alive = self._keep_alive,
            cache = False,
            # repeat_last_n = 0,
            # top_k = 5,
            # top_p = 0.5,
            format = 'json',
            tools = tools
            # other params ...
        )
        self._chat = None

    # def call_llama_server (self, prompt):
    #     completion = self._llama_client.chat.completions.create(
    #         # completion = client.chatCompletions.create(
    #         model="local-model",  # this field is currently unused
    #         messages=prompt,
    #         temperature=self._temperature,
    #
    #         keep_alive= self._keep_alive,
    #         #max_tokens=100,
    #         stream=True,
    #     )
    #
    #     content = ""
    #     for chunk in completion:
    #         if chunk.choices[0].delta.content is not None:
    #             content += chunk.choices[0].delta.content
    #     return content

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

    def analyze_last_utterance(self, chat):
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
        instruct = self._s_instruct
        if chat.last_utterance.dialogue_acts[0]==DialogueAct.QUESTION:
            instruct = self._q_instruct
        prompt = [instruct, input]
        print('PROMPT', prompt)
        attempt = 0
        max=3
        while not triples and attempt<max:
            attempt += 1
            response = self._llm.invoke(prompt)
            try:
                content = json.loads(response.content)
                #print('content', content)
                if "triples" in content:
                    triples.extend(content["triples"])
            except:
                logger.debug("ERROR parsing JSON",response.content)
        for triple_value in triples:
            triple = self._convert_triple(triple_value, chat.last_utterance.utterance_speaker, chat.speaker, chat.agent)
            if triple:
                chat.last_utterance.triples.append(triple)

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
        instruct = self._c_instruct
        if chat.last_utterance.dialogue_acts[0]==DialogueAct.QUESTION:
            instruct = self._q_instruct
        prompt = [instruct]

        conversation = self._chat_to_conversation(chat)
        prompt.extend(conversation)
        print('INPUT', prompt)
        attempt = 0
        max=3
        while not triples and attempt<max:
            attempt += 1
            response = self._llm.invoke(prompt)
            try:
                content = json.loads(response.content)
                print('content', content)
                if "triples" in content:
                    triples.extend(content["triples"])
            except:
                logger.debug("ERROR parsing JSON",response.content)
        for triple_value in triples:
            triple = self._convert_triple(triple_value, chat.last_utterance.utterance_speaker, chat.speaker, chat.agent)
            if triple:
                chat.last_utterance.triples.append(triple)

    #@TODO needs to be fixed as we are requesting different output format now
    def analyze_in_context_server(self, chat):
            """
            Analyzer factory function

            Find appropriate Analyzer for this utterance

            Parameters
            ----------
            utterance: Utterance
                utterance to be analyzed

            """

            triples = []
            conversation = self._chat_to_conversation(chat)
            input = {"role": "user", "content": conversation}
            prompt = [self._instruct, input]
            attempt = 0
            max = 5
            while not triples and attempt < max:
                attempt += 1
                response = self.call_llama_server(prompt)
                #response {"dialogue": [{"sender": "human", "text": "I have three white cats",
                # "triples": [ { "subject": "I", "predicate": "have", "object": "three-white-cats", "sentiment": 0, "polarity": 1, "certainty": 1}]}]}
                try:
                    content = json.loads(response)
                    if "triples" in content:
                        triples.extend(content["triples"])
                except:
                    logger.debug("ERROR parsing JSON", response)
            for triple_value in triples:
                triple = self._convert_triple(triple_value, chat.last_utterance.utterance_speaker, chat.speaker,
                                              chat.agent)
                if triple:
                    chat.last_utterance.triples.append(triple)

    def _convert_triple(self, triple_value, speaker, human, agent):
        #{"subject": "I", "predicate": "love_dogs", "object": "also", "sentiment": 0, "polarity": 0, "certainty": 1n}
        if len(triple_value) < 3:
            return None
        triple = None
        print('triple_value', triple_value)
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
            triple_value['subject'] = triple_value['subject'].replace("_", "-")
            triple_value['subject'] = triple_value['subject'].replace(" ", "-")
            triple_value['subject'] = triple_value['subject'].replace("my-", human+"-")
            triple_value['subject'] = triple_value['subject'].replace("your-", agent+"-")

            if triple_value['object'].startswith("_"):
                triple_value['object']=triple_value['object'][1:]
            if triple_value['object'].endswith("_"):
                triple_value['object']=triple_value['object'][:-1]
            self._fix_pp_objects(triple_value)
            triple_value['object'] = triple_value['object'].replace("_", "-")
            triple_value['object'] = triple_value['object'].replace(" ", "-")
            triple_value['object'] = triple_value['object'].replace("my-", human+"-")
            triple_value['object'] = triple_value['object'].replace("your-", agent+"-")

            triple_value['predicate'] = triple_value['predicate'].replace("_", "-")
            triple_value['predicate'] = triple_value['predicate'].replace(" ", "-")
            triple = {"subject": {"label": triple_value['subject'].lower(), "type": [], "uri": None},
                          "predicate": {"label": triple_value['predicate'].lower(), "type": [], "uri": None},
                          "object": {"label": triple_value['object'].lower(), "type": [], "uri": None}
                          }
            if 'polarity' in triple_value and 'certainty' in triple_value and 'sentiment' in triple_value:
                triple["perspective"] = {"polarity": triple_value["polarity"],"certainty": triple_value['certainty'], "sentiment": triple_value['sentiment']}

        return triple

    def _fix_pp_objects(self, triple):
        if "object" in triple and "predicate" in triple:
            for preposition in prepositions_en:
                if triple["object"].startswith(preposition+" ") or triple["object"].startswith(preposition+"-") or triple["object"].startswith(preposition+"_"):
                    triple["predicate"] += "-"+preposition
                    triple["object"] = triple["object"][len(preposition):].strip()


    def _chat_to_conversation(self, chat):
        conversation = []
        utterances_by_speaker = [(speaker, " ".join(utt.transcript for utt in utterances)) for speaker, utterances
                                 in itertools.groupby(chat.utterances, lambda utt: utt.utterance_speaker)]
        utterances_by_speaker = utterances_by_speaker[-3:]
        speakers = list(zip(*utterances_by_speaker))[0]
        turns = list(zip(*utterances_by_speaker))[1]

        print(utterances_by_speaker)
        #print(speakers)
        #print(turns)
        for element in utterances_by_speaker:
            utterance = None
            print('element[0]', element[0])
            if chat.agent == element[0]:
              #  utterance = {'role': 'assistant', 'content': f'''{element[0]} said {element[1]}'''}
                utterance = {'role': 'user','content': element[1],  'speaker': element[0]}
            else:
               # utterance = {'role': 'user', 'content': f'''{element[0]} said {element[1]}'''}
                utterance = {'role': 'user','content': element[1],  'speaker': element[0]}
            if utterance:
                conversation.append(utterance)
        print(conversation)
        return conversation

if __name__ == "__main__":
    '''
    test files with triples are formatted like so "test sentence : subject predicate object" 
    multi-word-expressions have dashes separating their elements, and are marked with apostrophes if they are a 
    collocation
    '''
    MODEL = LLAMA_MODEL
    MODEL = QWEN_MODEL
    analyzer = LlamaAnalyzer( model_name=MODEL,temperature=0.1, keep_alive=10)
    agent = "Leolani"
    human = "Lenka"
    utterances = [{"speaker": human, "utterance": "I love cats.", "dialogue_act": DialogueAct.STATEMENT},
                  {"speaker": agent, "utterance": "I have three white cats", "dialogue_act": DialogueAct.STATEMENT},
                  {"speaker": agent, "utterance": "Do you also love dogs?", "dialogue_act": DialogueAct.QUESTION},
                  {"speaker": human, "utterance": "No I do not.", "dialogue_act": DialogueAct.STATEMENT}]
    # utterances = [
    #     #{"speaker": human, "utterance": "my mother loves the beatles.", "dialogue_act": DialogueAct.STATEMENT},
    #               {"speaker": agent, "utterance": "I have three white cats", "dialogue_act": DialogueAct.STATEMENT},
    #              # {"speaker": agent, "utterance": "I come from the Netherlands", "dialogue_act": DialogueAct.STATEMENT},
    #               ]
    chat = Chat("Leolani", "Lenka")
    for utterance in utterances:
        chat.add_utterance(transcript=utterance["utterance"], utterance_speaker=utterance["speaker"],
                           dialogue_acts=[utterance["dialogue_act"]])
        if utterance['speaker']==human:
            analyzer.analyze_in_context(chat)
    for utterance in chat.utterances:
        print(utterance)
        print('Final triples', utterance.triples)
