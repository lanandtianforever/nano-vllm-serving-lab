"""
Experiment C: Output Length Sweep.
Sweeps max_tokens to observe how TPOT and E2E latency change as output grows.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from collections import defaultdict
from typing import Iterable

from local_serving_baseline.lmstudio_client import LMStudioClient


def build_long_output_prompt(sample_idx: int) -> str:
    return (
        "Write a long numbered list for an LLM serving benchmark. "
        "Continue until the API stops you. Do not end early. "
        "Each item must be one short sentence about serving latency, prefill, "
        "decode, KV cache, batching, tail latency, or benchmark design. "
        f"Use benchmark variant {sample_idx} and produce at least 220 numbered items.\n\n"
        "Begin now:\n"
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


def summarize_by_output_length(rows: list[dict]) -> list[dict]:
    grouped: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[int(row["max_tokens"])].append(row)

    summaries: list[dict] = []
    for max_tokens in sorted(grouped):
        group = grouped[max_tokens]
        successful = [row for row in group if not row.get("error")]

        def values(field: str) -> list[float]:
            return [row[field] for row in successful if row.get(field) is not None]

        def avg(field: str) -> float | None:
            vals = values(field)
            if not vals:
                return None
            return sum(vals) / len(vals)

        summaries.append(
            {
                "max_tokens": max_tokens,
                "num_requests": len(group),
                "num_errors": sum(1 for row in group if row.get("error")),
                "avg_ttft": avg("ttft"),
                "p50_ttft": percentile(values("ttft"), 0.50),
                "p95_ttft": percentile(values("ttft"), 0.95),
                "avg_e2e_latency": avg("e2e_latency"),
                "p95_e2e_latency": percentile(values("e2e_latency"), 0.95),
                "avg_tpot": avg("tpot"),
                "p95_tpot": percentile(values("tpot"), 0.95),
                "avg_tokens_per_second": avg("tokens_per_second"),
                "avg_output_chunks": avg("output_tokens"),
            }
        )
    return summaries


def write_jsonl(path: str, rows: list[dict]) -> None:
    with open(path, "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def write_summary_markdown(path: str, rows: list[dict], summaries: list[dict]) -> None:
    lines = [
        "# Day 4 Output Length Sweep Summary",
        "",
        "This summary is generated from the raw JSONL file produced by",
        "`local_serving_baseline/run_output_len_sweep.py`.",
        "",
        f"Total requests: {len(rows)}",
        "",
        "Latency and throughput metrics below exclude rows with non-null `error`.",
        "",
        "| Max tokens | Requests | Errors | Avg TTFT (s) | P50 TTFT (s) | P95 TTFT (s) | Avg E2E (s) | P95 E2E (s) | Avg TPOT (s) | P95 TPOT (s) | Avg chunks/s | Avg output chunks |",
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
                    fmt(item["max_tokens"]),
                    fmt(item["num_requests"]),
                    fmt(item["num_errors"]),
                    fmt(item["avg_ttft"]),
                    fmt(item["p50_ttft"]),
                    fmt(item["p95_ttft"]),
                    fmt(item["avg_e2e_latency"]),
                    fmt(item["p95_e2e_latency"]),
                    fmt(item["avg_tpot"]),
                    fmt(item["p95_tpot"]),
                    fmt(item["avg_tokens_per_second"]),
                    fmt(item["avg_output_chunks"]),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Interview Notes",
            "",
            "- Treat `max_tokens` as the requested generation cap, not guaranteed actual output length.",
            "- The client currently counts non-empty streaming chunks as `output_tokens`; this is token-like but not tokenizer-accurate.",
            "- Rows with a non-null `error` are counted in the Errors column but excluded from latency and throughput averages.",
            "- Use this run to discuss how longer generations increase E2E latency and expose decode-phase throughput limits.",
            "- Do not claim GPU kernel-level decode performance from this Mac + LM Studio run.",
        ]
    )

    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def run_output_len_sweep(
    model: str = "qwen/qwen3-8b",
    output_lengths: list[int] | None = None,
    requests_per_length: int = 5,
    output_dir: str = "local_serving_baseline/results",
    output_prefix: str = "output_len_sweep_day4",
) -> list[dict]:
    if output_lengths is None:
        output_lengths = [64, 128, 256, 512]

    client = LMStudioClient()
    results: list[dict] = []

    os.makedirs(output_dir, exist_ok=True)

    for max_tok in output_lengths:
        for sample_idx in range(requests_per_length):
            print(
                f"[output len sweep] max_tokens={max_tok} "
                f"sample={sample_idx + 1}/{requests_per_length}"
            )
            prompt = build_long_output_prompt(sample_idx=sample_idx)

            record = client.send_single(model=model, prompt=prompt, max_tokens=max_tok)
            d = record.to_dict(concurrency=1, context_length=len(prompt.split()))
            d["sample_idx"] = sample_idx
            results.append(d)

            print(
                f"  TTFT={d['ttft']}s  E2E={d['e2e_latency']}s  "
                f"TPOT={d['tpot']}s  chunks/s={d['tokens_per_second']}  "
                f"output_chunks={d['output_tokens']} error={d['error']}"
            )

    output_path = os.path.join(output_dir, f"{output_prefix}.jsonl")
    summary_path = os.path.join(output_dir, f"{output_prefix}_summary.md")
    write_jsonl(output_path, results)
    write_summary_markdown(summary_path, results, summarize_by_output_length(results))
    print(f"[output len sweep] saved raw results to {output_path}")
    print(f"[output len sweep] saved summary to {summary_path}")

    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local LM Studio output length sweep.")
    parser.add_argument("--model", default="qwen/qwen3-8b")
    parser.add_argument("--lengths", nargs="+", type=int, default=[64, 128, 256, 512])
    parser.add_argument("--requests-per-length", type=int, default=5)
    parser.add_argument("--output-dir", default="local_serving_baseline/results")
    parser.add_argument("--output-prefix", default="output_len_sweep_day4")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_output_len_sweep(
        model=args.model,
        output_lengths=args.lengths,
        requests_per_length=args.requests_per_length,
        output_dir=args.output_dir,
        output_prefix=args.output_prefix,
    )
