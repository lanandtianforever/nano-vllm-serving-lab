from __future__ import annotations

import json
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any

import urllib.request
import urllib.error


@dataclass
class TokenEvent:
    ts: float
    token_idx: int
    text: str


@dataclass
class RequestRecord:
    request_id: str
    model: str
    prompt_len_estimate: int
    max_tokens: int
    arrival_time: float
    first_token_time: float | None = None
    finish_time: float | None = None
    output_tokens: int = 0
    token_events: list[TokenEvent] = field(default_factory=list)
    error: str | None = None

    @property
    def ttft(self) -> float | None:
        if self.first_token_time is None:
            return None
        return self.first_token_time - self.arrival_time

    @property
    def e2e_latency(self) -> float | None:
        if self.finish_time is None:
            return None
        return self.finish_time - self.arrival_time

    @property
    def tpot(self) -> float | None:
        if self.first_token_time is None or self.finish_time is None or self.output_tokens <= 1:
            return None
        return (self.finish_time - self.first_token_time) / (self.output_tokens - 1)

    @property
    def tokens_per_second(self) -> float | None:
        if self.first_token_time is None or self.finish_time is None:
            return None
        decode_time = self.finish_time - self.first_token_time
        if self.output_tokens <= 1 or decode_time <= 0:
            return None
        return (self.output_tokens - 1) / decode_time

    def to_dict(self, concurrency: int = 1, context_length: int = 0) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "model": self.model,
            "prompt_len_estimate": self.prompt_len_estimate,
            "max_tokens": self.max_tokens,
            "arrival_time": round(self.arrival_time, 6),
            "first_token_time": round(self.first_token_time, 6) if self.first_token_time else None,
            "finish_time": round(self.finish_time, 6) if self.finish_time else None,
            "ttft": round(self.ttft, 4) if self.ttft is not None else None,
            "e2e_latency": round(self.e2e_latency, 4) if self.e2e_latency is not None else None,
            "tpot": round(self.tpot, 6) if self.tpot is not None else None,
            "tokens_per_second": round(self.tokens_per_second, 2) if self.tokens_per_second else None,
            "output_tokens": self.output_tokens,
            "concurrency": concurrency,
            "context_length": context_length,
            "error": self.error,
        }


def generate_prompt(target_tokens: int) -> str:
    sentence = "The quick brown fox jumps over the lazy dog. "
    repeats = max(1, target_tokens // 10)
    filler = sentence * repeats
    return f"Read the following text and summarize it in one sentence:\n\n{filler}"


def generate_short_prompt() -> str:
    return "Say hello, how are you?"


class LMStudioClient:
    def __init__(self, base_url: str = "http://127.0.0.1:1234"):
        self.base_url = base_url.rstrip("/")

    def _send_streaming(
        self,
        model: str,
        prompt: str,
        max_tokens: int = 256,
    ) -> RequestRecord:
        record = RequestRecord(
            request_id=str(uuid.uuid4())[:8],
            model=model,
            prompt_len_estimate=len(prompt.split()),
            max_tokens=max_tokens,
            arrival_time=time.time(),
        )

        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
        }
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url=f"{self.base_url}/v1/chat/completions",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                for line in response:
                    line = line.decode("utf-8").strip()
                    if not line or line == "data: [DONE]":
                        continue
                    if not line.startswith("data: "):
                        continue

                    try:
                        chunk = json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue

                    if "error" in chunk:
                        record.error = chunk["error"].get("message", str(chunk["error"]))
                        record.finish_time = time.time()
                        break

                    if "choices" not in chunk:
                        continue

                    if record.first_token_time is None:
                        record.first_token_time = time.time()

                    choices = chunk.get("choices", [])
                    delta = choices[0].get("delta", {}) if choices else {}
                    content = delta.get("content") or delta.get("reasoning_content") or ""
                    if content:
                        record.token_events.append(
                            TokenEvent(ts=time.time(), token_idx=record.output_tokens, text=content)
                        )
                        record.output_tokens += 1

                    if choices and choices[0].get("finish_reason"):
                        record.finish_time = time.time()

                if record.finish_time is None:
                    record.finish_time = time.time()
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:500]
            record.error = body
            record.finish_time = time.time()
        except urllib.error.URLError as e:
            record.error = str(e)
            record.finish_time = time.time()

        return record

    def send_single(self, model: str, prompt: str, max_tokens: int = 256) -> RequestRecord:
        return self._send_streaming(model, prompt, max_tokens)

    def send_concurrent(
        self,
        model: str,
        prompts: list[str],
        max_tokens: int = 256,
        concurrency: int = 4,
    ) -> list[RequestRecord]:
        records: list[RequestRecord] = []

        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = {
                executor.submit(self._send_streaming, model, prompt, max_tokens): i
                for i, prompt in enumerate(prompts)
            }
            for future in as_completed(futures):
                records.append(future.result())

        records.sort(key=lambda r: r.arrival_time)
        return records
