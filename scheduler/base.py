from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional


@dataclass
class Request:
    request_id: str
    arrival_ts_ms: int
    prompt_tokens: int
    output_tokens: int
    prefix_id: Optional[str] = None
    slo_ms: Optional[int] = None
    generated_tokens: int = 0
    state: str = "waiting_prefill"
    first_scheduled_ts_ms: Optional[int] = None
    finished_ts_ms: Optional[int] = None

    @property
    def done(self) -> bool:
        return self.state == "finished"

    @property
    def decode_ready(self) -> bool:
        return self.state == "decoding" and self.generated_tokens < self.output_tokens

    @property
    def waiting_prefill(self) -> bool:
        return self.state == "waiting_prefill"

    @property
    def remaining_output_tokens(self) -> int:
        return max(0, self.output_tokens - self.generated_tokens)


@dataclass
class ScheduleDecision:
    kind: str
    request_id: Optional[str]
    reason: str


class BaseScheduler:
    name = "base"

    def schedule(self, requests: Iterable[Request], now_ms: int) -> ScheduleDecision:
        raise NotImplementedError

    @staticmethod
    def _active_requests(requests: Iterable[Request]) -> List[Request]:
        return [request for request in requests if not request.done]
