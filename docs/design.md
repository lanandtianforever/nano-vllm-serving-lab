# Design Notes

## What this scaffold optimizes for

- easy to extend
- interviewable
- deterministic tests
- small enough to refactor quickly

## First implementation choices

- Use Python stdlib only.
- Keep the scheduler contract minimal.
- Separate workload generation, scheduling, and metrics from the start.
- Simulate time in milliseconds and progress in tokens.

## What is intentionally deferred

- exact nano-vLLM queue internals
- paged KV cache allocator behavior
- true chunked prefill
- prefix cache block accounting
- real benchmark replay from production traces
