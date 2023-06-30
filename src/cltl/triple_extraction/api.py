import enum
from datetime import datetime
from random import getrandbits
from typing import List

from cltl.commons.casefolding import casefold_text
from nltk import pos_tag

from cltl.triple_extraction import logger
from cltl.triple_extraction.utils.helper_functions import add_deduplicated


class DialogueAct(enum.Enum):
    STATEMENT = enum.auto()
    QUESTION = enum.auto()


class Chat:
    def __init__(self, agent, speaker):
        """
        Create Chat

        Parameters
        ----------
        agent: str
            Name of the agent (a.k.a. Pepper)
        speaker: str
            Name of speaker (a.k.a. the person Pepper has a chat with)
        """

        self._id = getrandbits(8)
        self._speaker = str(speaker) # self._agent1
        self._agent = str(agent)     #self._agent2
        self._utterances = []

        self._log = self._update_logger()
        self._log.info("<< Start of Chat with {} >>".format(speaker))

    @property
    def speaker(self):
        # type: () -> str
        """
        Returns
        -------
        speaker: str
            Name of speaker (a.k.a. the person Pepper has a chat with)
        """
        return self._speaker

    @speaker.setter
    def speaker(self, value):
        self._speaker = value

    @property
    def agent(self):
        # type: () -> str
        """
        Returns
        -------
        speaker: str
            Name of speaker (a.k.a. Pepper or any other agent)
        """
        return self._agent

    @agent.setter
    def agent(self, value):
        self.agent = value

    @property
    def id(self):
        # type: () -> int
        """
        Returns
        -------
        id: int
            Unique (random) identifier of this chat
        """
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

    @property
    def utterances(self):
        # type: () -> List[Utterance]
        """
        Returns
        -------
        utterances: list of Utterance
            List of utterances that occurred in this chat
        """
        return self._utterances

    @property
    def last_utterance(self):
        # type: () -> Utterance
        """
        Returns
        -------
        last_utterance: Utterance
            Most recent Utterance
        """
        return self._utterances[-1]

    def add_utterance(self, transcript, utterance_speaker=None):
        # type: (str) -> Utterance
        """
        Add Utterance to Conversation

        Parameters
        ----------
        transcript: str

        Returns
        -------
        utterance: Utterance
        """
        utterance = Utterance(self, transcript, len(self._utterances), utterance_speaker)

        #@TODO we do not know who the speaker is
        #utterance._chat_speaker = self._speaker
        #utterance._chat_agent = self._agent
        self._utterances.append(utterance)

        self._log = self._update_logger()
        self._log.info(utterance)

        return utterance

    def _update_logger(self):
        return logger.getChild("Chat".format(self.speaker, len(self._utterances)))

    def __repr__(self):
        return "\n".join([str(utterance) for utterance in self._utterances])


class Utterance:
    def __init__(self, chat: Chat, transcript: str, turn: int, utterance_speaker = None, dialogue_acts: List[DialogueAct] = None):
        """
        Construct Utterance Object

        Parameters
        ----------
        chat: Chat
            Reference to Chat Utterance is part of
        transcript: str
            Text representing the transcript of what was said
        turn: int
            Utterance Turn
        """

        self._log = logger.getChild(self.__class__.__name__)

        self._chat = chat
        self._utterance_speaker  = utterance_speaker
        #@WARNING This information duplicate the chat information and _chat_speaker is not necesarily the speaker of the utterance.
        # Use _utterance_speaker to store the speaker or source of the utterance
        self._chat_speaker = chat._speaker #superfluous with information with chat
        self._chat_agent = chat._agent
        self._turn = turn
        self._datetime = datetime.now()

        self._transcript = transcript
        self._tokens = self._clean(self._tokenize(self._transcript))

        self._dialogue_acts = dialogue_acts if dialogue_acts else []

        self._triples = []
        self._triples_as_json = []  # Convenience for deduplication

    @property
    def chat(self) -> Chat:
        """
        Returns
        -------
        chat: Chat
            Utterance Chat
        """
        return self._chat

    @property
    def utterance_speaker(self) -> str:
        """
        Returns
        --------
        speaker: str
            Name of the speaker of the utterance (not to confuse with the chat_speaker)
        """
        return self._utterance_speaker

    @property
    def chat_speaker(self) -> str:
        """
        Returns
        -------
        speaker: str
            Name of speaker (a.k.a. the person Pepper has a chat with)
        """
        return self._chat_speaker

    @property
    def chat_agent(self) -> str:
        """
        Returns
        -------
        speaker: str
            Name of agent (a.k.a. Pepper or any other agent)
        """
        return self._chat_agent

    @property
    def transcript(self) -> str:
        """
        Returns
        -------
        transcript: str
            Utterance Transcript
        """
        return self._transcript

    @property
    def turn(self) -> int:
        """
        Returns
        -------
        turn: int
            Utterance Turn
        """
        return self._turn

    @property
    def dialogue_acts(self) -> List[DialogueAct]:
        return self._dialogue_acts

    @dialogue_acts.setter
    def dialogue_acts(self, dialogue_acts):
        self._speech_acts = dialogue_acts

    @property
    def triples(self):
        # type: () -> list
        """
        Returns
        -------
        triples: List
            Structured representation of the triples found in the utterance
        """
        return self._triples

    @property
    def datetime(self):
        return self._datetime

    @property
    def tokens(self):
        """
        Returns
        -------
        tokens: list of str
            Tokenized transcript
        """
        return self._tokens

    def add_triple(self, triple):
        # type: (dict) -> (bool)

        self._triples_as_json, triple_is_new = add_deduplicated(triple, self._triples_as_json)

        if triple_is_new:
            # Add triple
            self._triples.append(triple)

        return triple_is_new

    def add_json_triple(self, triple):
        # type: (dict) -> (bool)

        self._triples.append(triple)

        return True

    def casefold(self, format='triple'):
        # type (str) -> ()
        """
        Format the labels to match triples or natural language
        Parameters
        ----------
        format

        Returns
        -------

        """
        self._chat_speaker = casefold_text(self.chat_speaker, format)

    def _tokenize(self, transcript):
        """
        Parameters
        ----------
        transcript: str
            Uttered text (Natural Language)

        Returns
        -------
        tokens: list of str
            Tokenized transcript: list of cleaned tokens for POS tagging and syntactic parsing
                - removes contractions and openers/introductions
        """

        # possible openers/greetings/introductions are removed from the beginning of the transcript
        # it is done like this to avoid lowercasing the transcript as caps are useful and google puts them
        openers = ['Leolani', 'Sorry', 'Excuse me', 'Hey', 'Hello', 'Hi']
        introductions = ['Can you tell me', 'Do you know', 'Please tell me', 'Do you maybe know']

        for o in openers:
            if transcript.startswith(o):
                transcript = transcript.replace(o, '')
            if transcript.startswith(o.lower()):
                transcript = transcript.replace(o.lower(), '')

        for i in introductions:
            if transcript.startswith(i):
                tmp = transcript.replace(i, '')
                first_word = tmp.split()[0]
                if first_word in ['what', 'that', 'who', 'when', 'where', 'which']:
                    transcript = transcript.replace(i, '')
            if transcript.startswith(i.lower()):
                tmp = transcript.replace(i.lower(), '')
                first_word = tmp.split()[0]
                if first_word.lower() in ['what', 'that', 'who', 'when', 'where', 'which']:
                    transcript = transcript.replace(i.lower(), '')

        # separating typical contractions
        transcript= transcript.replace("!", "")
        transcript= transcript.replace("?", "")
        transcript= transcript.replace(",", "")
        transcript= transcript.replace(".", "")
        tokens_raw = transcript.replace("'", " ").split()
        dict = {'m': 'am', 're': 'are', 'll': 'will'}
        dict_not = {'won': 'will', 'don': 'do', 'doesn': 'does', 'didn': 'did', 'haven': 'have', 'wouldn': 'would',
                    'aren': 'are'}

        for key in dict:
            tokens_raw = self._replace_token(tokens_raw, key, dict[key])

        if 't' in tokens_raw:
            tokens_raw = self._replace_token(tokens_raw, 't', 'not')
            for key in dict_not:
                tokens_raw = self._replace_token(tokens_raw, key, dict_not[key])

        # in case of possessive genitive the 's' is just removed, while for the aux verb 'is' is inserted
        if 's' in tokens_raw:
            index = tokens_raw.index('s')
            try:
                tag = pos_tag([tokens_raw[index + 1]])
                if tag[0][1] in ['DT', 'JJ', 'IN'] or tag[0][1].startswith('V'):  # determiner, adjective, verb
                    tokens_raw.remove('s')
                    tokens_raw.insert(index, 'is')
                else:
                    tokens_raw.remove('s')
            except:
                tokens_raw.remove('s')

        return tokens_raw

    @staticmethod
    def _replace_token(tokens_raw, old, new):
        """
        :param tokens_raw: list of tokens
        :param old: token to replace
        :param new: new token
        :return: new list with the replaced token
        """
        if old in tokens_raw:
            index = tokens_raw.index(old)
            tokens_raw.remove(old)
            tokens_raw.insert(index, new)
        return tokens_raw

    @staticmethod
    def _clean(tokens):
        """
        Parameters
        ----------
        tokens: list of str
            Tokenized transcript

        Returns
        -------
        cleaned_tokens: list of str
            Tokenized & Cleaned transcript
        """
        return tokens

    def __repr__(self):
        author = self.utterance_speaker if self.utterance_speaker else ""
        if not author:
            author = "No author"
        return '{:10s} {:03d}: "{}"'.format(author, self.turn, self.transcript)
