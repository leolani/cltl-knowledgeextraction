import json
import logging

from cltl.triple_extraction.api import Chat


logger = logging.getLogger(__name__)


class Analyzer:
    def analyze_in_context(self, chat: Chat):
        """
        Analyzer factory function

        Determines the type of utterance, extracts the RDF triple and perspective attaching them to the last utterance

        Parameters
        ----------
        chat: Chat
            contains the previous utterances and extracted triples if any

        """
        raise NotImplementedError()

    def analyze(self, utterance):
        """Deprecated, use `analyze_in_context` instead!"""
        raise NotImplementedError()

    def set_extracted_values(self, utterance_type=None, triple=None, perspective={}):
        # Pack everything together
        triple["perspective"] = perspective
        triple["utterance_type"] = utterance_type

        # Set type, and triple
        triple_is_new = self.utterance.add_triple(triple)

        if not triple_is_new:
            return

        if utterance_type:
            self._log_info("Utterance type: {}".format(json.dumps(utterance_type.name,
                                                                  sort_keys=True, separators=(', ', ': '))))

        if triple:
            for el in ["subject", "predicate", "object"]:
                self._log_info("RDF triplet {:>10}: {}".format(el, json.dumps(triple[el],
                                                                              sort_keys=True, separators=(', ', ': '))))

    @property
    def utterance(self):
        """
        Returns
        -------
        utterance: Utterance
            Utterance
        """
        raise NotImplementedError()

    @property
    def triple(self):
        """
        Returns
        -------
        triple: dict or None
        """
        return self.utterance.triple

    def _log_info(self, message):
        logger.info("%s: %s", self.__class__.__name__, message)