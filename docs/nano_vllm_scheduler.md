# nano-vLLM Scheduler Lab

## Initial policies

- FCFS
- Decode-Priority

## Planned next policies

- Chunked Prefill
- Prefix-Aware
- SLO-Aware

## Key questions

1. When does decode-priority improve interactive latency?
2. How much does it hurt long prefill TTFT?
3. Under mixed workloads, when does goodput diverge from raw throughput?
