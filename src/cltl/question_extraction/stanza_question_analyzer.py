import stanza
from cltl.question_extraction.question_to_statement import POSTree
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
        self._utterance = utterance
        doc = self._parser(self._utterance)
        statements = []
        for sentence in doc.sentences:
            tree = POSTree(str(sentence.constituency))
            statement = tree.adjust_order().replace("**blank**", "DUMMY")
            statements.append(statement)
        for statement in statements:
            #### Extract the triples
            chat = Chat("Leolani", "Lenka")
            triple_extractor = CFGAnalyzer()
            chat.add_utterance(statement)
            triple_extractor.analyze(chat.last_utterance)
            for triple in chat.last_utterance.triples:
                DUMMY = False
                if triple["subject"]=="DUMMY":
                    triple["subject"]=="?"
                    DUMMY = True
                if triple["predicate"]=="DUMMY":
                    triple["predicate"]=="?"
                    DUMMY = True
                if triple["object"]=="DUMMY":
                    triple["object"]=="?"
                    DUMMY = True
                if DUMMY:
                    self._triples.append(triple)



if __name__ == "__main__":

    analyzer = StanzaQuestionAnalyzer()
    text = 'What tracks users?'
    analyzer.analyze(text)
    print(analyzer.utterance)
    print(analyzer.triples)

