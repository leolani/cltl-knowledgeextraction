from openie import StanfordOpenIE

from cltl.triple_extraction.analyzer import Analyzer


class OIEAnalyzer(Analyzer):
    # https://stanfordnlp.github.io/CoreNLP/openie.html#api
    # Default value of openie.affinity_probability_cap was 1/3.
    PROPERTIES = {'openie.affinity_probability_cap': 2 / 3, }

    def __init__(self):
        """
        OIE Analyzer Object

        Parameters
        ----------
        """

        super(OIEAnalyzer, self).__init__()

    def analyze(self, utterance):
        """
        Analyzer factory function

        Find appropriate Analyzer for this utterance

        Parameters
        ----------
        utterance: Utterance
            utterance to be analyzed

        """
        super(OIEAnalyzer, self).analyze(utterance)

        try:
            with StanfordOpenIE(properties=OIEAnalyzer.PROPERTIES) as client:
                text = utterance.transcript
                print('Text: %s.' % text)
                for triple in client.annotate(text):
                    self._log.info('|-', triple)
                    print('|-', triple)

                triple["predicate"] = triple.pop("relation")
                self.utterance._triple = triple

        except Exception as e:
            self._log.warning("Couldn't extract triples")
            self._log.exception(e)
