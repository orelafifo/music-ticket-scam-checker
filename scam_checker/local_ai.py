"""Talk to the AI model running on this computer through Ollama.

Ollama is a free app that runs AI models locally, so nothing sent here goes online.
One model, Qwen2.5-VL, does two jobs: reading screenshots and spotting people's names.
"""

from __future__ import annotations

import base64
import io
import os
from typing import Callable

import requests
from PIL import Image

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
LOCAL_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5vl:3b")
REPLY_TIMEOUT_SECONDS = 180  # the first request also loads the model, which is slow

PostRequest = Callable[..., requests.Response]


class LocalAIError(RuntimeError):
    """Raised with a plain-English message the app can show to the user."""


class OllamaChat:
    def __init__(self, model: str = LOCAL_MODEL, base_url: str = OLLAMA_URL, post: PostRequest = requests.post):
        self.model = model
        self._chat_url = f"{base_url}/api/chat"
        self._post = post

    def ask(self, prompt: str, images: list[Image.Image] | None = None, json_reply: bool = False) -> str:
        message = {"role": "user", "content": prompt}
        if images:
            message["images"] = [image_to_base64(image) for image in images]
        # Temperature 0 means "always the most likely answer": no creative variation.
        request_body = {"model": self.model, "messages": [message], "stream": False, "options": {"temperature": 0}}
        if json_reply:
            request_body["format"] = "json"  # Ollama then only allows valid JSON as the reply
        return self._send(request_body)

    def _send(self, request_body: dict) -> str:
        try:
            response = self._post(self._chat_url, json=request_body, timeout=REPLY_TIMEOUT_SECONDS)
        except requests.ConnectionError as error:
            raise LocalAIError("Ollama isn't running. Open the Ollama app, then try again.") from error
        if response.status_code == 404:
            raise LocalAIError(f"The AI model isn't downloaded yet. In the terminal, run: ollama pull {self.model}")
        response.raise_for_status()
        return response.json()["message"]["content"]


def image_to_base64(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")
