import itertools
import logging
from typing import List
import json
from cltl.commons.discrete import UtteranceType, Polarity, Certainty
from cltl.triple_extraction.conversational_triples.utils import pronoun_to_speaker_name
from langchain_ollama import ChatOllama
from openai import OpenAI

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

# _INSTRUCT_STATEMENT = {'role':'system', 'content': '''You will receive a statement from a user in a conversation and you need to break it down into triples consisting of a subject, predicate,and object.
# Each triple should capture the essence of statement by the speaker.
# Replace the predicate by its lemma, for example "is" and "am" should become "be".
# Remove auxiliary verbs such as "be", "have", "can", "might", "must", "will", "shall", "should" from predicates.
# If the object starts with a preposition, concatenate the preposition to the predicate separated by a hyphen, for example "be-from" and not "be_from".
# If the predicate is followed by an infinite verb-phrase such as "like to swim", the object should start with "to-" as in "to-swim".
# If the predicate is an cognitive verb such as "think", "believe" or "know" or a speech-act such "say" or "tell",
# then extract the triple from the complement phrase of the predicate and convert the predicate to a perspective value for certainty and polarity.
# Combine multi-word subjects, predicates and objects with an hyphens, for example 'my-sister", "three-white-cats".
# Additionally, annotate each triple with:
# - Sentiment (-1 for negative, 0 for neutral, 1 for positive)
# - Polarity (-1 for negation, 0 for neutral/questioning, 1 for affirmation)
# - Certainty (a scale between 0 for uncertain and 1 for certain)
# Ensure that predicates are semantically meaningful.
# Save it as a JSON with this format:
# {"dialogue": [{"sender": "user", "text": "I am from Amsterdam.", "triples": [ { "subject": "I", "predicate": "be-from", "object": "Amsterdam", "sentiment": 0, "polarity": 1, "certainty": 1}]},
# {"dialogue": [{"sender": "user", "text": "lana is reading a book.", "triples": [ { "subject": "lana", "predicate": "read", "object": "book", "sentiment": 0, "polarity": 1, "certainty": 1}]},
# {"dialogue": [{"sender": "user", "text": "You hate dogs.", "triples": [ { "subject": "You", "predicate": "hate", "object": "dogs", "sentiment": -1, "polarity": 1, "certainty": 0.7}]},
# {"dialogue": [{"sender": "user", "text": "Selene does not like cheese.", "triples": [ { "subject": "Selene", "predicate": "like", "object": "cheese", "sentiment": -1, "polarity": -1, "certainty": 0.5}]},
# {"dialogue": [{"sender": "user","text": " I think that you like cats", "triples": [ {"subject": "you", "predicate": "like", "object": "cats", "sentiment": 1, "polarity": 1, "certainty": 0.1}]}]}
# {"dialogue": [{"sender": "user","text": " John said you like cats", "triples": [ {"subject": "you", "predicate": "like", "object": "cats", "sentiment": 1, "polarity": 1, "certainty": 0.1}]}]}
#                     Do not output any other text than the JSON.'''
#
# }

_INSTRUCT_STATEMENT = {'role':'system', 'content': '''You will receive a statement from a user in a conversation 
and you need to break it down into triples consisting of a subject, predicate and object. 
Each triple should capture the essence of statement by the speaker. 
Replace the predicate by its lemma, for example "is" and "am" should become "be", "likes" and "liked" should become "like".
Remove auxiliary verbs from the predicates such as "be", "have", "can", "might", "must", "will", "shall", "should", and also negation variants such as "cannot", "won't", "shouldn't".
Remove negation words such as "n't", "no", "not" and "never" from the predicates. 
If the object starts with a preposition, concatenate the preposition to the predicate separated by a hyphen, 
for example "I am from amsterdam" should become {"subject": "I", "predicate": "be-from", "object": "amsterdam"}.
If "am", "is" or "be" is the main verb followed by an adjective then "be" should be the predicate and the adjective the object,
for example "wind is cold" should become {"subject": "wind", "predicate": "be", "object": "cold"}.
If "am", "is" or "be" is the main verb followed by a noun phrase then "be" should be the predicate and the noun phrase the object,
for example "this is a teddy bear" should become {"subject": "this", "predicate": "be", "object": "teddy-bear"}.
Do not extend the predicate with hyphens followed by determiners such as "a", "an", "the" or adjectives such as "cold", "big".
If the predicate is followed by an infinite verb phrase with "to" such as "like to swim", then the object should start with "to-" as in "to-swim".
If the predicate is an cognitive verb such as "think", "believe" or "know" or a speech-act such "say" or "tell", 
then extract the triple from the complement phrase of the predicate,
for example "I think selene likes cats" should become {"subject": "selene", "predicate": "like", "object": "cats"}. 
Combine multi-word subjects, predicates and objects with hyphens, for example "three white cats" should become "three-white-cats".
If you have no value for the subject or object use an empty string "" as a value, do NOT use none or None as a value.
Additionally, use any auxiliary verbs, negation words, adverbs and cognitive verbs to annotate each triple with:  
- Sentiment (-1 for negative, 0 for neutral, 1 for positive) 
- Polarity (-1 for negation, 0 for neutral/questioning, 1 for affirmation) 
- Certainty (a scale between 0 for uncertain and 1 for certain) 
Ensure that predicates are semantically meaningful. 
Save it as a JSON with this format:
{"sender": "user", "text": "I am from Amsterdam.", "triples": [ { "subject": "I", "predicate": "be-from", "object": "Amsterdam", "sentiment": 0, "polarity": 1, "certainty": 1}]},
{"sender": "user", "text": "lana is reading a book.", "triples": [ { "subject": "lana", "predicate": "read", "object": "book", "sentiment": 0, "polarity": 1, "certainty": 1}]},
{"sender": "user", "text": "You hate dogs.", "triples": [ { "subject": "You", "predicate": "hate", "object": "dogs", "sentiment": -1, "polarity": 1, "certainty": 0.7}]},
{"sender": "user", "text": "Selene does not like cheese.", "triples": [ { "subject": "selene", "predicate": "like", "object": "cheese", "sentiment": -1, "polarity": -1, "certainty": 0.5}]},
{"sender": "user","text": "Selene likes to swim", "triples": [ {"subject": "selene", "predicate": "like", "object": "to-swim", "sentiment": 1, "polarity": 1, "certainty": 0.1}]}
{"sender": "user","text": "Selene likes swimming", "triples": [ {"subject": "selene", "predicate": "like", "object": "swimming", "sentiment": 1, "polarity": 1, "certainty": 0.1}]}
{"sender": "user","text": "I have to go to paris", "triples": [ {"subject": "i", "predicate": "go-to", "object": "paris", "sentiment": 1, "polarity": 1, "certainty": 0.1}]}
{"sender": "user","text": "I think that you like cats", "triples": [ {"subject": "you", "predicate": "like", "object": "cats", "sentiment": 1, "polarity": 1, "certainty": 0.1}]}
{"sender": "user","text": "John said you like cats", "triples": [ {"subject": "you", "predicate": "like", "object": "cats", "sentiment": 1, "polarity": 1, "certainty": 0.1}]}
                    Do not output any other text than the JSON.'''
}

_INSTRUCT_QUESTION = {'role':'system', 'content': '''You will receive a question from a user in a conversation and you need to break it down into triples consisting of a subject, predicate,and object. 
If the question is a yes/no question that starts with a verb, the triple should capture the essence of question by the speaker, 
for example "Do cats eat grass?" should be represented as {"subject": "cats", "predicate": "eat", "object": "grass"}.
If the question contains a wh-word such as "who", whom", "what", "where", or "when" then represent the triple element for the wh-word as an empty string "",
for example "Who eats grass?" should be represented as {"subject": "", "predicate": "eat", "object": "grass"},
"What do you eat? should be represented as  {"subject": "you", "predicate": "eat", "object": ""}.
If the wh-word is preceded or followed by a preposition such as "by whom", "for what", "to where" or "who for", "what for", "where to",
extend the predicate with the a hyphen followed by the preposition,
for example "To where did Selene go?" should become {"subject": "selene", "predicate": "go-to", "object": ""}.
If the question contains "how" give an empty string for the object element but add "-by" to the predicate,
for example "How did Selene come?" should become  {"subject": "selene", "predicate": "come-by", "object": ""}.
If the question contains "why" give an empty string for the object element but add "-because" to the predicate,
for example "Why did Selene come?" should become  {"subject": "selene", "predicate": "come-because", "object": ""}.
Replace the predicate by its lemma, for example "is" and "am" should become "be", "likes" and "liked" should become "like".
Remove auxiliary verbs from the predicates such as "be", "have", "can", "might", "must", "will", "shall", "should", and also negation variants such as "cannot", "won't", "shouldn't".
Remove negation words such as "n't", "no", "not" and "never" from the predicates. 
If the object starts with a preposition, concatenate the preposition to the predicate separated by a hyphen, 
for example "Who is from Mexico?" should become {"subject": "", "predicate": "be-from", "object": "mexico"}.
If "am", "is" or "be" is the main verb followed by an adjective then "be" should be the predicate and the adjective the object,
for example "what is cold" should become {"subject": "", "predicate": "be", "object": "cold"}.
If "am", "is" or "be" is the main verb followed by a noun phrase then "be" should be the predicate and the noun phrase the object,
for example "what is a teddy bear" should become {"subject": "teddy-bear", "predicate": "be", "object": ""}.
Do not extend the predicate with determiners such as "a", "an", "the" or adjectives such as "cold", "nice".
If the predicate is followed by an infinite verb phrase with "to" such as "like to swim", then the object should start with "to-" as in "to-swim".
Combine multi-word subjects, predicates and objects with an hyphens, for example 'my-sister", "three-white-cats".
Ensure that predicates are semantically meaningful. 
Save it as a JSON with this format:
{"sender": "user","text": " Who likes cats?", "triples": [ {"subject": "", "predicate": "like", "object": "cats"}]},
{"sender": "user","text": " When did Selene come?", "triples": [ {"subject": "Selene", "predicate": "come", "object": ""}]},
{"sender": "user","text": " Where can I go?", "triples": [ {"subject": "I", "predicate": "go", "object": ""}]},
{"sender": "user","text": " Who likes cats?", "triples": [ {"subject": "", "predicate": "like", "object": "cats"}]},
{"sender": "user","text": " What are cats?", "triples": [ {"subject": "cats", "predicate": "be", "object": ""}]},
{"sender": "user","text": " Are cats pets?", "triples": [ {"subject": "cats", "predicate": "be", "object": "pets"}]},
{"sender": "user","text": " Do you like cats?", "triples": [ {"subject": "you", "predicate": "like", "object": "cats"}]}
                    Do not output any other text than the JSON.'''

}

#user_prompt = f"Analyze the following conversation with ID {conversation_id}: {conversation_text}"

class LlamaAnalyzer(Analyzer):
    def __init__(self, model_name: str, temperature: float = 0.1, s_instruct= _INSTRUCT_STATEMENT, q_instruct = _INSTRUCT_QUESTION, keep_alive=10, llama_server= "http://localhost", port= "9001"):
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
            # other params ...
        )
        self._chat = None

    def call_llama_server (self, prompt):
        completion = self._llama_client.chat.completions.create(
            # completion = client.chatCompletions.create(
            model="local-model",  # this field is currently unused
            messages=prompt,
            temperature=self._temperature,

            keep_alive= self._keep_alive,
            #max_tokens=100,
            stream=True,
        )

        content = ""
        for chunk in completion:
            if chunk.choices[0].delta.content is not None:
                content += chunk.choices[0].delta.content
        # for chunk in completion:
        #     print('chunk', chunk)
        #     if "choices" in chunk:
        #         for item in chunk:
        #             print(type(item), item)
        #             if 'content' in item:
        #                  new_message["content"] += item.delta.content
        return content

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
        instruct = self._s_instruct
        if chat.last_utterance.dialogue_acts[0]==DialogueAct.QUESTION:
            instruct = self._q_instruct
        prompt = [instruct, input]
        attempt = 0
        max=1
        while not triples and attempt<max:
            attempt += 1
           #print('attempt', attempt)
            response = self._llm.invoke(prompt)
 #           print('response', response)
            try:
                content = json.loads(response.content)
                print('content', content)
                if "triples" in content:
                    triples.extend(content["triples"])
                # if "dialogue" in content:
                #     dialogue = content["dialogue"]
                #     for field in dialogue:
                #        # print('field', field)
                #         if "triples" in field:
                #            # print(field["triples"])
                #             triples.extend(field["triples"])
            except:
                logger.debug("ERROR parsing JSON",response.content)
        for triple_value in triples:
            triple = self._convert_triple(triple_value, chat.last_utterance.utterance_speaker, chat.speaker, chat.agent)
            if triple:
                chat.last_utterance.triples.append(triple)

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
            input = {"role": "user", "content": chat.last_utterance.transcript}
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
                    if "dialogue" in content:
                        dialogue = content["dialogue"]
                        for field in dialogue:
                            if "triples" in field:
                                triples.extend(field["triples"])
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
                    print('BEFORE', triple)
                    triple["predicate"] += "-"+preposition
                    triple["object"] = triple["object"][len(preposition):].strip()
                    print('AFTER', triple)


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
        model_name=LLAMA_MODEL,temperature=0.1, keep_alive=10)
    agent = "Leolani"
    human = "Lenka"
    utterances = [{"speaker": human, "utterance": "I love cats.", "dialogue_act": DialogueAct.STATEMENT},
                  {"speaker": agent, "utterance": "I have three white cats", "dialogue_act": DialogueAct.STATEMENT},
                  {"speaker": agent, "utterance": "Do you also love dogs?", "dialogue_act": DialogueAct.QUESTION},
                  {"speaker": human, "utterance": "No I do not.", "dialogue_act": DialogueAct.STATEMENT}]
    utterances = [
        #{"speaker": human, "utterance": "my mother loves the beatles.", "dialogue_act": DialogueAct.STATEMENT},
                  {"speaker": agent, "utterance": "I have three white cats", "dialogue_act": DialogueAct.STATEMENT},
                 # {"speaker": agent, "utterance": "I come from the Netherlands", "dialogue_act": DialogueAct.STATEMENT},
                  ]
    chat = Chat("Leolani", "Lenka")
    for utterance in utterances:
        chat.add_utterance(transcript=utterance["utterance"], utterance_speaker=utterance["speaker"],
                           dialogue_acts=utterance["dialogue_act"])
        analyzer.analyze_in_context(chat)
    for utterance in chat.utterances:
        print(utterance)
        print('Final triples', utterance.triples)
