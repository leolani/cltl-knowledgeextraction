import stanza
from cltl.question_extraction.question_to_statement.POSTree import POSTree
from cltl.question_extraction.analyzer import Analyzer
from cltl.triple_extraction.api import Chat
from cltl.triple_extraction.cfg_analyzer import CFGAnalyzer

# 1. Call stanza to parse a text: https://stanfordnlp.github.io/stanza/data_conversion.html#document-to-python-object
# 2. If question, use POSTree to convert it to a statement
# 3. Extract triple from statement
# 4. Convert triple to a sparql query


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
        return self._triples

    def analyze(self, utterance):
        """

        Parameters
        ----------
        utterance: Utterance
            utterance to be analyzed

        """
        try:
            self._triples = []
            self._utterance = utterance
            if not utterance[-1]=="." and  not utterance[-1]=="?":
                self._utterance +="?"
            doc = self._parser(self._utterance)
            statements = []
            for sentence in doc.sentences:
                tree = POSTree(str(sentence.constituency))
                try:
                    statement = tree.adjust_order()  #.replace("**blank**", "DUMMY")
                    statements.append(statement)
                except:
                    print("Cammot process:", sentence)
            for statement in statements:
                #### Extract the triples
                chat = Chat("Leolani", "Lenka")
                triple_extractor = CFGAnalyzer()
                chat.add_utterance(statement)
                triple_extractor.analyze(chat.last_utterance)
                for triple in chat.last_utterance.triples:
                    DUMMY = False
                    if triple["subject"]['label']=="**blank**":
                        triple["subject"]['label']=""
                        DUMMY = True
                    if triple["predicate"]['label']=="**blank**":
                        triple["predicate"]['label']=""
                        DUMMY = True
                    if triple["object"]['label']=="**blank**":
                        triple["object"]['label']=""
                        DUMMY = True
                    if DUMMY:
                        self._triples.append(triple)
        except Exception as e:
            print("Exception:", utterance)
            raise e



if __name__ == "__main__":
    analyzer = StanzaQuestionAnalyzer()

    texts = ["What tracks users?", "Who can sing", "what can sing", "where is selene from"]
    texts = ["where is selene from"]
    for text in texts:
        try:
            analyzer.analyze(text)
            print(analyzer.utterance)
            print(analyzer.triples)
        except Exception as e:
            print("Exception:", text)
            raise e

