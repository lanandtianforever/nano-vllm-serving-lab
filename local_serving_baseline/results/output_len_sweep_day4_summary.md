# Day 4 Output Length Sweep Summary

This summary is generated from the raw JSONL file produced by
`local_serving_baseline/run_output_len_sweep.py`.

Total requests: 20

Latency and throughput metrics below exclude rows with non-null `error`.

| Max tokens | Requests | Errors | Avg TTFT (s) | P50 TTFT (s) | P95 TTFT (s) | Avg E2E (s) | P95 E2E (s) | Avg TPOT (s) | P95 TPOT (s) | Avg chunks/s | Avg output chunks |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 64 | 5 | 1 | 1.2058 | 0.4558 | 3.0255 | 3.3796 | 5.1433 | 0.0367 | 0.0376 | 27.2725 | 60.2500 |
| 128 | 5 | 0 | 0.3582 | 0.3343 | 0.4397 | 5.0058 | 5.1101 | 0.0378 | 0.0383 | 26.4680 | 124.0000 |
| 256 | 5 | 0 | 0.3585 | 0.3452 | 0.3930 | 9.9449 | 10.0601 | 0.0383 | 0.0386 | 26.0800 | 251.0000 |
| 512 | 5 | 0 | 0.3511 | 0.3457 | 0.3825 | 24.5394 | 28.7197 | 0.0484 | 0.0566 | 21.1320 | 500.6000 |

## Interview Notes

- Treat `max_tokens` as the requested generation cap, not guaranteed actual output length.
- The client currently counts non-empty streaming chunks as `output_tokens`; this is token-like but not tokenizer-accurate.
- Rows with a non-null `error` are counted in the Errors column but excluded from latency and throughput averages.
- Use this run to discuss how longer generations increase E2E latency and expose decode-phase throughput limits.
- Do not claim GPU kernel-level decode performance from this Mac + LM Studio run.
