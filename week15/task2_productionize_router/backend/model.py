"""ONNX Runtime inference for the AG_NEWS LSTM — no torch in the serve path."""
from __future__ import annotations

import json
import re
from typing import List

import numpy as np
import onnxruntime as ort

from . import config


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - logits.max(axis=-1, keepdims=True)
    exps = np.exp(shifted)
    return exps / exps.sum(axis=-1, keepdims=True)


class RouterModel:
    def __init__(self):
        meta = json.loads(config.VOCAB_PATH.read_text())
        self.stoi = meta["stoi"]
        self.unk_idx = meta["unk_idx"]
        self.pad_idx = meta["pad_idx"]
        self.class_names = meta["class_names"]
        self.session = ort.InferenceSession(
            str(config.ONNX_MODEL_PATH),
            providers=["CPUExecutionProvider"],
        )

    def _to_ids(self, text: str) -> List[int]:
        ids = [self.stoi.get(tok, self.unk_idx) for tok in tokenize(text)]
        return ids if ids else [self.unk_idx]

    def _pad(self, sequences: List[List[int]]) -> np.ndarray:
        width = max(len(seq) for seq in sequences)
        rows = [seq + [self.pad_idx] * (width - len(seq)) for seq in sequences]
        return np.array(rows, dtype=np.int64)

    def predict_one(self, text: str) -> dict:
        return self.predict_batch([text])[0]

    def predict_batch(self, texts: List[str]) -> List[dict]:
        ids = [self._to_ids(t) for t in texts]
        batch = self._pad(ids)
        logits = self.session.run(None, {"input_ids": batch})[0]
        probs = _softmax(logits)

        out: List[dict] = []
        for row in probs:
            best = int(np.argmax(row))
            out.append(
                {
                    "category": self.class_names[best],
                    "confidence": float(row[best]),
                    "probabilities": {
                        name: float(p) for name, p in zip(self.class_names, row)
                    },
                }
            )
        return out
