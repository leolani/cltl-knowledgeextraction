import logging

from openie import StanfordOpenIE

from cltl.commons.discrete import UtteranceType
from cltl.triple_extraction.analyzer import Analyzer
from cltl.triple_extraction.api import Chat
from cltl.triple_extraction.utils.helper_functions import fix_pronouns

logger = logging.getLogger(__name__)


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
        self._utterance = None

    @property
    def utterance(self):
        return self._utterance

    def analyze_in_context(self, chat: Chat):
        self.analyze(chat.last_utterance)

    def analyze(self, utterance):
        """
        Analyzer factory function

        Find appropriate Analyzer for this utterance

        Parameters
        ----------
        utterance: Utterance
            utterance to be analyzed

        """
        self._utterance = utterance

        try:
            with StanfordOpenIE(properties=OIEAnalyzer.PROPERTIES) as client:
                text = utterance.transcript

                result = client.annotate(text)
                if result:
                    logger.info(f'Found {len(result)} triples')
                    for triple in result:
                        # Final triple assignment
                        fixed_triple = {
                            "subject": {'label': fix_pronouns(triple['subject'], self._utterance.chat.speaker, self._utterance.chat.agent),
                                        'type': []},
                            "predicate": {'label': triple['relation'], 'type': []},
                            "object": {'label': fix_pronouns(triple['object'], self._utterance.chat.speaker, self._utterance.chat.agent),
                                       'type': []},
                        }

                        self.set_extracted_values(utterance_type=UtteranceType.STATEMENT, triple=fixed_triple)

        except Exception:
            logger.exception("Couldn't extract triples")
