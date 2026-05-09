# Week 1 Summary

Week 1 turned the local serving baseline from a scaffold into a reproducible,
documented measurement layer. The goal was not to prove vLLM performance. The
goal was to build reliable serving-metric intuition before moving into vLLM
reading and white-box scheduler work.

## What Was Built

- A streaming LM Studio client for OpenAI-compatible chat completions.
- Localhost proxy bypass for clean local benchmark traffic.
- Three reproducible sweep scripts:
  - concurrency sweep
  - context-length sweep
  - output-length sweep
- JSONL raw result files for each sweep.
- Markdown summary files for each sweep.
- Dependency-free SVG chart generation.
- A formal local baseline report.
- A Chinese interview Q&A file that tracks likely follow-up questions and safe
  answers.

## Experiment Summary

### Concurrency Sweep

The concurrency sweep used 10 requests per level for concurrency 1, 2, 4, and 8.

Main observation:

- Concurrency 1 and 2 were close in E2E latency.
- Concurrency 4 increased E2E and TPOT.
- Concurrency 8 significantly worsened E2E latency and chunk-level TPOT.

Interview-safe conclusion:

> The MacBook Air M5 + LM Studio baseline shows that serving quality degrades
> under higher concurrency. This is a local black-box saturation signal, not a
> vLLM capacity claim.

### Context Sweep

The context sweep used context labels 1024, 2048, 4096, and 8192 with five
requests per label.

Main observation:

- TTFT increased clearly from the 1024 label to the 4096 label.
- The 8192 row required prompt word capping to avoid exceeding the loaded LM
  Studio context window.

Interview-safe conclusion:

> Longer prompts increase prefill pressure and TTFT, but benchmark prompt
> length must be stated carefully because context label, word count, and
> tokenizer token count are different.

### Output Length Sweep

The output sweep used a long-output prompt and max token caps 64, 128, 256, and
512.

Main observation:

- The prompt successfully pushed 128/256/512 settings close to the requested
  generation cap.
- TTFT stayed mostly stable from 128 to 512.
- E2E latency grew with output length.
- The 512 setting showed worse chunk-level TPOT.

Interview-safe conclusion:

> With a fixed prompt, longer outputs mainly add decode steps, so E2E latency
> grows while TTFT remains relatively stable.

## Key Lessons

1. Local black-box measurements are useful for building metric intuition, but
   they must not be presented as vLLM performance numbers.
2. Error rows should be counted separately from successful-request latency
   summaries.
3. Word count is not tokenizer token count.
4. E2E latency and TPOT can have very different scales, so charting them in
   separate panels makes trends clearer.
5. The Week 1 baseline gives a concrete metric vocabulary for the upcoming
   scheduler and vLLM contribution work.

## Current Artifacts

- `docs/local_serving_baseline.md`
- `docs/interview_qna.md`
- `analysis/plot_local_baseline.py`
- `analysis/figures/local_concurrency_e2e_tpot.svg`
- `analysis/figures/local_context_ttft.svg`
- `analysis/figures/local_output_e2e_tpot.svg`
- `local_serving_baseline/results/concurrency_sweep_day2.jsonl`
- `local_serving_baseline/results/context_sweep_day3.jsonl`
- `local_serving_baseline/results/output_len_sweep_day4.jsonl`

## Week 2 Direction

Week 2 should shift from local measurement to vLLM alignment:

1. Read vLLM contribution docs and local development workflow.
2. Read vLLM benchmark sweep docs and scripts.
3. Read prefix caching and chunked prefill docs/code paths.
4. Identify a small vLLM PR candidate.
5. Keep extending the scheduler lab toward chunked prefill and prefix-aware
   scheduling.

