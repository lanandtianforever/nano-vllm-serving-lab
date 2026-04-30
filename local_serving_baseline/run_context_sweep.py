"""
Experiment A: Context Length Sweep.
Sweeps different prompt lengths to observe TTFT, E2E latency, and tokens/s
as context length grows.
"""

from __future__ import annotations

import json
import os

from local_serving_baseline.lmstudio_client import LMStudioClient, generate_prompt


def run_context_sweep(
    model: str = "qwen/qwen3-8b",
    context_lengths: list[int] | None = None,
    max_tokens: int = 128,
    output_dir: str = "local_serving_baseline/results",
) -> list[dict]:
    if context_lengths is None:
        context_lengths = [512, 1024, 2048, 4096]

    client = LMStudioClient()
    results: list[dict] = []

    os.makedirs(output_dir, exist_ok=True)

    for ctx_len in context_lengths:
        prompt = generate_prompt(ctx_len // 2)
        print(f"[context sweep] ctx_len={ctx_len}  (prompt ~{len(prompt.split())} words)")

        record = client.send_single(model=model, prompt=prompt, max_tokens=max_tokens)
        d = record.to_dict(concurrency=1, context_length=ctx_len)
        results.append(d)

        print(
            f"  TTFT={d['ttft']}s  E2E={d['e2e_latency']}s  "
            f"tokens/s={d['tokens_per_second']}  output_tokens={d['output_tokens']}"
        )

    output_path = os.path.join(output_dir, "context_sweep.jsonl")
    with open(output_path, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    print(f"[context sweep] saved to {output_path}")

    return results


if __name__ == "__main__":
    run_context_sweep()
