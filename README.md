# nano-vLLM Serving Lab

An execution-focused lab for the project described in `nano_vllm_serving_lab_project_doc_v2_1.md`.

This repo is split into two layers:

1. `local_serving_baseline/`
   Measure a local LM Studio / MLX model through its OpenAI/Anthropic-compatible API.
2. `scheduler/`, `benchmark/`, `metrics/`
   Build a white-box scheduler simulation harness that lets us reason about request lifecycle,
   prefill/decode trade-offs, tail latency, throughput, and goodput.

## Current scope

This initial scaffold focuses on the main project path:

- a scheduler abstraction
- FCFS and decode-priority policies
- a synthetic workload generator
- a lightweight simulation runner
- latency and goodput metric helpers
- a minimal LM Studio client for the local baseline

It is intentionally small so we can iterate quickly and keep the repo explainable in interviews.

## Layout

```text
nano-vllm-serving-lab/
├── docs/
├── local_serving_baseline/
├── scheduler/
├── benchmark/
├── metrics/
├── workloads/
├── scripts/
└── tests/
```

## Quick start

Run the local tests:

```bash
python3 -m unittest discover -s tests
```

Run the scheduler simulation demo:

```bash
python3 -m benchmark.runner
```

## Project stance

The local model is not the project.

The local model only provides a black-box baseline for:

- TTFT
- TPOT
- E2E latency
- tokens/s
- P95/P99

The core project value is still the white-box scheduler and KV cache reasoning path.
