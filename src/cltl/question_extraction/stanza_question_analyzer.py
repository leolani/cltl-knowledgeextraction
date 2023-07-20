import stanza
import logging

from cltl.commons.discrete import UtteranceType

from cltl.question_extraction.question_to_statement.POSTree import POSTree
from cltl.question_extraction.analyzer import Analyzer
from cltl.triple_extraction.api import Chat, DialogueAct, Utterance
from cltl.triple_extraction.cfg_analyzer import CFGAnalyzer

# 1. Call stanza to parse a text: https://stanfordnlp.github.io/stanza/data_conversion.html#document-to-python-object
# 2. If question, use POSTree to convert it to a statement
# 3. Extract triple from statement
# 4. Convert triple to a sparql query

logger = logging.getLogger(__name__)

class StanzaQuestionAnalyzer(Analyzer):

    def __init__(self):
        """
        Abstract Analyzer Object

        Parameters
        ----------
        """
        self._parser = stanza.Pipeline(lang='en', processors='tokenize,mwt,pos,lemma,constituency')
        self._utterance = None
        self._triples = []

    @property
    def utterance(self):
        return self._utterance

    @property
    def triples(self):
        return self.utterance.triples

    def analyze_in_context(self, chat: Chat):
        self.analyze(chat.last_utterance)

    def analyze(self, utterance: Utterance):
        """

        Parameters
        ----------
        utterance: Utterance
            utterance to be analyzed

        """
        try:
            self._triples = []
            self._utterance = utterance
            if not DialogueAct.QUESTION in utterance.dialogue_acts:
                return

            transcript = utterance.transcript
            if not transcript[-1]=="." and  not transcript[-1]=="?":
                transcript +="?"
            doc = self._parser(transcript)
            statements = []
            for sentence in doc.sentences:
                tree = POSTree(str(sentence.constituency))
                try:
                    statement = tree.adjust_order()  #.replace("**blank**", "DUMMY")
                    statements.append(statement)
                    #print("Can process:", sentence)
                except Exception as e:
                    logger.warning(f"Cannot process:{sentence}")
                    logger.warning(f"Exception {e}")
            for statement in statements:
                #### Extract the triples
                chat = Chat("Leolani", "Lenka")
                triple_extractor = CFGAnalyzer()
                chat.add_utterance(statement)
                triple_extractor.analyze(chat.last_utterance)
                for triple in chat.last_utterance.triples:
                    if triple["subject"]['label']=="**blank**":
                        triple["subject"]['label']=""
                    if triple["object"]['label']=="**blank**":
                        triple["object"]['label']=""
                    if triple["predicate"]['label']=="**blank**":
                        triple["predicate"]['label']=""
                    elif "**blank**-" in triple["predicate"]['label']:
                        triple["predicate"]['label'] = triple["predicate"]['label'].replace("**blank**-", "")
                    elif "-**blank**" in triple["predicate"]['label']:
                        triple["predicate"]['label'] = triple["predicate"]['label'].replace("-**blank**", "")

                    triple["utterance_type"] = UtteranceType.QUESTION
                        # must-**blank**-go

                    self.utterance.add_triple(triple)
        except Exception as e:
            logger.exception("Exception while analyzing %s", utterance)


if __name__ == "__main__":
    analyzer = StanzaQuestionAnalyzer()

    #texts = ["What tracks users?", "Who can sing", "what can sing", "where is Selene from", "are your parents from the Netherlands"]
    texts = ["where is Selene", "where is Selene from"]
    texts = ["is purple your favorite color"]
    for text in texts:
        try:
            analyzer.analyze(text)
            print(analyzer.utterance)
            print(analyzer.triples)
        except Exception as e:
            print("Exception:", text)
            raise e

