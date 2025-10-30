import itertools
import logging
from typing import List
import json
from cltl.commons.discrete import UtteranceType, Polarity, Certainty
from cltl.triple_extraction.conversational_triples.utils import pronoun_to_speaker_name
import cltl.triple_extraction.utils.standard_question_to_triple as standard_question
from langchain_ollama import ChatOllama
from ollama import Client
from openai import OpenAI
from cltl.triple_extraction.prompts.prompts import MODEL_RESPONSE, STATEMENT, QUESTION, CONVERSATION_SHORT, CONVERSATION_LONG, tools
from cltl.triple_extraction.analyzer import Analyzer
from cltl.triple_extraction.api import Chat, DialogueAct, Utterance

# to use ollama pull the model from the terminal in the venv: ollama pull <model-name>
#LLAMA_MODEL = "llama3.2:1b"
LLAMA_MODEL = "llama3.2"
QWEN_MODEL = "qwen2.5"
logger = logging.getLogger(__name__)

qwords_en = ["what", "when", "where", "who", "whom", "why", "how"]
whowords = ["who", "wie"]
qverbs_en = ["do", "does", "did", "have", "has", "is", "are", "were", "was", "tell", "can", "give", "show", "provide", "list"]
qwords_nl = ["wat", "wie","wanneer", "waar", "waarom", "waardoor", "waarnaar", "waarin", "waarover", "hoe"]
qverbs_nl = ["kan", "kun", "wil", "ben", "is", "zijn", "waren", "moet", "ga", "vertel", "weet", "ken", "zal", "gaan", "gingen"]
prepositions_en = ["in", "on", "into", "from", "at", "under", "for", "of", "to", "about"]
prepositions_nl = ["in", "op", "naar", "van", "bij", "onder", "voor", "naast", "te", "over"]

class LLMAnalyzer(Analyzer):
    def __init__(self, model_name: str, model_server="cloud", model_url="https://ollama.com", model_port="9001", model_key = "",
                 temperature: float = 0.1, dialogue_acts: List[DialogueAct] = None,
                 s_instruct= STATEMENT.INSTRUCT, q_instruct = QUESTION.INSTRUCT, c_instruct = CONVERSATION_LONG.INSTRUCT,
                 keep_alive=10,  lang="en", context_length = 3):
        """
        Parameters
        ----------
        model_path: str
            Path to the model
        dialogue_acts: List[DialogueAct]
            Dialogue acts for which triple extraction should be performed
        """
        super().__init__()
        self._language = lang
        self._q_instruct = q_instruct
        self._s_instruct = s_instruct
        self._c_instruct = c_instruct
        self._model = model_name
        self._temperature = temperature
        self._keep_alive = keep_alive
        self._context_length = context_length
        self._SERVER = model_server
        if self._SERVER=="server":
            self._client = OpenAI(base_url=model_url, api_key="not-needed")
        elif self._SERVER=="local":
            self._client = ChatOllama(
                model=self._model,
                temperature=self._temperature,
                base_url=model_url
                # other params ...
            )
        elif self._SERVER=="cloud":
            self._client = Client(
                host=model_url,
                headers={'Authorization': 'Bearer ' + model_key})
        else:
            raise ValueError("Unknown server type")
        logger.debug("Initializing LLM triple extractor: %s, %s, %s", model_server, model_url, model_name)
        self._chat = None
        self._dialogue_acts = set(dialogue_acts) if dialogue_acts else None

    def is_question(self, transcript):
        words = transcript.split()
        if words[0].lower() in qwords_en + qwords_nl + qverbs_en + qverbs_nl + whowords:
            return True
        if words[-1] == "?":
            return True
        return False
        
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

    def call_llm(self, prompt):
        response = ''
        if self._SERVER=="cloud":
            for part in self._client.chat(model=self._model, messages=prompt, stream=True):
                response += part['message']['content']
        elif self._SERVER=="local":
            response = self._client.invoke(prompt)
        elif self._SERVER=="server":
            response = self._client.chat.completions.create(model=self._model, messages=prompt)
        else:
            raise ValueError("Unknown server type")
        logger.debug('LLM response: %s', response)
        return response

    def analyze_in_context(self, chat):
        """
        Analyzer factory function

        Find appropriate Analyzer for this utterance

        Parameters
        ----------
        utterance: Utterance
            utterance to be analyzed

        """
        logger.debug('Analyze in context the last utterance: %s', chat.last_utterance.transcript)
        if self.is_question(chat.last_utterance.transcript):
            chat.last_utterance._dialogue_acts = [UtteranceType.QUESTION]
            logger.debug("Asking a question: %s, %s", chat.last_utterance.transcript, chat.last_utterance._dialogue_acts)
            self.analyze_question_in_context(chat)
        else:
            chat.last_utterance._dialogue_acts = [UtteranceType.STATEMENT]
            logger.debug("Making a statement: %s, %s", chat.last_utterance.transcript, chat.last_utterance._dialogue_acts)
            self.analyze_statement_in_context(chat)
        content = None
        if not chat.last_utterance.triples:
            content = self.get_model_response(chat)
        return content

    def get_model_response(self, chat):
        instruct = MODEL_RESPONSE.INSTRUCT
        prompt = [instruct]
        conversation = self._chat_to_conversation(chat=chat, context_length=self._context_length)
        prompt.extend(conversation)
        response = self.call_llm(prompt=prompt)
        return response

    def analyze_statement_in_context(self, chat):
        #Already done
        self._chat = chat
        self._utterance = chat.last_utterance
        triples = []
        if chat.last_utterance.utterance_speaker == chat.speaker:

            ## Already done
            self._chat = chat
            self._utterance = chat.last_utterance

            ### For conversational behaviour use next prompt instead of s_instruct
            # instruct = self._c_instruct

            instruct = self._s_instruct
            prompt = [instruct]
            conversation = self._chat_to_conversation(chat=chat, context_length=self._context_length)
            prompt.extend(conversation)
            response = self.call_llm(prompt=prompt)
            if response:
                try:
                    content = json.loads(response)
                    if "triples" in content:
                        triples.extend(content["triples"])
                except:
                    logger.debug("ERROR parsing JSON %s", response)
            for triple_value in triples:
                if not self._check_triple(triple_value):
                    triple = self._convert_triple(UtteranceType.STATEMENT, triple_value, chat.last_utterance.utterance_speaker, chat.speaker, chat.agent)
                else:
                    triple = triple_value
                if triple:
                    logger.debug("LLM Analyzer: extracted triple as STATEMENT: %s", triple)
                    chat.last_utterance.triples.append(triple)
        else:
            logger.debug('LLM Analyzer: This is not from the human speaker %s but from %s', chat.speaker,
                         chat.last_utterance.utterance_speaker)
        if not triples:
            logger.warning("LLM Analyzer: couldn't extract STATEMENT triples")

    def analyze_question_in_context(self, chat):
        """
        Analyzer factory function

        Find appropriate Analyzer for this utterance

        Parameters
        ----------
        utterance: Utterance
            utterance to be analyzed

        """
        ## Already done
        self._chat = chat
        self._utterance = chat.last_utterance

        triples = []
        if chat.last_utterance.utterance_speaker == chat.speaker:
            ## Already done
            self._chat = chat
            self._utterance = chat.last_utterance
            triple_values = []
            triple_values = standard_question.ask_for_all(chat.last_utterance, chat.speaker, chat.agent)
            if not triple_values:
                triple_values = standard_question.standard_questions(chat.last_utterance, chat.speaker, chat.agent)
            if not triple_values:
                instruct = self._q_instruct
                prompt = [instruct]
                #### We only consider the last utterance to extract a question!!!
                conversation = self._chat_to_conversation(chat=chat, context_length=1)
                prompt.extend(conversation)
                response = self.call_llm(prompt=prompt)
                if response:
                    try:
                        content = json.loads(response)
                        if "triples" in content:
                            triple_values.extend(content["triples"])
                    except:
                        logger.debug("ERROR parsing JSON %s", response)
            for triple_value in triple_values:
                if not self._check_triple(triple_value):
                    triple = self._convert_triple(UtteranceType.QUESTION, triple_value, chat.last_utterance.utterance_speaker,
                                                  chat.speaker, chat.agent)
                else:
                    triple = triple_value
                logger.debug("LLM Analyzer: extracted triple as a QUESTION: %s", triple)
                chat.last_utterance.triples.append(triple)
        else:
            logger.warning(f'LLM Analyzer: This is not from the human speaker {chat.speaker} but from {chat.last_utterance.utterance_speaker}')

        if not triples:
            logger.warning("LLM Analyzer: couldn't extract triples")

    def _check_triple(self, triple):
        #{'subject': {'label': 'jan', 'type': [], 'uri': None}, 'predicate': {'label': '', 'type': [], 'uri': None}, 'object': {'label': '', 'type': [], 'uri': None}, 'perspective': {'sentiment': 0.0, 'certainty': 1.0, 'polarity': 1.0, 'emotion': 0.0}}
        if 'subject' in triple and 'predicate' in triple and 'object' in triple:
            if 'label' in triple['subject'] and 'label' in triple['predicate'] and 'label' in triple['object']:
                return True
        return False

    def _convert_triple(self, utterance_type, triple_value, speaker, human, agent):
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
                          "predicate": {"label": triple_value['predicate'].lower(), "type": [], "uri": "n2mu:"+triple_value['predicate'].lower()},
                          "object": {"label": triple_value['object'].lower(), "type": [], "uri": None}
                          }
            if 'polarity' in triple_value and 'certainty' in triple_value and 'sentiment' in triple_value:
                triple["perspective"] = {"polarity": float(triple_value["polarity"]),"certainty": float(triple_value['certainty']), "sentiment": float(triple_value['sentiment'])}
            elif 'perspective' in triple_value:
                triple["perspective"] = {"polarity": float(triple_value["perspective"]["polarity"]),"certainty": float(triple_value["perspective"]['certainty']), "sentiment": float(triple_value["perspective"]['sentiment'])}
            triple["utterance_type"] = utterance_type
        return triple

    def _fix_pp_objects(self, triple):
        if "object" in triple and "predicate" in triple:
            for preposition in prepositions_en:
                if triple["object"].startswith(preposition+" ") or triple["object"].startswith(preposition+"-") or triple["object"].startswith(preposition+"_"):
                    triple["predicate"] += "-"+preposition
                    triple["object"] = triple["object"][len(preposition):].strip()

    def _chat_to_conversation(self, chat, context_length=3):
        conversation = []
        for utt in chat.utterances:
            utterance = {'role': 'user', 'content': utt.transcript, 'speaker':utt.utterance_speaker}
            conversation.append(utterance)
        logger.debug("Conversation before trimming: %s", conversation)
        if len(conversation)>=context_length:
            conversation = conversation[-context_length:]
        logger.debug("Conversation after trimming to the context length of %s: %s", context_length, conversation)
        return conversation

    @property
    def utterance(self) -> Utterance:
        return self._chat.last_utterance
    
if __name__ == "__main__":
    '''
    test files with triples are formatted like so "test sentence : subject predicate object" 
    multi-word-expressions have dashes separating their elements, and are marked with apostrophes if they are a 
    collocation
    '''
    MODEL = LLAMA_MODEL
    MODEL = QWEN_MODEL
    MODEL = "gpt-oss:120b"
    url = model_url="https://ollama.com"
    server = "cloud"
    ollama_cloud_key = ''
    analyzer = LLMAnalyzer(model_name=MODEL, model_server = server, model_url=url, model_key = ollama_cloud_key, temperature=0.1, keep_alive=10)
    agent = "Leolani"
    human = "Lenka"
    utterances = [{"speaker": human, "utterance": "I love cats.", "dialogue_act": DialogueAct.STATEMENT},
#                  {"speaker": agent, "utterance": "I have three white cats", "dialogue_act": DialogueAct.STATEMENT},
                  {"speaker": agent, "utterance": "Do you also love dogs?", "dialogue_act": DialogueAct.QUESTION},
                  {"speaker": human, "utterance": "What do I like?", "dialogue_act": DialogueAct.QUESTION},
                  {"speaker": human, "utterance": "What do I have?", "dialogue_act": DialogueAct.QUESTION},
                  {"speaker": human, "utterance": "Who likes cats?", "dialogue_act": DialogueAct.QUESTION},
                  {"speaker": human, "utterance": "What do you know about me?", "dialogue_act": DialogueAct.QUESTION},
                  {"speaker": human, "utterance": "Tell me all about me?", "dialogue_act": DialogueAct.QUESTION},
           #       {"speaker": human, "utterance": "No I do not.", "dialogue_act": DialogueAct.STATEMENT}
                ]
    chat = Chat("Leolani", "Lenka")
    for utterance in utterances:
        chat.add_utterance(transcript=utterance["utterance"], utterance_speaker=utterance["speaker"],
                           dialogue_acts=[utterance["dialogue_act"]])
        if utterance['speaker']==human:
            analyzer.analyze_in_context(chat)
    for utterance in chat.utterances:
        print(utterance)
        print('Final triples', utterance.triples)
