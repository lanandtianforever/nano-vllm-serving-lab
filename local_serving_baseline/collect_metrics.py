from __future__ import annotations

import json

from local_serving_baseline.lmstudio_client import LMStudioClient


def collect_single_prompt(model: str, prompt: str, max_tokens: int = 256) -> dict:
    client = LMStudioClient()
    record = client.send_single(model=model, prompt=prompt, max_tokens=max_tokens)
    return record.to_dict()


def collect_concurrent(
    model: str, prompts: list[str], max_tokens: int = 256, concurrency: int = 4
) -> list[dict]:
    client = LMStudioClient()
    records = client.send_concurrent(model=model, prompts=prompts, max_tokens=max_tokens, concurrency=concurrency)
    return [r.to_dict(concurrency=concurrency) for r in records]
