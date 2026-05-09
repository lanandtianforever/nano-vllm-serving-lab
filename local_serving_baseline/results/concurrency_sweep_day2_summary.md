# Day 2 Concurrency Sweep Summary

This summary is generated from the raw JSONL file produced by
`local_serving_baseline/run_concurrency_sweep.py`.

Total requests: 40

| Concurrency | Requests | Errors | Avg TTFT (s) | P50 TTFT (s) | P95 TTFT (s) | P99 TTFT (s) | Avg E2E (s) | P95 E2E (s) | Avg TPOT (s) | Avg tokens/s | Avg output chunks |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 10 | 0 | 0.4336 | 0.3685 | 0.7340 | 0.9498 | 5.5741 | 6.0311 | 0.0414 | 24.2240 | 125.3000 |
| 2 | 10 | 0 | 0.6253 | 0.5875 | 0.8706 | 0.9036 | 5.5265 | 5.7884 | 0.0393 | 25.4310 | 125.6000 |
| 4 | 10 | 0 | 0.9635 | 0.8358 | 1.4425 | 1.4676 | 8.8363 | 9.8870 | 0.0641 | 16.2080 | 124.1000 |
| 8 | 10 | 0 | 1.5414 | 1.5558 | 2.4780 | 2.5364 | 16.2634 | 19.2307 | 0.1192 | 10.0250 | 124.7000 |

## Interview Notes

- Treat this as a MacBook Air M5 + LM Studio black-box serving baseline, not a vLLM benchmark.
- Use the trend to discuss concurrency pressure, queueing, TTFT, TPOT, and tail latency.
- Do not claim production serving performance from this local run.
