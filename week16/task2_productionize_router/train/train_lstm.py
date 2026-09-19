"""
Train AG_NEWS LSTM (Week 13 SimpleLSTM) on the full train split.
Writes model.pt, vocab.json, and metrics.json under ../artifacts/.
"""
import json
import re
import time
from collections import Counter
from pathlib import Path

import torch
import torch.nn as nn
from datasets import load_dataset
from torch.utils.data import DataLoader

OUT_DIR = Path(__file__).resolve().parent.parent / "artifacts"
OUT_DIR.mkdir(parents=True, exist_ok=True)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
LABELS = ["World", "Sports", "Business", "Sci/Tech"]

EMBED_DIM = 64
HIDDEN_DIM = 128
MIN_FREQ = 3
MAX_VOCAB_SIZE = 30000
BATCH_SIZE = 64
EPOCHS = 8
LR = 0.001
GRAD_CLIP_NORM = 1.0


def tokenize(text):
    return re.findall(r"[a-z0-9]+", text.lower())


class SimpleLSTM(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, num_classes, pad_idx):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=pad_idx)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, num_classes)

    def forward(self, text):
        x = self.embedding(text)
        _, (h, _) = self.lstm(x)
        return self.fc(h[-1])


def build_vocab(train_split, min_freq, max_size):
    counts = Counter()
    for row in train_split:
        counts.update(tokenize(row["text"]))

    kept = [tok for tok, n in counts.most_common() if n >= min_freq][:max_size]
    itos = ["<unk>", "<pad>"] + kept
    stoi = {tok: i for i, tok in enumerate(itos)}
    return stoi, len(itos)


def main():
    print(f"Using device: {DEVICE}")
    started = time.time()

    ds = load_dataset("fancyzhx/ag_news")
    train_split, test_split = ds["train"], ds["test"]
    print(
        f"Train rows: {len(train_split)} | Test rows: {len(test_split)} "
        f"({time.time() - started:.1f}s)"
    )

    stoi, vocab_size = build_vocab(train_split, MIN_FREQ, MAX_VOCAB_SIZE)
    unk_idx = stoi["<unk>"]
    pad_idx = stoi["<pad>"]
    print(f"Vocab size (min_freq={MIN_FREQ}, cap={MAX_VOCAB_SIZE}): {vocab_size:,}")

    def to_ids(text):
        return [stoi.get(tok, unk_idx) for tok in tokenize(text)]

    def collate(batch):
        y = torch.tensor([ex["label"] for ex in batch], dtype=torch.int64)
        xs = [torch.tensor(to_ids(ex["text"]), dtype=torch.int64) for ex in batch]
        x = nn.utils.rnn.pad_sequence(xs, batch_first=True, padding_value=pad_idx)
        return x, y

    train_loader = DataLoader(
        train_split, batch_size=BATCH_SIZE, shuffle=True, collate_fn=collate
    )
    test_loader = DataLoader(
        test_split, batch_size=BATCH_SIZE, shuffle=False, collate_fn=collate
    )

    net = SimpleLSTM(vocab_size, EMBED_DIM, HIDDEN_DIM, len(LABELS), pad_idx).to(DEVICE)
    print(f"Model parameters: {sum(p.numel() for p in net.parameters()):,}")

    opt = torch.optim.Adam(net.parameters(), lr=LR)
    loss_fn = nn.CrossEntropyLoss()

    for epoch in range(EPOCHS):
        net.train()
        epoch_t0 = time.time()
        running_loss = 0.0
        n_ok = 0
        n_seen = 0

        for xb, yb in train_loader:
            xb, yb = xb.to(DEVICE), yb.to(DEVICE)
            opt.zero_grad()
            logits = net(xb)
            loss = loss_fn(logits, yb)
            loss.backward()
            # Early training can explode without this on LSTMs.
            torch.nn.utils.clip_grad_norm_(net.parameters(), GRAD_CLIP_NORM)
            opt.step()

            running_loss += loss.item()
            n_ok += (logits.argmax(1) == yb).sum().item()
            n_seen += yb.size(0)

        train_acc = n_ok / n_seen

        net.eval()
        val_ok = 0
        val_seen = 0
        with torch.no_grad():
            for xb, yb in test_loader:
                xb, yb = xb.to(DEVICE), yb.to(DEVICE)
                logits = net(xb)
                val_ok += (logits.argmax(1) == yb).sum().item()
                val_seen += yb.size(0)
        val_acc = val_ok / val_seen

        print(
            f"Epoch {epoch + 1}/{EPOCHS} | Train Acc: {train_acc:.1%} | "
            f"Test Acc: {val_acc:.1%} | {time.time() - epoch_t0:.1f}s"
        )

    torch.save(
        {
            "model_state_dict": net.state_dict(),
            "vocab_size": vocab_size,
            "embed_dim": EMBED_DIM,
            "hidden_dim": HIDDEN_DIM,
            "num_classes": len(LABELS),
            "pad_idx": pad_idx,
        },
        OUT_DIR / "model.pt",
    )

    with open(OUT_DIR / "vocab.json", "w") as f:
        json.dump(
            {
                "stoi": stoi,
                "unk_idx": unk_idx,
                "pad_idx": pad_idx,
                "class_names": LABELS,
            },
            f,
        )

    with open(OUT_DIR / "metrics.json", "w") as f:
        json.dump(
            {
                "final_test_accuracy": val_acc,
                "vocab_size": vocab_size,
                "epochs": EPOCHS,
                "total_train_seconds": time.time() - started,
            },
            f,
            indent=2,
        )

    print(
        f"Saved model.pt, vocab.json, metrics.json to {OUT_DIR} "
        f"({time.time() - started:.1f}s total)"
    )


if __name__ == "__main__":
    main()
