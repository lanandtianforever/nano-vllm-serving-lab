from __future__ import annotations

import json
import time
import urllib.request
from typing import Any


class LMStudioClient:
    def __init__(self, base_url: str = "http://127.0.0.1:1234", api_token: str = "lmstudio") -> None:
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token

    def message(self, model: str, prompt: str, max_tokens: int = 256) -> dict[str, Any]:
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url=f"{self.base_url}/v1/messages",
            data=body,
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_token,
            },
            method="POST",
        )
        started = time.time()
        with urllib.request.urlopen(request, timeout=300) as response:
            raw = response.read()
        ended = time.time()
        return {
            "elapsed_s": ended - started,
            "response": json.loads(raw.decode("utf-8")),
        }
