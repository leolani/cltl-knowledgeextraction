import itertools
import logging
import os

import openai
from cltl.commons.discrete import UtteranceType
from dotenv import load_dotenv

from cltl.triple_extraction.analyzer import Analyzer
from cltl.triple_extraction.api import Chat

logger = logging.getLogger(__name__)


def chatgpt(utterances, model="gpt-3.5-turbo"):
    """ functions to call ChatGPT predictions """
    response = openai.ChatCompletion.create(
        model=model,
        messages=utterances,
        temperature=0,
        top_p=1,
        max_tokens=100,
        frequency_penalty=0,
        presence_penalty=0
    )
    return {
        'prompt': utterances,
        'text': response['choices'][0]['message']['content'],
        'finish_reason': response['choices'][0]['finish_reason']
    }


class LlmAnalyzer(Analyzer):
    def __init__(self):
        """
        LLM (GPT3.5) Analyzer Object

        Parameters
        ----------
        """
        load_dotenv()
        openai.api_key = os.getenv("OPENAI_API_KEY")

        self._utterance = None
        self._pre_prompt = """
This is a triple extraction task over snippets of dialogue. 
Please find all named entities, and the relations that connect them. 
Answer without any explanation, in the format ["entity_type", "entity_name"]->["relation"]->["entity_type", "entity_name"]  
If no triple exists, then just answer "[]".

Dialogue: 
    Lola: My birthday is on October 24th
    John: I did not know that!
    Lola: I am still a 17 year old girl
Triples: 
    ["Person", "Lola"]->"birthday"->["October 24", "Date"]
    ["Person", "John"]->["know"]->["Event", "Lola's birthday"]
    ["Person", "Lola"]->["age"]->["Age", "17 years old"]
    ["Person", "Lola"]->["gender"]->["Gender", "female"] 

Dialogue: 
    Vilko: I used to play football in school
    Jonna: are you going to the high school football game tonight?
    Vilko: I never miss a game
Triples: 
    ["Person", "Vilko"]->["play"]->["Sport", "football"] 
    ["Person", "Vilko"]->["play-football"]->["Time", "in-school"]
    ["Person", "Vilko"]->["watch"]->["Sport", "football"] 
    ["Person", "Vilko"]->["watch-football"]->["Time", "tonight"]
    
Dialogue: 
    """

    @property
    def utterance(self):
        return self._utterance

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
        self._chat = chat
        self._utterance = chat.last_utterance

        # Extract triples
        dialogue_history = self._format_dialogue_history(chat)
        triples = self._prompt_for_triples(dialogue_history)

        # Extract perspective
        # perspective = self.extract_perspective()
        # triples = [triple.update({'perspective': perspective}) for triple in triples]

        # Final triple assignment
        if triples:
            for triple in triples:
                logger.info('final triple: {}'.format(triple))
                self.set_extracted_values(utterance_type=UtteranceType.STATEMENT, triple=triple)
        else:
            logger.warning("Couldn't extract triples")

    def extract_perspective(self):
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

    def _format_dialogue_history(self, chat):
        # Group utterances by speaker to create something closer to turns
        utterances_by_speaker = [(speaker, " ".join(utt.transcript for utt in utterances)) for speaker, utterances
                                 in itertools.groupby(chat.utterances, lambda utt: utt.utterance_speaker)]

        # Take the last 3, as that's the chunk size
        utterances_by_speaker = utterances_by_speaker[-3:]

        # Format
        conversation = '\n\t'.join([f"{el[0]}: {el[1]}" for el in utterances_by_speaker])

        return conversation

    def _prompt_for_triples(self, text):
        prompt = self._pre_prompt + f'{text}\nTriples:\n\t'
        prompt = [{"role": "user", "content": prompt}]

        prediction = chatgpt(prompt)

        triples = self._clean_prediction(prediction['text'])

        return triples

    def _clean_prediction(self, txt):
        candidates = txt.split('\n')

        triples = []
        for candidate in candidates:
            elements = candidate.split('->')
            elements = [e.strip('[]"') for e in elements]

            triple = {
                "subject": {"label": elements[0].split('", "')[1], "type": [elements[0].split('", "')[0]], "uri": None},
                "predicate": {"label": elements[1], "type": [], "uri": None},
                "object": {"label": elements[2].split('", "')[1], "type": [elements[2].split('", "')[0]], "uri": None}
            }

            triples.append(triple)

        return triples


if __name__ == "__main__":
    '''
    test files with triples are formatted like so "test sentence : subject predicate object" 
    multi-word-expressions have dashes separating their elements, and are marked with apostrophes if they are a 
    collocation
    '''
    chat = Chat("Leolani", "Lenka")
    utterances = [("Thomas", "I like animals."), ("Thomas", "I love cats."),
                  ("Jaap", "Do you also love dogs?"),
                  ("Thomas", "No I do not.")]
    analyzer = LlmAnalyzer()

    for speaker, utterance in utterances:
        chat.add_utterance(utterance, speaker)

    analyzer.analyze_in_context(chat)
    # print(utterance)
    # print('Final triples', utterance.triples)
