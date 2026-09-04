"""
Load artifacts/model.pt -> ONNX, check parity, then dynamic int8 quantize.
Run after train_lstm.py.
"""
import json
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort
import torch
import torch.nn as nn
from onnxruntime.quantization import QuantType, quantize_dynamic

OUT_DIR = Path(__file__).resolve().parent.parent / "artifacts"


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


def _avg_ms(fn, n=50, warmup=5):
    for _ in range(warmup):
        fn()
    t0 = time.time()
    for _ in range(n):
        fn()
    return (time.time() - t0) / n * 1000


def main():
    ckpt = torch.load(OUT_DIR / "model.pt", map_location="cpu")
    net = SimpleLSTM(
        ckpt["vocab_size"],
        ckpt["embed_dim"],
        ckpt["hidden_dim"],
        ckpt["num_classes"],
        ckpt["pad_idx"],
    )
    net.load_state_dict(ckpt["model_state_dict"])
    net.eval()

    sample = torch.randint(0, ckpt["vocab_size"], (1, 16), dtype=torch.int64)
    onnx_fp32 = OUT_DIR / "model.onnx"

    torch.onnx.export(
        net,
        (sample,),
        str(onnx_fp32),
        input_names=["input_ids"],
        output_names=["logits"],
        dynamic_axes={
            "input_ids": {0: "batch", 1: "seq_len"},
            "logits": {0: "batch"},
        },
        opset_version=17,
    )
    print(f"Exported ONNX model to {onnx_fp32}")

    check = torch.randint(0, ckpt["vocab_size"], (4, 24), dtype=torch.int64)
    with torch.no_grad():
        torch_logits = net(check).numpy()

    sess = ort.InferenceSession(str(onnx_fp32), providers=["CPUExecutionProvider"])
    onnx_logits = sess.run(None, {"input_ids": check.numpy()})[0]

    max_diff = float(np.abs(torch_logits - onnx_logits).max())
    print(f"Max abs difference between PyTorch and ONNX outputs: {max_diff:.6f}")
    assert max_diff < 1e-3, "ONNX export does not match PyTorch model output"

    onnx_int8 = OUT_DIR / "model.quant.onnx"
    quantize_dynamic(str(onnx_fp32), str(onnx_int8), weight_type=QuantType.QInt8)
    print(
        f"Quantized ONNX model saved to {onnx_int8} "
        f"({onnx_fp32.stat().st_size / 1e6:.1f}MB -> {onnx_int8.stat().st_size / 1e6:.1f}MB)"
    )

    q_sess = ort.InferenceSession(str(onnx_int8), providers=["CPUExecutionProvider"])
    one = torch.randint(0, ckpt["vocab_size"], (1, 20), dtype=torch.int64)

    torch_ms = _avg_ms(lambda: net(one))
    onnx_ms = _avg_ms(lambda: sess.run(None, {"input_ids": one.numpy()}))
    quant_ms = _avg_ms(lambda: q_sess.run(None, {"input_ids": one.numpy()}))

    print(
        f"Avg latency (batch=1, seq_len=20): PyTorch={torch_ms:.2f}ms | "
        f"ONNX={onnx_ms:.2f}ms | ONNX-int8={quant_ms:.2f}ms"
    )

    metrics = json.loads((OUT_DIR / "metrics.json").read_text())
    metrics.update(
        {
            "onnx_export_max_diff": max_diff,
            "latency_ms_pytorch": torch_ms,
            "latency_ms_onnx_fp32": onnx_ms,
            "latency_ms_onnx_int8": quant_ms,
            "onnx_size_mb": onnx_fp32.stat().st_size / 1e6,
            "onnx_quant_size_mb": onnx_int8.stat().st_size / 1e6,
        }
    )
    (OUT_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
