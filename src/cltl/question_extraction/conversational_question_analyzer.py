import itertools
import logging
from typing import List

from cltl.commons.discrete import UtteranceType, Polarity, Certainty

from cltl.triple_extraction.analyzer import Analyzer
from cltl.triple_extraction.api import Chat, DialogueAct, Utterance
from cltl.triple_extraction.conversational_triples.conversational_triple_extraction import AlbertTripleExtractor
from cltl.triple_extraction.utils.triple_normalization import TripleNormalizer

logger = logging.getLogger(__name__)

class ConversationalQuestionAnalyzer(Analyzer):
    def __init__(self, model_path: str, base_model: str, threshold: float = 0.8, max_triples: int = 0,
                 batch_size: int = 8, dialogue_acts: List[DialogueAct] = None, lang="en"):
        """
        Parameters
        ----------
        model_path: str
            Path to the model
        dialogue_acts: List[DialogueAct]
            Dialogue acts for which triple extraction should be performed
        """
        super().__init__()

        self._extractor = AlbertTripleExtractor(path=model_path, base_model=base_model, max_triples=max_triples, lang=lang)
        self._triple_normalizer = TripleNormalizer()
        self._threshold = threshold
        self._max_triples = max_triples
        self._batch_size = batch_size
        self._dialogue_acts = set(dialogue_acts) if dialogue_acts else None
        self._sep = self._extractor._sep
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

        if (self._dialogue_acts and self.utterance.dialogue_acts
                and not self._dialogue_acts.intersection(self.utterance.dialogue_acts)):
            logger.info("Ignore utterance with dialogue acts %s", self.utterance.dialogue_acts)
            return
        triples = []
        #print('chat.last_utterance.utterance_speaker', chat.last_utterance.utterance_speaker)
        #print('chat.speaker', chat.speaker)
        if chat.last_utterance.utterance_speaker == chat.speaker:
            self._chat = chat

            self._utterance = chat.last_utterance
            triples = self.ask_for_all(self._utterance, chat.speaker, chat.agent)
            if not triples:
                conversation =""
                speakers = [chat.agent, chat.speaker, chat.agent]
                if chat.last_utterance.transcript.casefold().startswith("who "):
                    conversation = self._sep + " **blank** " + self._sep + " Someone" + chat.last_utterance.transcript[3:] + " "+self._sep+"##blank##"
                else:
                    conversation = self._sep +" **blank** "+ self._sep + " " + chat.last_utterance.transcript
                    conversation = self._sep +" **blank** "+ self._sep + " " + chat.last_utterance.transcript +" " +self._sep+"##blank##"
                # if chat.last_utterance.transcript.casefold().startswith("who "):
                #     conversation = "<eos>" + "**blank**" + "<eos>" + "Someone" + chat.last_utterance.transcript[3:] + "<eos>##blank##"
                # else:
                #     conversation = "<eos>" +"**blank**"+ "<eos>" + chat.last_utterance.transcript
                #     conversation = "<eos>" +"**blank**"+ "<eos>" + chat.last_utterance.transcript +"<eos>##blank##"
                # if not conversation.endswith("?"):
                #     conversation+="?"

                # print('chat.speaker', chat.speaker)
                # print('chat.agent', chat.agent)
                # print('Conversation input', conversation)

                extracted_triples = self._extractor.extract_triples(speakers, conversation, chat.speaker, chat.agent, batch_size=self._batch_size)
                triples = [self._convert_triple(triple_value)
                           for triple_value
                           in extracted_triples]

                # triples = [self._convert_triple(triple_value)
                #            for score, triple_value
                #            in sorted(extracted_triples, key=lambda r: r[0], reverse=True)
                #            if score >= self._threshold]
                triples = list(filter(None, triples))
               # print('Triples', triples)
        else:
            logger.debug('This is not from the human speaker', chat.speaker, ' but from:', chat.last_utterance.utterance_speaker )

        if not triples:
            logger.warning("Couldn't extract triples")

        if self._max_triples and len(triples) > self._max_triples:
            logger.debug('Limit %s triples to %s', len(triples), self._max_triples)
            triples = triples[:self._max_triples]

        for triple in triples:
            logger.debug("triple: %s", triple)
            self._remove_blank(triple)
            chat.last_utterance.triples.append(triple)
            self.set_extracted_values_given_perspective(utterance_type=UtteranceType.QUESTION, triple=triple)

    def ask_for_all(self, utterance, human, agent):
        triples = []
        if utterance.casefold().startswith("Tell me all about ") or utterance.casefold().startswith("What do you know about "):
            tokens = utterance.split()
            who = tokens[-1]
            if who.endswith("?"):
                who = who[:-1]
            if who.lowercase()=="me":
                who = human
            if who.lowercase()=="you":
                who= agent
            triple = {"subject": {"label": who, "type": [], "uri": None},
                      "predicate": {"label": "", "type": [], "uri": None},
                      "object": {"label": "", "type": [], "uri": None}
                      }
            triples.append(triple)
        return triples

    def _remove_blank(self, triple):
        if triple["subject"]['label'] == "**blank**" or triple["subject"]['label'] == "blank" or triple["subject"]['label'] == "someone":
            triple["subject"]['label'] = ""
        elif "**blank**-" in triple["subject"]['label']:
            triple["subject"]['label'] = triple["subject"]['label'].replace("**blank**-", "")
        elif "-**blank**" in triple["subject"]['label']:
            triple["subject"]['label'] = triple["subject"]['label'].replace("-**blank**", "")
        elif "blank-" in triple["subject"]['label']:
            triple["subject"]['label'] = triple["subject"]['label'].replace("blank-", "")
        elif "-blank" in triple["subject"]['label']:
            triple["subject"]['label'] = triple["subject"]['label'].replace("-blank", "")

        if triple["object"]['label'] == "**blank**" or triple["object"]['label'] == "blank":
            triple["object"]['label'] = ""
        elif "**blank**-" in triple["object"]['label']:
            triple["object"]['label'] = triple["object"]['label'].replace("**blank**-", "")
        elif "-**blank**" in triple["object"]['label']:
            triple["object"]['label'] = triple["object"]['label'].replace("-**blank**", "")
        elif "blank-" in triple["object"]['label']:
            triple["object"]['label'] = triple["object"]['label'].replace("blank-", "")
        elif "-blank" in triple["object"]['label']:
            triple["object"]['label'] = triple["object"]['label'].replace("-blank", "")

        if triple["predicate"]['label'] == "**blank**" or triple["predicate"]['label'] == "blank":
            triple["predicate"]['label'] = ""
        elif "**blank**-" in triple["predicate"]['label']:
            triple["predicate"]['label'] = triple["predicate"]['label'].replace("**blank**-", "")
        elif "-**blank**" in triple["predicate"]['label']:
            triple["predicate"]['label'] = triple["predicate"]['label'].replace("-**blank**", "")
        elif "blank-" in triple["predicate"]['label']:
            triple["predicate"]['label'] = triple["predicate"]['label'].replace("blank-", "")
        elif "-blank" in triple["predicate"]['label']:
            triple["predicate"]['label'] = triple["predicate"]['label'].replace("-blank", "")
        return triple

    def _convert_triple(self, triple_value):
        if len(triple_value) < 3:
            return None

        triple = {"subject": {"label": triple_value[0], "type": [], "uri": None},
                  "predicate": {"label": triple_value[1], "type": [], "uri": None},
                  "object": {"label": triple_value[2], "type": [], "uri": None}
                  }

        self._remove_blank(triple)
        if len(triple_value) == 4:
            triple["perspective"] = {"polarity": Polarity.from_str(triple_value[3]).value}
        elif len(triple_value) == 5:
            triple["perspective"] = {"polarity": Polarity.from_str(triple_value[3]).value,
                                     "certainty": Certainty.from_str(triple_value[4]).value}

        return self._triple_normalizer.normalize(self.utterance, self.get_simple_triple(triple))

    def _chat_to_conversation(self, chat):
        utterances_by_speaker = [(speaker, " ".join(utt.transcript for utt in utterances)) for speaker, utterances
                                 in itertools.groupby(chat.utterances, lambda utt: utt.utterance_speaker)]
        utterances_by_speaker = utterances_by_speaker[-3:]

        speakers = list(zip(*utterances_by_speaker))[0]
        turns = list(zip(*utterances_by_speaker))[1]
        conversation = ("<eos>" * min(2, (3 - len(utterances_by_speaker)))) + "<eos>".join(turns)

        speaker1 = speakers[-1] if speakers else None
        if len(speakers) > 1:
            speaker2 = speakers[-2]
        else:
            speaker2 = chat.agent if speaker1 == chat.speaker else chat.speaker

        return conversation, speaker1, speaker2

    def get_simple_triple(self, triple):
        simple_triple = {'subject': triple['subject']['label'].replace(" ", "-").replace('---', '-'),
                         'predicate': triple['predicate']['label'].replace(" ", "-").replace('---', '-'),
                         'object': triple['object']['label'].replace(" ", "-").replace('---', '-'),
                         'perspective': triple['perspective']}
        return simple_triple

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

    @property
    def utterance(self) -> Utterance:
        return self._chat.last_utterance


if __name__ == "__main__":
    import json
    '''
    test files with triples are formatted like so "test sentence : subject predicate object" 
    multi-word-expressions have dashes separating their elements, and are marked with apostrophes if they are a 
    collocation
    '''
    analyzer = ConversationalQuestionAnalyzer(model_path='/Users/piek/Desktop/d-Leolani/leolani-models/conversational_triples/2024-03-11', base_model='google-bert/bert-base-multilingual-cased', lang="en")
    utterances = [{"speaker": "Lenka", "utterance": "I love cats.", "dialog_act": DialogueAct.STATEMENT},
                  {"speaker": "Leolani", "utterance": "Amazing, I never heard about cats before!", "dialog_act": DialogueAct.STATEMENT},
                  {"speaker": "Lenka", "utterance": "Do you also love dogs?", "dialog_act": DialogueAct.QUESTION}]

    utterances = [{"speaker": "Lenka", "utterance": "I love cats.", "dialog_act": DialogueAct.STATEMENT},
                  {"speaker": "Leolani", "utterance": "Amazing, I never heard about cats before!", "dialog_act": DialogueAct.STATEMENT},
                  {"speaker": "Lenka", "utterance": "What do you like?", "dialog_act": DialogueAct.QUESTION}]


    utterances = [{"speaker": "Lenka", "utterance": "What do you like?", "dialog_act": DialogueAct.QUESTION},
                  {"speaker": "Lenka", "utterance": "Do you like cats?", "dialog_act": DialogueAct.QUESTION},
                  {"speaker": "Lenka", "utterance": "Who are your friends?", "dialog_act": DialogueAct.QUESTION},
                  {"speaker": "Lenka", "utterance": "Where am I from?", "dialog_act": DialogueAct.QUESTION},
                  {"speaker": "Lenka", "utterance": "How old are you?", "dialog_act": DialogueAct.QUESTION},
                  {"speaker": "Lenka", "utterance": "Where are you?", "dialog_act": DialogueAct.QUESTION},
                  {"speaker": "Lenka", "utterance": "What is your name?", "dialog_act": DialogueAct.QUESTION},
                  {"speaker": "Lenka", "utterance": "What is my name?", "dialog_act": DialogueAct.QUESTION}
                  ]

    utterances = [{"speaker": "Lenka", "utterance": "when are you coming", "dialog_act": DialogueAct.QUESTION},
{"speaker": "Lenka", "utterance": "where are you going", "dialog_act": DialogueAct.QUESTION},
{"speaker": "Lenka", "utterance": "where can I go", "dialog_act": DialogueAct.QUESTION},
{"speaker": "Lenka", "utterance": "where did Bram come from", "dialog_act": DialogueAct.QUESTION},
{"speaker": "Lenka", "utterance": "where did you go yesterday", "dialog_act": DialogueAct.QUESTION},
{"speaker": "Lenka", "utterance": "where is Selene from", "dialog_act": DialogueAct.QUESTION},
{"speaker": "Lenka", "utterance": "where is selene from", "dialog_act": DialogueAct.QUESTION},
{"speaker": "Lenka", "utterance": "where was Selene born", "dialog_act": DialogueAct.QUESTION},
{"speaker": "Lenka", "utterance": "where were you born", "dialog_act": DialogueAct.QUESTION}]

    utterances = [{"speaker": "Lenka", "utterance": "Who can sing", "dialog_act": DialogueAct.QUESTION},
{"speaker": "Lenka", "utterance": "who hates cleaning", "dialog_act": DialogueAct.QUESTION},
{"speaker": "Lenka", "utterance": "who is from Mexico", "dialog_act": DialogueAct.QUESTION},
{"speaker": "Lenka", "utterance": "who likes singing", "dialog_act": DialogueAct.QUESTION},
{"speaker": "Lenka", "utterance": "who likes talking to people", "dialog_act": DialogueAct.QUESTION},
{"speaker": "Lenka", "utterance": "who likes watching movies", "dialog_act": DialogueAct.QUESTION},
{"speaker": "Lenka", "utterance": "Who lives in Amsterdam", "dialog_act": DialogueAct.QUESTION},
{"speaker": "Lenka", "utterance": "who lives in New York", "dialog_act": DialogueAct.QUESTION},
{"speaker": "Lenka", "utterance": "who will come to school", "dialog_act": DialogueAct.QUESTION},
{"speaker": "Lenka", "utterance": "who works at the university", "dialog_act": DialogueAct.QUESTION}]


    human="Lenka"
    agent="Leolani"
    cnt = 0
    unsolved = []
    for utt in utterances:
        if utt.get('speaker')==human and utt.get('dialog_act')==DialogueAct.QUESTION:
            chat = Chat(agent, human)
            chat.add_utterance(utt.get('utterance'), utt.get('speaker'), utt.get('dialog_act'))
            analyzer.analyze_in_context(chat)
            if len(chat.last_utterance.triples)>0:
                cnt+=1
                print('Final triples', chat.last_utterance.triples)
            else:
                unsolved.append(utt.get('utterance'))

    print("Solved:", str(cnt), " out of:" + str(len(utterances)))
    print("Unsolved:", unsolved)
