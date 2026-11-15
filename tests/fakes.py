"""Stand-ins for Ollama's HTTP replies, so tests never need Ollama running."""

import requests


class FakeResponse:
    def __init__(self, status_code: int, body: dict | None = None):
        self.status_code = status_code
        self._body = body or {}

    def json(self):
        return self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))


def fake_post(reply_text: str, sent_requests: list | None = None):
    """A stand-in for requests.post that always answers with `reply_text`."""

    def post(url, json, timeout):
        if sent_requests is not None:
            sent_requests.append(json)
        return FakeResponse(200, {"message": {"content": reply_text}})

    return post
