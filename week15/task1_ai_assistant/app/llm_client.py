"""Gemini (tools + structured JSON) and Ollama (plain local chat)."""
import httpx
from google import genai
from google.genai import types

from . import config
from .net import ipv4_httpx_client
from .schemas import AssistantAnswer

SYSTEM_INSTRUCTION = (
    "You are the Fusemachines AI Fellowship Course Assistant. You help students "
    "find information in their own course materials (weekly guides and assignments). "
    "Always use the search_course_materials tool before answering questions about "
    "course content -- never rely on memory alone. If the answer isn't in the course "
    "materials, say so honestly and set escalate_to_human."
)


class GeminiClient:
    def __init__(self):
        self._client = genai.Client(
            api_key=config.GEMINI_API_KEY,
            http_options=types.HttpOptions(httpx_client=ipv4_httpx_client()),
        )

    def chat(self, message: str, tools: list, temperature: float, top_p: float) -> AssistantAnswer:
        # Pass 1: tools on, free text (SDK handles the tool loop).
        draft = self._client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=temperature,
                top_p=top_p,
                tools=tools,
            ),
        )
        draft_text = draft.text or ""

        # Pass 2: tools off, force AssistantAnswer JSON.
        packed = self._client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=(
                f"User question: {message}\n\nDraft answer: {draft_text}\n\n"
                "Package this into the required JSON schema."
            ),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=AssistantAnswer,
            ),
        )
        return packed.parsed


class OllamaClient:
    def __init__(self, host: str = config.OLLAMA_HOST, model: str = config.OLLAMA_MODEL):
        self.host = host
        self.model = model

    def chat(self, message: str, temperature: float) -> str:
        url = f"{self.host}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": message},
            ],
            "stream": False,
            "options": {"temperature": temperature},
        }
        r = httpx.post(url, json=payload, timeout=60.0)
        r.raise_for_status()
        return r.json()["message"]["content"]
