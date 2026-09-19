import os
import time

import requests
import streamlit as st

API_BASE = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="AG_NEWS Topic Router", page_icon="📰")
st.title("📰 AG_NEWS Topic Router")
st.caption("Productionized Week 13 LSTM classifier — ONNX-optimized, with a Gemini fallback.")

text = st.text_area(
    "News headline / snippet",
    placeholder="e.g. The central bank raised interest rates today.",
)

if st.button("Classify", type="primary") and text.strip():
    t0 = time.time()
    try:
        r = requests.post(f"{API_BASE}/predict", json={"text": text}, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as err:
        st.error(f"Request failed: {err}")
    else:
        rtt_ms = (time.time() - t0) * 1000
        labels = {
            "onnx_local": "🟢 local ONNX",
            "gemini_fallback": "🟡 Gemini fallback",
            "degraded": "🔴 degraded",
        }
        st.subheader(f"Category: {data['category']}")
        served = labels.get(data["provider_used"], data["provider_used"])
        if data.get("cached"):
            served += " (cached)"
        st.write(f"Served by: {served}")

        if data.get("confidence") is not None:
            st.progress(data["confidence"], text=f"Confidence: {data['confidence']:.1%}")
        if data.get("probabilities"):
            st.bar_chart(data["probabilities"])

        st.caption(
            f"Server latency: {data['latency_ms']:.2f}ms | Round-trip: {rtt_ms:.1f}ms"
        )

st.divider()
st.subheader("Batch classification")
batch_input = st.text_area("One headline per line", height=120)

if st.button("Classify batch") and batch_input.strip():
    headlines = [line for line in batch_input.splitlines() if line.strip()]
    try:
        r = requests.post(
            f"{API_BASE}/predict_batch", json={"texts": headlines}, timeout=30
        )
        r.raise_for_status()
        rows = r.json()
    except Exception as err:
        st.error(f"Request failed: {err}")
    else:
        for headline, row in zip(headlines, rows):
            conf = row.get("confidence", 0) or 0
            st.write(f"**{row['category']}** ({conf:.1%}) — {headline}")
