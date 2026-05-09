# Day 3 Context Sweep Summary

This summary is generated from the raw JSONL file produced by
`local_serving_baseline/run_context_sweep.py`.

Total requests: 20

| Context label | Requests | Errors | Avg prompt words | Avg TTFT (s) | P50 TTFT (s) | P95 TTFT (s) | Avg E2E (s) | P95 E2E (s) | Avg TPOT (s) | Avg tokens/s | Avg output chunks |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1024 | 5 | 0 | 589.0000 | 0.6065 | 0.5263 | 0.8801 | 2.9939 | 3.2553 | 0.0398 | 25.1360 | 61.0000 |
| 2048 | 5 | 0 | 1152.0000 | 1.3980 | 1.5844 | 1.6532 | 3.8541 | 4.1369 | 0.0405 | 24.6780 | 61.6000 |
| 4096 | 5 | 0 | 2278.0000 | 3.2048 | 3.2227 | 3.3010 | 5.8204 | 6.0234 | 0.0430 | 23.2740 | 61.8000 |
| 8192 | 5 | 0 | 2926.0000 | 2.8267 | 2.8293 | 3.0642 | 5.7251 | 6.2098 | 0.0480 | 20.9760 | 61.4000 |

## Interview Notes

- Treat `context_length` as the configured experiment label; `prompt_len_estimate` is word-count based, not tokenizer-accurate.
- Long prompts may be capped by `--max-prompt-words` to avoid exceeding the loaded LM Studio context window.
- Use this run to discuss how longer prompts increase prefill pressure and TTFT in a black-box local serving setup.
- Do not claim vLLM PagedAttention or GPU-side KV cache behavior from this Mac + LM Studio run.
