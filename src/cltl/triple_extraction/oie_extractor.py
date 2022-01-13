import logging

from openie import StanfordOpenIE

from cltl.triple_extraction.analyzer import Analyzer


class OIEAnalyzer(Analyzer):
    # https://stanfordnlp.github.io/CoreNLP/openie.html#api
    # Default value of openie.affinity_probability_cap was 1/3.
    PROPERTIES = {'openie.affinity_probability_cap': 2 / 3, }

    LOG = logging.getLogger(__name__)

    def __init__(self, chat):
        """
        Abstract Analyzer Object: call Analyzer.analyze(utterance) factory function

        Parameters
        ----------
        chat: Chat
            Chat to be analyzed
        """

        self._chat = chat

    @staticmethod
    def analyze(chat):
        """
        Analyzer factory function

        Find appropriate Analyzer for this utterance

        Parameters
        ----------
        chat: Chat
            Chat to be analyzed

        Returns
        -------
        analyzer: Analyzer
            Appropriate Analyzer Subclass
        """

        try:
            with StanfordOpenIE(properties=OIEAnalyzer.PROPERTIES) as client:
                text = chat.last_utterance.transcript
                print('Text: %s.' % text)
                for triple in client.annotate(text):
                    OIEAnalyzer.LOG.info('|-', triple)
                    print('|-', triple)

        except Exception as e:
            OIEAnalyzer.LOG.warning("Couldn't extract triples")
            OIEAnalyzer.LOG.exception(e)

    @property
    def chat(self):
        """
        Returns
        -------
        chat: Chat
            Chat to be analyzed
        """
        return self._chat

    @property
    def utterance_type(self):
        """
        Returns
        -------
        utterance_type: UtteranceType
            Utterance Type
        """
        return NotImplementedError()

    @property
    def triple(self):
        """
        Returns
        -------
        triple: dict or None
        """
        return self._triple

    @property
    def perspective(self):
        """
        Returns
        -------
        perspective: dict or None
        """

        return self._perspective
