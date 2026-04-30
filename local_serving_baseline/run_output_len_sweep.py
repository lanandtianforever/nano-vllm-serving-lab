"""
Experiment C: Output Length Sweep.
Sweeps max_tokens to observe how TPOT and E2E latency change as output grows.
"""

from __future__ import annotations

import json
import os

from local_serving_baseline.lmstudio_client import LMStudioClient, generate_short_prompt


def run_output_len_sweep(
    model: str = "qwen/qwen3-8b",
    output_lengths: list[int] | None = None,
    output_dir: str = "local_serving_baseline/results",
) -> list[dict]:
    if output_lengths is None:
        output_lengths = [64, 128, 256, 512]

    client = LMStudioClient()
    results: list[dict] = []

    os.makedirs(output_dir, exist_ok=True)

    for max_tok in output_lengths:
        print(f"[output len sweep] max_tokens={max_tok}")
        prompt = generate_short_prompt()

        record = client.send_single(model=model, prompt=prompt, max_tokens=max_tok)
        d = record.to_dict(concurrency=1, context_length=len(prompt.split()))
        results.append(d)

        print(
            f"  TTFT={d['ttft']}s  E2E={d['e2e_latency']}s  "
            f"TPOT={d['tpot']}s  tokens/s={d['tokens_per_second']}  output_tokens={d['output_tokens']}"
        )

    output_path = os.path.join(output_dir, "output_len_sweep.jsonl")
    with open(output_path, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    print(f"[output len sweep] saved to {output_path}")

    return results


if __name__ == "__main__":
    run_output_len_sweep()
