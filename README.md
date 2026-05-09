# nano-vLLM Serving Lab

An execution-focused LLM serving lab for moving from local black-box
measurements into white-box scheduler and KV cache reasoning.

The project has two layers:

1. `local_serving_baseline/`
   Measures a MacBook Air M5 + LM Studio OpenAI-compatible streaming endpoint.
2. `scheduler/`, `benchmark/`, `metrics/`
   Builds a lightweight nano-vLLM-style scheduler simulation harness for
   prefill/decode scheduling trade-offs, tail latency, throughput, and goodput.

## Project Stance

The local model is not the main project.

The local model provides a black-box serving baseline for:

- TTFT
- TPOT
- E2E latency
- chunks/s
- P95 / P99
- error accounting

The main project value is the white-box path: scheduler design, workload
construction, KV cache reasoning, prefix-cache-aware scheduling, and
vLLM-aligned benchmark / documentation contributions.

## Week 1 Results

Week 1 focused on making the local baseline measurable, reproducible, and
interview-safe.

### Concurrency Pressure

MacBook Air M5 + LM Studio, `qwen/qwen3-8b`, 10 requests per concurrency level:

| Concurrency | Avg E2E (s) | P95 E2E (s) | Avg TPOT (s/chunk) |
|---:|---:|---:|---:|
| 1 | 5.5741 | 6.0311 | 0.0414 |
| 2 | 5.5265 | 5.7884 | 0.0393 |
| 4 | 8.8363 | 9.8870 | 0.0641 |
| 8 | 16.2634 | 19.2307 | 0.1192 |

![Concurrency sweep](analysis/figures/local_concurrency_e2e_tpot.svg)

### Context / Prefill Pressure

Context labels are experimental labels; prompt length is currently word-count
based, not tokenizer-accurate.

| Context label | Avg prompt words | Avg TTFT (s) | P95 TTFT (s) |
|---:|---:|---:|---:|
| 1024 | 589 | 0.6065 | 0.8801 |
| 2048 | 1152 | 1.3980 | 1.6532 |
| 4096 | 2278 | 3.2048 | 3.3010 |
| 8192 | 2926 | 2.8267 | 3.0642 |

![Context sweep](analysis/figures/local_context_ttft.svg)

### Output / Decode Pressure

Rows with non-null `error` are counted separately and excluded from latency and
throughput averages.

| Max tokens | Errors | Avg E2E (s) | Avg TPOT (s/chunk) | Avg output chunks |
|---:|---:|---:|---:|---:|
| 64 | 1 | 3.3796 | 0.0367 | 60.25 |
| 128 | 0 | 5.0058 | 0.0378 | 124.00 |
| 256 | 0 | 9.9449 | 0.0383 | 251.00 |
| 512 | 0 | 24.5394 | 0.0484 | 500.60 |

![Output length sweep](analysis/figures/local_output_e2e_tpot.svg)

## Documentation

- [Local serving baseline](docs/local_serving_baseline.md)
- [Week 1 summary](docs/week1_summary.md)
- [Architecture notes](docs/architecture.md)
- [Scheduler lab notes](docs/nano_vllm_scheduler.md)
- [Interview Q&A in Chinese](docs/interview_qna.md)
- [Development log](docs/dev_log.md)

## Quick Start

Run tests:

```bash
python3 -m unittest discover -s tests
```

Run the scheduler simulation demo:

```bash
python3 -m benchmark.runner
```

Generate local baseline figures from JSONL results:

```bash
python3 analysis/plot_local_baseline.py
```

## Reproducing Local Baseline Runs

Start LM Studio server and load the model, for example:

```bash
lms server start -p 1234 --bind 127.0.0.1
lms load qwen/qwen3-8b --identifier 'qwen/qwen3-8b' --context-length 4096 --parallel 1 -y
```

Run the three sweeps:

```bash
python3 -m local_serving_baseline.run_concurrency_sweep \
  --levels 1 2 4 8 \
  --requests-per-level 10 \
  --max-tokens 128 \
  --output-prefix concurrency_sweep_day2

python3 -m local_serving_baseline.run_context_sweep \
  --lengths 1024 2048 4096 8192 \
  --requests-per-length 5 \
  --max-tokens 64 \
  --output-prefix context_sweep_day3

python3 -m local_serving_baseline.run_output_len_sweep \
  --lengths 64 128 256 512 \
  --requests-per-length 5 \
  --output-prefix output_len_sweep_day4
```

## Current Limitations

- The local baseline is LM Studio / MLX, not vLLM.
- `output_tokens` currently counts non-empty streaming chunks, not
  tokenizer-accurate tokens.
- Prompt length is currently word-count based.
- The scheduler lab is a simulator and does not yet model full vLLM batching,
  PagedAttention, real KV block allocation, or CUDA execution.

## Next Milestones

- Add tokenizer-accurate prompt and output token counting.
- Read vLLM benchmark, prefix caching, and chunked prefill documentation/code.
- Identify a small vLLM PR around benchmark examples, prefix caching docs,
  error messages, or tests.
- Extend the scheduler lab with chunked prefill and prefix-aware scheduling.

