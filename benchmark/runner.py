from __future__ import annotations

from copy import deepcopy

from benchmark.workload_generator import make_mixed_workload
from metrics.recorder import RequestMetrics, summarize_requests
from metrics.report import to_json
from scheduler.base import Request
from scheduler.decode_priority import DecodePriorityScheduler
from scheduler.fcfs import FCFSScheduler

PREFILL_COST_PER_TOKEN_MS = 1
DECODE_COST_PER_TOKEN_MS = 4


def run_simulation(requests: list[Request], scheduler) -> dict:
    now_ms = 0
    metrics: list[RequestMetrics] = []

    while True:
        active = [request for request in requests if request.state != "finished"]
        if not active:
            break

        visible = [request for request in active if request.arrival_ts_ms <= now_ms]
        if not visible:
            now_ms = min(request.arrival_ts_ms for request in active)
            continue

        decision = scheduler.schedule(visible, now_ms)
        if decision.kind == "idle" or decision.request_id is None:
            now_ms += 1
            continue

        chosen = next(request for request in requests if request.request_id == decision.request_id)
        if chosen.first_scheduled_ts_ms is None:
            chosen.first_scheduled_ts_ms = now_ms

        if decision.kind == "prefill":
            now_ms += chosen.prompt_tokens * PREFILL_COST_PER_TOKEN_MS
            chosen.state = "decoding"
            continue

        now_ms += DECODE_COST_PER_TOKEN_MS
        chosen.generated_tokens += 1
        if chosen.generated_tokens >= chosen.output_tokens:
            chosen.state = "finished"
            chosen.finished_ts_ms = now_ms
            metrics.append(
                RequestMetrics(
                    request_id=chosen.request_id,
                    arrival_ts_ms=chosen.arrival_ts_ms,
                    first_scheduled_ts_ms=chosen.first_scheduled_ts_ms or chosen.arrival_ts_ms,
                    finished_ts_ms=chosen.finished_ts_ms,
                    output_tokens=chosen.output_tokens,
                    slo_ms=chosen.slo_ms,
                )
            )

    return summarize_requests(metrics)


def main() -> None:
    baseline_workload = make_mixed_workload()
    fcfs_summary = run_simulation(deepcopy(baseline_workload), FCFSScheduler())
    decode_summary = run_simulation(deepcopy(baseline_workload), DecodePriorityScheduler())
    print("=== FCFS ===")
    print(to_json(fcfs_summary))
    print("=== Decode Priority ===")
    print(to_json(decode_summary))


if __name__ == "__main__":
    main()
