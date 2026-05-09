"""
Experiment A: Context Length Sweep.
Sweeps different prompt lengths to observe TTFT, E2E latency, and tokens/s
as context length grows.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from collections import defaultdict
from typing import Iterable

from local_serving_baseline.lmstudio_client import LMStudioClient


def build_context_prompt(target_words: int, sample_idx: int) -> str:
    """Build a deterministic long prompt with enough lexical variety."""
    base_facts = [
        "tenant isolation requires predictable capacity planning",
        "prefill work dominates the first token latency for long prompts",
        "decode work advances one generated token at a time",
        "kv cache usage grows with active context and generated tokens",
        "tail latency is more important than average latency for serving",
        "shared prefixes can reduce repeated prefill computation",
        "scheduler policy changes can improve one request class while hurting another",
        "goodput measures requests that finish within the target service objective",
    ]
    words: list[str] = []
    cursor = 0
    while len(words) < target_words:
        fact = base_facts[(cursor + sample_idx) % len(base_facts)]
        sentence = (
            f"Observation {cursor}: {fact}. "
            f"Request group {sample_idx} keeps the same conclusion but changes the wording. "
        )
        words.extend(sentence.split())
        cursor += 1

    body = " ".join(words[:target_words])
    return (
        "You are evaluating a local LLM serving endpoint. "
        "Read the synthetic workload notes below and summarize the dominant "
        "serving bottleneck in exactly two concise sentences.\n\n"
        f"{body}\n\nSummary:"
    )


def percentile(values: Iterable[float], p: float) -> float | None:
    ordered = sorted(v for v in values if v is not None)
    if not ordered:
        return None
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * p
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    weight = rank - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def summarize_by_context(rows: list[dict]) -> list[dict]:
    grouped: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[int(row["context_length"])].append(row)

    summaries: list[dict] = []
    for context_length in sorted(grouped):
        group = grouped[context_length]

        def values(field: str) -> list[float]:
            return [row[field] for row in group if row.get(field) is not None]

        def avg(field: str) -> float | None:
            vals = values(field)
            if not vals:
                return None
            return sum(vals) / len(vals)

        summaries.append(
            {
                "context_length": context_length,
                "num_requests": len(group),
                "num_errors": sum(1 for row in group if row.get("error")),
                "avg_prompt_len_estimate": avg("prompt_len_estimate"),
                "avg_ttft": avg("ttft"),
                "p50_ttft": percentile(values("ttft"), 0.50),
                "p95_ttft": percentile(values("ttft"), 0.95),
                "avg_e2e_latency": avg("e2e_latency"),
                "p95_e2e_latency": percentile(values("e2e_latency"), 0.95),
                "avg_tpot": avg("tpot"),
                "avg_tokens_per_second": avg("tokens_per_second"),
                "avg_output_tokens": avg("output_tokens"),
            }
        )
    return summaries


def write_jsonl(path: str, rows: list[dict]) -> None:
    with open(path, "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def write_summary_markdown(path: str, rows: list[dict], summaries: list[dict]) -> None:
    lines = [
        "# Day 3 Context Sweep Summary",
        "",
        "This summary is generated from the raw JSONL file produced by",
        "`local_serving_baseline/run_context_sweep.py`.",
        "",
        f"Total requests: {len(rows)}",
        "",
        "| Context label | Requests | Errors | Avg prompt words | Avg TTFT (s) | P50 TTFT (s) | P95 TTFT (s) | Avg E2E (s) | P95 E2E (s) | Avg TPOT (s) | Avg tokens/s | Avg output chunks |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    def fmt(value: float | int | None) -> str:
        if value is None:
            return "n/a"
        if isinstance(value, int):
            return str(value)
        return f"{value:.4f}"

    for item in summaries:
        lines.append(
            "| "
            + " | ".join(
                [
                    fmt(item["context_length"]),
                    fmt(item["num_requests"]),
                    fmt(item["num_errors"]),
                    fmt(item["avg_prompt_len_estimate"]),
                    fmt(item["avg_ttft"]),
                    fmt(item["p50_ttft"]),
                    fmt(item["p95_ttft"]),
                    fmt(item["avg_e2e_latency"]),
                    fmt(item["p95_e2e_latency"]),
                    fmt(item["avg_tpot"]),
                    fmt(item["avg_tokens_per_second"]),
                    fmt(item["avg_output_tokens"]),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Interview Notes",
            "",
            "- Treat `context_length` as the configured experiment label; `prompt_len_estimate` is word-count based, not tokenizer-accurate.",
            "- Long prompts may be capped by `--max-prompt-words` to avoid exceeding the loaded LM Studio context window.",
            "- Use this run to discuss how longer prompts increase prefill pressure and TTFT in a black-box local serving setup.",
            "- Do not claim vLLM PagedAttention or GPU-side KV cache behavior from this Mac + LM Studio run.",
        ]
    )

    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def run_context_sweep(
    model: str = "qwen/qwen3-8b",
    context_lengths: list[int] | None = None,
    max_tokens: int = 64,
    requests_per_length: int = 5,
    prompt_word_ratio: float = 0.55,
    max_prompt_words: int = 2900,
    output_dir: str = "local_serving_baseline/results",
    output_prefix: str = "context_sweep_day3",
) -> list[dict]:
    if context_lengths is None:
        context_lengths = [1024, 2048, 4096, 8192]

    client = LMStudioClient()
    results: list[dict] = []

    os.makedirs(output_dir, exist_ok=True)

    for ctx_len in context_lengths:
        target_words = max(1, min(int(ctx_len * prompt_word_ratio), max_prompt_words))
        for sample_idx in range(requests_per_length):
            prompt = build_context_prompt(target_words=target_words, sample_idx=sample_idx)
            print(
                f"[context sweep] ctx_len={ctx_len} sample={sample_idx + 1}/{requests_per_length} "
                f"(prompt ~{len(prompt.split())} words)"
            )

            record = client.send_single(model=model, prompt=prompt, max_tokens=max_tokens)
            d = record.to_dict(concurrency=1, context_length=ctx_len)
            d["sample_idx"] = sample_idx
            d["target_prompt_words"] = target_words
            results.append(d)

            print(
                f"  TTFT={d['ttft']}s  E2E={d['e2e_latency']}s  "
                f"TPOT={d['tpot']}s  tokens/s={d['tokens_per_second']}  "
                f"output_tokens={d['output_tokens']} error={d['error']}"
            )

    output_path = os.path.join(output_dir, f"{output_prefix}.jsonl")
    summary_path = os.path.join(output_dir, f"{output_prefix}_summary.md")
    write_jsonl(output_path, results)
    write_summary_markdown(summary_path, results, summarize_by_context(results))
    print(f"[context sweep] saved raw results to {output_path}")
    print(f"[context sweep] saved summary to {summary_path}")

    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local LM Studio context length sweep.")
    parser.add_argument("--model", default="qwen/qwen3-8b")
    parser.add_argument("--lengths", nargs="+", type=int, default=[1024, 2048, 4096, 8192])
    parser.add_argument("--max-tokens", type=int, default=64)
    parser.add_argument("--requests-per-length", type=int, default=5)
    parser.add_argument("--prompt-word-ratio", type=float, default=0.55)
    parser.add_argument("--max-prompt-words", type=int, default=2900)
    parser.add_argument("--output-dir", default="local_serving_baseline/results")
    parser.add_argument("--output-prefix", default="context_sweep_day3")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_context_sweep(
        model=args.model,
        context_lengths=args.lengths,
        max_tokens=args.max_tokens,
        requests_per_length=args.requests_per_length,
        prompt_word_ratio=args.prompt_word_ratio,
        max_prompt_words=args.max_prompt_words,
        output_dir=args.output_dir,
        output_prefix=args.output_prefix,
    )
