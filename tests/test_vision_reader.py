"""Tests for the Ollama reader, using a fake connection so Ollama doesn't need to be running."""

import pytest
import requests
from PIL import Image

from scam_checker.screenshot.ocr import OllamaVisionReader, TextReadingError, split_into_lines


class FakeResponse:
    def __init__(self, status_code: int, body: dict | None = None):
        self.status_code = status_code
        self._body = body or {}

    def json(self):
        return self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))


def fake_post(reply_text: str, sent_requests: list):
    def post(url, json, timeout):
        sent_requests.append(json)
        return FakeResponse(200, {"message": {"content": reply_text}})

    return post


def test_reader_sends_the_image_and_returns_lines():
    sent = []
    reader = OllamaVisionReader(model="qwen2.5vl:3b", post=fake_post("Hi there\n£85 each", sent))
    assert reader.read(Image.new("RGB", (20, 20))) == ["Hi there", "£85 each"]
    assert sent[0]["model"] == "qwen2.5vl:3b"
    assert len(sent[0]["messages"][0]["images"]) == 1


def test_code_fences_and_blank_lines_are_dropped():
    assert split_into_lines("```\nHi there\n\n£85 each\n```") == ["Hi there", "£85 each"]


def test_clear_message_when_ollama_is_not_running():
    def post(url, json, timeout):
        raise requests.ConnectionError()

    with pytest.raises(TextReadingError, match="Open the Ollama app"):
        OllamaVisionReader(post=post).read(Image.new("RGB", (20, 20)))


def test_clear_message_when_the_model_is_not_downloaded():
    def post(url, json, timeout):
        return FakeResponse(404)

    with pytest.raises(TextReadingError, match="ollama pull qwen2.5vl:3b"):
        OllamaVisionReader(model="qwen2.5vl:3b", post=post).read(Image.new("RGB", (20, 20)))
