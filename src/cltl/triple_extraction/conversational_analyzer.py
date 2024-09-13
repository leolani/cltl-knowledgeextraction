import itertools
import logging
from typing import List

from cltl.commons.discrete import UtteranceType, Polarity, Certainty

from cltl.triple_extraction.analyzer import Analyzer
from cltl.triple_extraction.api import Chat, DialogueAct, Utterance
from cltl.triple_extraction.conversational_triples.conversational_triple_extraction import AlbertTripleExtractor
from cltl.triple_extraction.utils.triple_normalization import TripleNormalizer

logger = logging.getLogger(__name__)


qwords_en = ["what", "when", "where", "who", "why", "how"]
whowords = ["who", "wie"]
qverbs_en = ["do", "does", "did", "have", "has", "is", "are", "were", "was"]
qwords_nl = ["wat", "wanneer", "waar", "waarom", "hoe"]
qverbs_nl = ["kan", "kun", "wil", "ben", "is", "zijn", "waren", "moet", "ga", "zal", "gaan", "gingen"]

class ConversationalAnalyzer(Analyzer):
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

        self._extractor = AlbertTripleExtractor(path=model_path, base_model=base_model, max_triples=max_triples,
                                                lang=lang)
        self._triple_normalizer = TripleNormalizer()
        self._threshold = threshold
        self._max_triples = max_triples
        self._batch_size = batch_size
        self._sep = self._extractor._sep
        self._dialogue_acts = set(dialogue_acts) if dialogue_acts else None

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

    def is_question(self, transcript):
        words = transcript.split()
        if words[0].lower() in qwords_en+qwords_nl+qverbs_en+qverbs_nl+whowords:
            return True
        if words[-1]=="?":
            return True
        return False


    def analyze_in_context(self, chat):
        """
        Analyzer factory function

        Find appropriate Analyzer for this utterance

        Parameters
        ----------
        utterance: Utterance
            utterance to be analyzed

        """
        if self.is_question(chat.last_utterance.transcript):
            chat.last_utterance.dialogue_acts=[UtteranceType.QUESTION]
            self.analyze_question_in_context(chat)
        else:
            chat.last_utterance.dialogue_acts=[UtteranceType.STATEMENT]
            self.analyze_statement_in_context(chat)

    def analyze_statement_in_context(self, chat):
        self._chat = chat
        if (self._dialogue_acts and self.utterance.dialogue_acts
                and not self._dialogue_acts.intersection(self.utterance.dialogue_acts)):
            logger.debug("Ignore utterance with dialogue acts %s", self.utterance.dialogue_acts)
            return

        triples = []
        if chat.last_utterance.utterance_speaker == chat.speaker:
            self._chat = chat

            self._utterance = chat.last_utterance
            speakers, conversation, speaker1, speaker2 = self._chat_to_conversation(chat)

            extracted_triples = self._extractor.extract_triples(speakers, conversation, chat.speaker, chat.agent,
                                                                batch_size=self._batch_size)
            triples = [self._convert_triple(triple_value)
                       for score, triple_value
                       in sorted(extracted_triples, key=lambda r: r[0], reverse=True)
                       if score >= self._threshold]
            triples = list(filter(None, triples))
        else:
            logger.debug('This is not from the human speaker', chat.speaker, ' but from:',
                         chat.last_utterance.utterance_speaker)

        if not triples:
            logger.warning("Couldn't extract triples")

        if self._max_triples and len(triples) > self._max_triples:
            logger.debug('Limit %s triples to %s', len(triples), self._max_triples)
            triples = triples[:self._max_triples]

        for triple in triples:
            logger.debug("triple: %s", triple)
            self.set_extracted_values_given_perspective(utterance_type=UtteranceType.STATEMENT, triple=triple)


    def analyze_question_in_context_org(self, chat):
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
        if chat.last_utterance.utterance_speaker == chat.speaker:
            self._chat = chat
            self._utterance = chat.last_utterance
            conversation =""

            if chat.last_utterance.transcript.casefold().startswith("who ") or chat.last_utterance.transcript.casefold().startswith("wie ") :
                conversation = self._sep + " **blank** " + self._sep + " Someone" + chat.last_utterance.transcript[3:] + " "+self._sep+"##blank##"
            else:
                conversation = self._sep +" **blank** "+ self._sep + " " + chat.last_utterance.transcript
                conversation = self._sep +" **blank** "+ self._sep + " " + chat.last_utterance.transcript +" " +self._sep+"##blank##"

            if not conversation.endswith("?"):
                conversation+="?"

            extracted_triples = self._extractor.extract_triples(conversation, chat.speaker, chat.agent, batch_size=self._batch_size)
            triples = [self._convert_triple(triple_value)
                       for score, triple_value
                       in sorted(extracted_triples, key=lambda r: r[0], reverse=True)
                       if score >= self._threshold]
            triples = list(filter(None, triples))
        else:
            logger.debug('This is not from the human speaker', chat.speaker, ' but from:', chat.last_utterance.utterance_speaker )

        if not triples:
            logger.warning("Couldn't extract triples")

        for triple in triples:
            logger.debug("triple: %s", triple)
            self._remove_blank(triple)
            chat.last_utterance.triples.append(triple)
            self.set_extracted_values_given_perspective(utterance_type=UtteranceType.QUESTION, triple=triple)

    def _remove_blank_org(self, triple):
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


    def analyze_question_in_context(self, chat):
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
        if chat.last_utterance.utterance_speaker == chat.speaker:
            self._chat = chat
            self._utterance = chat.last_utterance

            triples = self.ask_for_all(self._utterance, chat.speaker, chat.agent)
            if not triples:
                    # Dummy list of speakers
                    speakers = [chat.agent, chat.speaker, chat.agent]
                    pos = self._utterance.transcript.index(" ")
                    first_word = self._utterance.transcript[:pos]
                    if first_word.lower() in whowords:
                        conversation = self._sep + " **blank** " + self._sep + " "+self._utterance.transcript
                        if not conversation.endswith("?"):
                            conversation += "?"
                        conversation += " "+self._sep+" Joe"
                    elif first_word.lower() in qwords_nl+qwords_en:
                        conversation = self._sep + " **blank** " + self._sep + " "+self._utterance.transcript
                        if not conversation.endswith("?"):
                            conversation += "?"
                        conversation += " "+self._sep+" Something"
                    elif first_word.lower() in qverbs_en+qverbs_nl:
                        conversation = self._sep + " **blank** " + self._sep + " "+self._utterance.transcript
                        if not conversation.endswith("?"):
                             conversation += "?"
                        conversation += " "+self._sep+" Yes"

                    extracted_triples = self._extractor.extract_triples(speakers, conversation, chat.speaker, chat.agent, batch_size=self._batch_size)

                    ##### We do not need to score these triples since we use dummies
                    # for score, triple_value in sorted(extracted_triples, key=lambda r: r[0], reverse=True):
                    #     triples = [self._convert_triple(triple_value)]
                    #     break
                    for triple_value in extracted_triples:
                        triples = [self._convert_triple(triple_value)]
            # end of else:
            triples = list(filter(None, triples))
        else:
            logger.warning('This is not from the human speaker', chat.speaker, ' but from:', chat.last_utterance.utterance_speaker )

        if not triples:
            logger.warning("Couldn't extract triples")

        if self._max_triples and len(triples) > self._max_triples:
            logger.debug('Limit %s triples to %s', len(triples), self._max_triples)
            triples = triples[:self._max_triples]

        for triple in triples:
            logger.info("triple: %s", triple)
            self._remove_blank(triple)
            chat.last_utterance.triples.append(triple)
            self.set_extracted_values_given_perspective(utterance_type=UtteranceType.QUESTION, triple=triple)

    def ask_for_all(self, utterance, human, agent):
        triples = []
        if utterance.transcript.lower().startswith("tell me all about ") or \
                utterance.transcript.lower().startswith("tell me about ") or \
                utterance.transcript.lower().startswith("what do you know about "):
            tokens = utterance.transcript.split()
            who = tokens[-1]
            if who.endswith("?"):
                who = who[:-1]
            if who.lower()=="me":
                who = human
            elif who.lower()=="you":
                who= agent
            elif who.lower().startswith("your"):
                who= agent
            triple = {"subject": {"label": who.lower(), "type": [], "uri": None},
                      "predicate": {"label": "", "type": ["n2mu"], "uri": None},
                      "object": {"label": "", "type": [], "uri": None},
                      "perspective": self.extract_perspective()
                      }
            triples.append(triple)
        return triples

    def _remove_blank(self, triple):
        if triple["subject"]['label'] == "**blank**" or triple["subject"]['label'] == "blank" \
                or triple["subject"]['label'] == "joe" \
                or triple["subject"]['label'] == "who" \
                or triple["subject"]['label'] == "someone":
            triple["subject"]['label'] = ""
        elif "**blank**-" in triple["subject"]['label']:
            triple["subject"]['label'] = triple["subject"]['label'].replace("**blank**-", "")
        elif "-**blank**" in triple["subject"]['label']:
            triple["subject"]['label'] = triple["subject"]['label'].replace("-**blank**", "")
        elif "blank-" in triple["subject"]['label']:
            triple["subject"]['label'] = triple["subject"]['label'].replace("blank-", "")
        elif "-blank" in triple["subject"]['label']:
            triple["subject"]['label'] = triple["subject"]['label'].replace("-blank", "")

        if triple["object"]['label'] == "**blank**" or triple["object"]['label'] == "blank" or triple["object"]['label'] == "something":
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

        ##### This should be based on the chat object  and not some obscure order
        # speaker1 = speakers[-1] if speakers else None
        # if len(speakers) > 1:
        #     speaker2 = speakers[-2]
        # else:
        #     speaker2 = chat.agent if speaker1 == chat.speaker else chat.speaker

        return speakers, conversation, chat.speaker, chat.agent

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
    '''
    test files with triples are formatted like so "test sentence : subject predicate object" 
    multi-word-expressions have dashes separating their elements, and are marked with apostrophes if they are a 
    collocation
    '''

    analyzer = ConversationalAnalyzer(model_path='/Users/piek/Desktop/d-Leolani/leolani-models/conversational_triples/2024-03-11', base_model='google-bert/bert-base-multilingual-cased', lang="en")
    agent = "Leolani"
    human="Lenka"
    utterances = [{"speaker": human, "utterance": "I love cats.", "dialogue_act": DialogueAct.STATEMENT},
                  {"speaker": agent, "utterance": "Do you also love dogs?", "dialogue_act": DialogueAct.QUESTION},
                  {"speaker": human, "utterance": "No I do not.", "dialogue_act": DialogueAct.STATEMENT}]
    chat = Chat("Leolani", "Lenka")
    for utterance in utterances:
        chat.add_utterance(transcript=utterance["utterance"], utterance_speaker=utterance["speaker"], dialogue_acts=utterance["dialogue_act"])
        analyzer.analyze_in_context(chat)
    for utterance in chat.utterances:
        print(utterance)
        print('Final triples', utterance.triples)
