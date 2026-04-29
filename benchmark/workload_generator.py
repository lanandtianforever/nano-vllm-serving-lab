from __future__ import annotations

from scheduler.base import Request


def make_mixed_workload() -> list[Request]:
    return [
        Request("req-long-1", arrival_ts_ms=0, prompt_tokens=8192, output_tokens=256, prefix_id="doc", slo_ms=12000),
        Request("req-short-1", arrival_ts_ms=5, prompt_tokens=128, output_tokens=48, prefix_id="chat", slo_ms=1500),
        Request("req-short-2", arrival_ts_ms=10, prompt_tokens=128, output_tokens=48, prefix_id="chat", slo_ms=1500),
        Request("req-mid-1", arrival_ts_ms=20, prompt_tokens=2048, output_tokens=128, prefix_id="task", slo_ms=5000),
    ]
