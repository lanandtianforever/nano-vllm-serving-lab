"""
Experiment B: Concurrency Sweep.
Sends N identical prompts concurrently and measures tail latency behaviour.
"""

from __future__ import annotations

import json
import os

from local_serving_baseline.lmstudio_client import LMStudioClient, generate_short_prompt


def run_concurrency_sweep(
    model: str = "qwen/qwen3-8b",
    concurrency_levels: list[int] | None = None,
    max_tokens: int = 128,
    output_dir: str = "local_serving_baseline/results",
) -> list[dict]:
    if concurrency_levels is None:
        concurrency_levels = [1, 2, 4, 8]

    client = LMStudioClient()
    all_results: list[dict] = []

    os.makedirs(output_dir, exist_ok=True)

    for level in concurrency_levels:
        print(f"[concurrency sweep] concurrency={level}")
        prompts = [generate_short_prompt() for _ in range(level * 2)]

        records = client.send_concurrent(
            model=model, prompts=prompts, max_tokens=max_tokens, concurrency=level
        )

        for r in records:
            d = r.to_dict(concurrency=level, context_length=len(prompts[0].split()))
            all_results.append(d)
            print(
                f"  {d['request_id']}: TTFT={d['ttft']}s  E2E={d['e2e_latency']}s  "
                f"tokens/s={d['tokens_per_second']}"
            )

    output_path = os.path.join(output_dir, "concurrency_sweep.jsonl")
    with open(output_path, "w") as f:
        for r in all_results:
            f.write(json.dumps(r) + "\n")
    print(f"[concurrency sweep] saved to {output_path}")

    return all_results


if __name__ == "__main__":
    run_concurrency_sweep()
