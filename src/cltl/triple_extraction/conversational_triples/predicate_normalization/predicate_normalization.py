import torch
import numpy as np
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModel
from sklearn.neighbors import KNeighborsClassifier

import spacy
from lemminflect import getInflection


class BERT:
    def __init__(self, base_model='bert-base-uncased'):
        print('Loading %s for predicate normalization' % base_model)
        self._tokenizer = AutoTokenizer.from_pretrained(base_model)
        self._model = AutoModel.from_pretrained(base_model)

    def _tokenize(self, subj, pred, obj):
        # Add [CLS] + subj
        input_ids = [self._tokenizer.cls_token_id]
        input_ids += self._tokenizer.encode(subj, add_special_tokens=False)

        # Add pred (remember indices!)
        pred_ids = self._tokenizer.encode(pred, add_special_tokens=False)
        pred_idx = list(range(len(input_ids), len(input_ids) + len(pred_ids)))
        input_ids += pred_ids

        # Add obj + sentence-final [SEP]
        input_ids += self._tokenizer.encode(obj, add_special_tokens=False)
        input_ids += [self._tokenizer.sep_token_id]
        return input_ids, pred_idx

    def get_embedding(self, subj, pred, obj):
        # Tokenize context and determine where the predicate comes from
        triple_ids, pred_idx = self._tokenize(subj, pred, obj)

        # Feed context through model
        state = self._model(torch.LongTensor([triple_ids])).last_hidden_state

        # Get embeddings of predicate tokens
        return torch.mean(state[0, pred_idx], dim=0).detach().numpy()


class PredicateNormalizer:
    def __init__(self, exemplar_file, base_model='bert-base-uncased', k=3, min_conf=0.4):
        self._model = BERT(base_model)
        self._nlp = spacy.load('en_core_web_sm')
        self._knn = KNeighborsClassifier(n_neighbors=k, metric=self._cosine_dist, weights='distance', algorithm='brute')
        self._fit_knn(exemplar_file)
        self._min_conf = min_conf

    def _fit_knn(self, path):
        print('\t- Fitting kNN')
        X, y = [], []
        with open(path, 'r', encoding='utf-8') as file:
            for i, line in tqdm(enumerate(file)):
                line = line.strip()
                if line and not line.startswith('#'):
                    try:
                        norm_pred, subj, pred, obj = [t.strip() for t in line.strip().split(',')]
                        # Precompute embeddings
                        X.append(self._model.get_embedding(subj, pred, obj))
                        y.append(norm_pred)
                    except:
                        print('Error in line %s: %s' % (i, line))
        self._knn.fit(X, y)

    @staticmethod
    def _cosine_dist(x, y):
        sim = x.dot(y) / (np.linalg.norm(x) * np.linalg.norm(y))
        return 1 - sim

    def _normalize_surface_form(self, pred):
        pred_tokens = []
        for token in list(self._nlp('I ' + pred))[1:]:
            # Map verbs to third-person singular
            if token.pos_ in ['VERB', 'INTJ', 'AUX']:
                inflections = getInflection(token.lemma_, tag='VBZ')  # may yield multiple inflections still
                token_string = token.lower_ if not inflections else inflections[0]
            else:
                token_string = token.lower_

            pred_tokens.append(token_string)

        # Use '_' as delimiter
        return '_'.join(pred_tokens)

    def normalize(self, subj, pred, obj):
        # Get contextual embedding of predicate
        x = self._model.get_embedding(subj, pred, obj)

        # Compute probability of each normalized predicate
        probs = self._knn.predict_proba([x])[0]

        # Identify normalized predicate with the highest likelihood
        i = np.argmax(probs)

        # Normalize only above minimum confidence
        if probs[i] > self._min_conf:
            return self._knn.classes_[i], probs[i]

        # If no match is found, map predicate to 3rd-person singular
        pred = self._normalize_surface_form(pred)
        return pred, probs[i]


if __name__ == '__main__':
    pred_norm = PredicateNormalizer('training_exemplars.txt')
    while True:
        subj = input('subj: ')
        pred = input('pred: ')
        obj_ = input(' obj: ')
        print(pred_norm.normalize(subj, pred, obj_))
