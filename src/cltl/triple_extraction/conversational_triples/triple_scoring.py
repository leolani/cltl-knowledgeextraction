import glob
import torch
from transformers import AutoTokenizer, AutoModel, AutoConfig
from tqdm import tqdm

# Capture errors
from transformers import logging
logging.set_verbosity(40)

from utils import *


class TripleScoring(torch.nn.Module):
    def __init__(self, base_model='albert-base-v2', path=None, max_len=80, sep='<eos>'):
        super().__init__()
        # Base model
        print('loading %s for triple scoring' % base_model)
        # Load base model
        self._model = AutoModel.from_pretrained(base_model)
        self._max_len = max_len
        self._base = base_model
        self._sep = sep

        # Load and extend tokenizer with SPEAKERS
        self._tokenizer = AutoTokenizer.from_pretrained(base_model)
        self._tokenizer.add_tokens(['SPEAKER1', 'SPEAKER2'], special_tokens=True)
        self._model.resize_token_embeddings(len(self._tokenizer))

        # SPO candidate scoring head
        hidden_size = AutoConfig.from_pretrained(base_model).hidden_size
        self._head = torch.nn.Linear(hidden_size, 3)
        self._relu = torch.nn.ReLU()
        self._softmax = torch.nn.Softmax(dim=-1)

        # GPU support
        self._device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
        self.to(self._device)

        # Load model / tokenizer if pretrained model is given
        if path:
            print('\t- Loading pretrained')
            model_path = glob.glob(path + '/candidate_scorer_' + base_model + '.zip')[0]
            self.load_state_dict(torch.load(model_path, map_location=self._device))

    def forward(self, input_ids, speaker_ids, attn_mask):
        """ Computes the forward pass through the model
        """
        out = self._model(input_ids=input_ids, token_type_ids=speaker_ids, attention_mask=attn_mask)
        h = self._relu(out.last_hidden_state[:, 0])
        return self._softmax(self._head(h))

    def _retokenize_dialogue(self, tokens, speaker=1):
        # Tokenize each token individually (keeping track of subwords)
        f_input_ids = [self._tokenizer.cls_token_id]
        speaker_ids = [speaker]
        for turn in ' '.join(tokens).split(self._sep):
            token_ids = self._tokenizer.encode(turn, add_special_tokens=True)[1:]  # strip [CLS]
            f_input_ids += token_ids
            speaker_ids += [speaker] * len(token_ids)
            speaker = 1 - speaker

        return f_input_ids, speaker_ids

    def _retokenize_triple(self, triple):
        # Append triple
        f_input_ids = self._tokenizer.encode(' '.join(triple), add_special_tokens=False)
        speaker_ids = [0] * len(f_input_ids)
        return f_input_ids, speaker_ids

    def _add_padding(self, sequence, pad_token):
        # If sequence is too long, cut off end
        sequence = sequence[:self._max_len]

        # Pad remainder to max_len
        padding = self._max_len - len(sequence)
        new_sequence = sequence + [pad_token] * padding

        # Mask out [PAD] tokens
        attn_mask = [1] * len(sequence) + [0] * padding
        return new_sequence, attn_mask

    def fit(self, tokens, triples, labels, epochs=2, lr=1e-6):
        """ Fits the model to the annotations
        """
        X = []
        for tokens, triple_lst, triple_labels in zip(tokens, triples, labels):

            # Tokenize dialogue
            dialog_input_ids, dialog_speakers = self._retokenize_dialogue(tokens)

            for triple, label in zip(triple_lst, triple_labels):
                # Tokenize triple
                triple_input_ids, triple_speakers = self._retokenize_triple(triple)

                # Concatenate dialogue + [UNK] + triple
                input_ids = dialog_input_ids[:-1] + [self._tokenizer.unk_token_id] + triple_input_ids
                speakers = dialog_speakers[:-1] + [0] + triple_speakers

                # Pad sequence with [PAD] to max_len
                input_ids, _ = self._add_padding(input_ids, self._tokenizer.pad_token_id)
                speakers, attn_mask = self._add_padding(speakers, 0)

                # Push Tensor to GPU
                input_ids = torch.LongTensor([input_ids]).to(self._device)
                speakers = torch.LongTensor([speakers]).to(self._device)
                attn_mask = torch.FloatTensor([attn_mask]).to(self._device)
                label_ids = torch.LongTensor([label]).to(self._device)

                X.append((input_ids, speakers, attn_mask, label_ids))

        # Set up optimizer and objective
        optimizer = torch.optim.Adam(self.parameters(), lr=lr)
        criterion = torch.nn.CrossEntropyLoss()

        for epoch in range(epochs):
            random.shuffle(X)

            losses = []
            for input_ids, speaker_ids, attn_mask, y in tqdm(X):
                # Was the triple entailed? Positively? Negatively?
                y_hat = self(input_ids, speaker_ids, attn_mask)
                loss = criterion(y_hat, y)
                losses.append(loss.item())

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

            print("mean loss =", np.mean(losses))

        # Save model to file
        torch.save(self.state_dict(), 'candidate_scorer_%s' % self._base)

    def predict(self, tokens, triples):
        # Re-tokenize dialogue
        dialog_input_ids, dialog_speakers = self._retokenize_dialogue(tokens)

        batch_input_ids = []
        batch_speakers = []
        batch_attn_mask = []

        for triple in triples:
            # Tokenize triple
            triple_input_ids, triple_speakers = self._retokenize_triple(triple)

            # Concatenate dialogue tokens, [UNK] and triple
            input_ids = dialog_input_ids + [self._tokenizer.unk_token_id] + triple_input_ids
            speakers = dialog_speakers + [0] + triple_speakers

            # Pad sequence with [PAD] to max_len
            input_ids, _ = self._add_padding(input_ids, self._tokenizer.pad_token_id)
            speakers, attn_mask = self._add_padding(speakers, 0)

            batch_input_ids.append(input_ids)
            batch_speakers.append(speakers)
            batch_attn_mask.append(attn_mask)

        # Push batches to GPU
        batch_input_ids = torch.LongTensor(batch_input_ids).to(self._device)
        batch_speakers = torch.LongTensor(batch_speakers).to(self._device)
        batch_attn_mask = torch.FloatTensor(batch_attn_mask).to(self._device)

        label = self(batch_input_ids, batch_speakers, batch_attn_mask)
        label = label.cpu().detach().numpy()
        return label


if __name__ == '__main__':
    annotations = load_annotations('<path_to_annotations')

    # Extract annotation triples and compute negative triples
    tokens, triples, labels = [], [], []
    for ann in annotations:
        ann_tokens, ann_triples, triple_labels = extract_triples(ann)
        triples.append(ann_triples)
        labels.append(triple_labels)
        tokens.append([t for ts in ann_tokens for t in ts + ['<eos>']])

    # Fit model
    scorer = TripleScoring()
    scorer.fit(tokens, triples, labels)
    torch.save(scorer.state_dict(), 'models/scorer_albert-v2_31_03_2022')


