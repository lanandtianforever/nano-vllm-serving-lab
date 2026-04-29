from __future__ import annotations

import unittest

from scheduler.base import Request
from scheduler.decode_priority import DecodePriorityScheduler
from scheduler.fcfs import FCFSScheduler


class SchedulerTests(unittest.TestCase):
    def test_fcfs_picks_earliest_arrival(self) -> None:
        requests = [
            Request("late", arrival_ts_ms=10, prompt_tokens=128, output_tokens=16),
            Request("early", arrival_ts_ms=0, prompt_tokens=128, output_tokens=16),
        ]
        decision = FCFSScheduler().schedule(requests, now_ms=10)
        self.assertEqual(decision.request_id, "early")
        self.assertEqual(decision.kind, "prefill")

    def test_decode_priority_prefers_decode_ready_request(self) -> None:
        requests = [
            Request("prefill", arrival_ts_ms=0, prompt_tokens=4096, output_tokens=64, state="waiting_prefill"),
            Request("decode", arrival_ts_ms=1, prompt_tokens=128, output_tokens=64, state="decoding", generated_tokens=5),
        ]
        decision = DecodePriorityScheduler().schedule(requests, now_ms=5)
        self.assertEqual(decision.request_id, "decode")
        self.assertEqual(decision.kind, "decode")


if __name__ == "__main__":
    unittest.main()
