import json
import logging
import sys

from cltl.combot.backend.api.discrete import UtteranceType

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('\r%(asctime)s - %(levelname)8s - %(name)60s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class Analyzer(object):

    def __init__(self):
        """
        Abstract Analyzer Object: call Analyzer.analyze(utterance) factory function

        Parameters
        ----------
        """
        self._log = logger.getChild(self.__class__.__name__)
        self._log.info("Booted")

        self._utterance = None

    def analyze(self, utterance):
        """
        Analyzer factory function

        Determines the type of utterance, extracts the RDF triple and perspective attaching them to the last utterance

        Parameters
        ----------
        utterance: Utterance
            utterance to be analyzed

        """

        self._utterance = utterance

        NotImplementedError()

    def set_extracted_values(self, utterance_type=None, triple=None, perspective=None):
        # Set type, triple and perspective
        self.utterance.set_type(utterance_type)
        self.utterance.set_triple(triple)
        self.utterance.set_perspective(perspective)

        if utterance_type:
            self._log.info("Utterance type: {}".format(json.dumps(utterance_type.name, sort_keys=True,
                                                                  separators=(', ', ': '))))

        if triple:
            for el in ["subject", "predicate", "object"]:
                self._log.info("RDF {:>10}: {}".format(el, json.dumps(triple[el], sort_keys=True,
                                                                      separators=(', ', ': '))))
        if perspective:
            for el in ['sentiment', 'certainty', 'polarity']:
                self._log.info("Perspective {:>10}: {}".format(el, json.dumps(perspective[el], sort_keys=True,
                                                                              separators=(', ', ': '))))

            for el in ['emotion']:
                self._log.info("Perspective {:>10}: {}".format(el, json.dumps(perspective[el].name, sort_keys=True,
                                                                              separators=(', ', ': '))))

    @property
    def utterance(self):
        """
        Returns
        -------
        utterance_type: UtteranceType
            Utterance Type
        """
        return self._utterance

    @property
    def utterance_type(self):
        """
        Returns
        -------
        utterance_type: UtteranceType
            Utterance Type
        """
        return self._utterance.type

    @property
    def triple(self):
        """
        Returns
        -------
        triple: dict or None
        """
        return self._utterance.triple

    @property
    def perspective(self):
        """
        Returns
        -------
        perspective: dict or None
        """

        return self._utterance.perspective
