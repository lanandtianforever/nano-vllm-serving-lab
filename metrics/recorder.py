from __future__ import annotations

from dataclasses import asdict, dataclass

from metrics.latency import percentile


@dataclass
class RequestMetrics:
    request_id: str
    arrival_ts_ms: int
    first_scheduled_ts_ms: int
    finished_ts_ms: int
    output_tokens: int
    slo_ms: int | None

    @property
    def ttft_ms(self) -> int:
        return self.first_scheduled_ts_ms - self.arrival_ts_ms

    @property
    def e2e_latency_ms(self) -> int:
        return self.finished_ts_ms - self.arrival_ts_ms

    @property
    def sla_met(self) -> bool | None:
        if self.slo_ms is None:
            return None
        return self.e2e_latency_ms <= self.slo_ms


def summarize_requests(metrics: list[RequestMetrics]) -> dict:
    e2e = [metric.e2e_latency_ms for metric in metrics]
    ttft = [metric.ttft_ms for metric in metrics]
    sla_candidates = [metric for metric in metrics if metric.sla_met is not None]
    sla_hit_ratio = 0.0
    if sla_candidates:
        sla_hit_ratio = sum(1 for metric in sla_candidates if metric.sla_met) / len(sla_candidates)

    return {
        "num_requests": len(metrics),
        "avg_ttft_ms": sum(ttft) / len(ttft) if ttft else 0.0,
        "p95_ttft_ms": percentile(ttft, 0.95),
        "p99_ttft_ms": percentile(ttft, 0.99),
        "avg_e2e_latency_ms": sum(e2e) / len(e2e) if e2e else 0.0,
        "p95_e2e_latency_ms": percentile(e2e, 0.95),
        "p99_e2e_latency_ms": percentile(e2e, 0.99),
        "sla_hit_ratio": sla_hit_ratio,
        "requests": [asdict(metric) for metric in metrics],
    }
