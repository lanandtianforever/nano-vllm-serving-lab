from __future__ import annotations

from scheduler.base import BaseScheduler, Request, ScheduleDecision


class DecodePriorityScheduler(BaseScheduler):
    name = "decode_priority"

    def schedule(self, requests: list[Request], now_ms: int) -> ScheduleDecision:
        active = self._active_requests(requests)
        if not active:
            return ScheduleDecision(kind="idle", request_id=None, reason="no active requests")

        decode_candidates = [request for request in active if request.decode_ready]
        if decode_candidates:
            chosen = min(decode_candidates, key=lambda request: (request.arrival_ts_ms, request.request_id))
            return ScheduleDecision(
                kind="decode",
                request_id=chosen.request_id,
                reason="prioritize ongoing decode to protect interactive latency",
            )

        prefill_candidates = [request for request in active if request.waiting_prefill]
        chosen = min(prefill_candidates, key=lambda request: (request.arrival_ts_ms, request.request_id))
        return ScheduleDecision(kind="prefill", request_id=chosen.request_id, reason="fallback to earliest prefill")
