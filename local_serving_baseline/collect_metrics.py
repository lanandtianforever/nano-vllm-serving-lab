from __future__ import annotations

from local_serving_baseline.lmstudio_client import LMStudioClient


def collect_single_prompt(model: str, prompt: str) -> dict:
    client = LMStudioClient()
    return client.message(model=model, prompt=prompt)
