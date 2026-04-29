# Local Serving Baseline

The local baseline exists to establish serving intuition before the white-box scheduler work.

## Endpoint

LM Studio Anthropic-compatible endpoint:

```text
POST /v1/messages
```

## Goal

Collect:

- TTFT
- TPOT
- E2E latency
- tokens/s
- P95 / P99

## Non-goals

- proving local models are stronger than GPT-5.5 or DeepSeek-V4
- turning the local model into the main project artifact
