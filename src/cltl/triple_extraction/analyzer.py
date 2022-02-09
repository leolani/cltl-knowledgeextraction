import json

from cltl.combot.backend.api import discrete
from cltl.combot.backend.utils.triple_helpers import continuous_to_enum
from cltl.triple_extraction import logger


class Analyzer(object):

    def __init__(self):
        """
        Abstract Analyzer Object: call Analyzer.analyze(utterance) factory function

        Parameters
        ----------
        """
        self._log = logger.getChild(self.__class__.__name__)
        self._log.debug("Booted")

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

    def set_extracted_values(self, utterance_type=None, triple=None, perspective={}):
        # Pack everything together
        triple["perspective"] = perspective
        triple["utterance_type"] = utterance_type

        # Set type, and triple
        self.utterance.add_triple(triple)

        if utterance_type:
            self._log.info("Utterance type: {}".format(json.dumps(utterance_type.name,
                                                                  sort_keys=True, separators=(', ', ': '))))

        if triple:
            for el in ["subject", "predicate", "object"]:
                self._log.info("RDF triplet {:>10}: {}".format(el, json.dumps(triple[el],
                                                                              sort_keys=True, separators=(', ', ': '))))
        if triple["perspective"]:
            for el in ['certainty', 'polarity', 'sentiment', 'emotion']:
                cls = getattr(discrete, el.title())
                closest = continuous_to_enum(cls, triple["perspective"][el])
                self._log.info("Perspective {:>10}: {}".format(el, closest.name))

    @property
    def utterance(self):
        """
        Returns
        -------
        utterance: Utterance
            Utterance
        """
        return self._utterance

    @property
    def triple(self):
        """
        Returns
        -------
        triple: dict or None
        """
        return self._utterance.triple
