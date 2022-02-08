from openie import StanfordOpenIE

from cltl.combot.backend.api.discrete import UtteranceType
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

                result = client.annotate(text)
                if result:
                    self._log.info(f'Found {len(result)} triples')
                    for triple in result:
                        # Final triple assignment
                        fixed_triple = {
                            "subject": {'label': triple['subject'], 'type': []},
                            "predicate": {'label': triple['relation'], 'type': []},
                            "object": {'label': triple['object'], 'type': []},
                        }

                        self.set_extracted_values(utterance_type=UtteranceType.STATEMENT, triple=fixed_triple)

        except Exception as e:
            self._log.warning("Couldn't extract triples")
            self._log.exception(e)
