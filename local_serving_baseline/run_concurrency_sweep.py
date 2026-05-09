"""
Experiment B: Concurrency Sweep.
Sends N identical prompts concurrently and measures tail latency behaviour.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from collections import defaultdict
from typing import Iterable

from local_serving_baseline.lmstudio_client import LMStudioClient, generate_short_prompt


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


def summarize_by_concurrency(rows: list[dict]) -> list[dict]:
    grouped: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[int(row["concurrency"])].append(row)

    summaries: list[dict] = []
    for level in sorted(grouped):
        group = grouped[level]

        def values(field: str) -> list[float]:
            return [row[field] for row in group if row.get(field) is not None]

        def avg(field: str) -> float | None:
            vals = values(field)
            if not vals:
                return None
            return sum(vals) / len(vals)

        summaries.append(
            {
                "concurrency": level,
                "num_requests": len(group),
                "num_errors": sum(1 for row in group if row.get("error")),
                "avg_ttft": avg("ttft"),
                "p50_ttft": percentile(values("ttft"), 0.50),
                "p95_ttft": percentile(values("ttft"), 0.95),
                "p99_ttft": percentile(values("ttft"), 0.99),
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
        "# Day 2 Concurrency Sweep Summary",
        "",
        "This summary is generated from the raw JSONL file produced by",
        "`local_serving_baseline/run_concurrency_sweep.py`.",
        "",
        f"Total requests: {len(rows)}",
        "",
        "| Concurrency | Requests | Errors | Avg TTFT (s) | P50 TTFT (s) | P95 TTFT (s) | P99 TTFT (s) | Avg E2E (s) | P95 E2E (s) | Avg TPOT (s) | Avg tokens/s | Avg output chunks |",
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
                    fmt(item["concurrency"]),
                    fmt(item["num_requests"]),
                    fmt(item["num_errors"]),
                    fmt(item["avg_ttft"]),
                    fmt(item["p50_ttft"]),
                    fmt(item["p95_ttft"]),
                    fmt(item["p99_ttft"]),
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
            "- Treat this as a MacBook Air M5 + LM Studio black-box serving baseline, not a vLLM benchmark.",
            "- Use the trend to discuss concurrency pressure, queueing, TTFT, TPOT, and tail latency.",
            "- Do not claim production serving performance from this local run.",
        ]
    )

    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def run_concurrency_sweep(
    model: str = "qwen/qwen3-8b",
    concurrency_levels: list[int] | None = None,
    max_tokens: int = 128,
    requests_per_level: int = 10,
    output_dir: str = "local_serving_baseline/results",
    output_prefix: str = "concurrency_sweep_day2",
) -> list[dict]:
    if concurrency_levels is None:
        concurrency_levels = [1, 2, 4, 8]

    client = LMStudioClient()
    all_results: list[dict] = []

    os.makedirs(output_dir, exist_ok=True)

    for level in concurrency_levels:
        print(f"[concurrency sweep] concurrency={level} requests={requests_per_level}")
        prompts = [generate_short_prompt() for _ in range(requests_per_level)]

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

    output_path = os.path.join(output_dir, f"{output_prefix}.jsonl")
    summary_path = os.path.join(output_dir, f"{output_prefix}_summary.md")
    write_jsonl(output_path, all_results)
    write_summary_markdown(summary_path, all_results, summarize_by_concurrency(all_results))
    print(f"[concurrency sweep] saved raw results to {output_path}")
    print(f"[concurrency sweep] saved summary to {summary_path}")

    return all_results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local LM Studio concurrency sweep.")
    parser.add_argument("--model", default="qwen/qwen3-8b")
    parser.add_argument("--levels", nargs="+", type=int, default=[1, 2, 4, 8])
    parser.add_argument("--max-tokens", type=int, default=128)
    parser.add_argument("--requests-per-level", type=int, default=10)
    parser.add_argument("--output-dir", default="local_serving_baseline/results")
    parser.add_argument("--output-prefix", default="concurrency_sweep_day2")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_concurrency_sweep(
        model=args.model,
        concurrency_levels=args.levels,
        max_tokens=args.max_tokens,
        requests_per_level=args.requests_per_level,
        output_dir=args.output_dir,
        output_prefix=args.output_prefix,
    )
