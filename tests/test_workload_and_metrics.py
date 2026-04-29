from __future__ import annotations

import unittest

from benchmark.runner import run_simulation
from benchmark.workload_generator import make_mixed_workload
from scheduler.decode_priority import DecodePriorityScheduler
from scheduler.fcfs import FCFSScheduler


class WorkloadAndMetricsTests(unittest.TestCase):
    def test_workload_generator_returns_requests(self) -> None:
        workload = make_mixed_workload()
        self.assertGreaterEqual(len(workload), 4)
        self.assertTrue(all(request.request_id for request in workload))

    def test_runner_returns_summary(self) -> None:
        summary = run_simulation(make_mixed_workload(), FCFSScheduler())
        self.assertEqual(summary["num_requests"], 4)
        self.assertIn("p95_e2e_latency_ms", summary)

    def test_policies_can_diverge(self) -> None:
        fcfs = run_simulation(make_mixed_workload(), FCFSScheduler())
        decode = run_simulation(make_mixed_workload(), DecodePriorityScheduler())
        self.assertNotEqual(fcfs["p95_e2e_latency_ms"], decode["p95_e2e_latency_ms"])


if __name__ == "__main__":
    unittest.main()
