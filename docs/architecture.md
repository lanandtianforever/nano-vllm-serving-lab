# Architecture

## Two-layer project

### Layer 1: Local Serving Baseline

LM Studio acts as a local black-box serving endpoint.

We care about:

- TTFT
- TPOT
- E2E latency
- tokens/s
- P95 / P99

### Layer 2: Scheduler Simulation and White-box Reasoning

This repo starts with a small scheduler simulator so we can iterate on:

- request lifecycle abstraction
- FCFS baseline
- decode-priority
- future chunked prefill
- future prefix-aware scheduling
- future SLO-aware scheduling

## Current request lifecycle abstraction

Each request moves through:

1. `waiting_prefill`
2. `decoding`
3. `finished`

The simulator does not try to be nano-vLLM-complete yet.
It only models enough state to help us reason about prefill/decode competition and latency trade-offs.
