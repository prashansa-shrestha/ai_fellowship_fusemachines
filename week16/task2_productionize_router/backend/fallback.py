"""Gemini-backed classifier used when the local ONNX path blows up."""
from typing import Literal

from google import genai
from google.genai import types
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from . import config
from .net import ipv4_httpx_client

CLASS_NAMES = ["World", "Sports", "Business", "Sci/Tech"]


class TopicPrediction(BaseModel):
    category: Literal["World", "Sports", "Business", "Sci/Tech"]


class GeminiFallbackClassifier:
    def __init__(self):
        self._client = genai.Client(
            api_key=config.GEMINI_API_KEY,
            http_options=types.HttpOptions(httpx_client=ipv4_httpx_client()),
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
    def predict_one(self, text: str) -> dict:
        prompt = (
            f"Classify this news headline into exactly one category "
            f"from {CLASS_NAMES}: {text!r}"
        )
        resp = self._client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=TopicPrediction,
            ),
        )
        return {
            "category": resp.parsed.category,
            "confidence": None,
            "probabilities": None,
        }
