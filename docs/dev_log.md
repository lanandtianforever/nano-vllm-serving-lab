# Dev Log

## 2026-04-29

- Created the initial project scaffold.
- Added a scheduler abstraction.
- Added FCFS and decode-priority policies.
- Added a synthetic simulation harness for request lifecycle experiments.
- Added a minimal LM Studio client for local black-box baseline measurements.

## 2026-05-09

- Day 1: Added a local-only current status note to separate defensible project
  claims from experiments that still need stronger evidence.
- Day 2: Started LM Studio local server on `127.0.0.1:1234` and loaded
  `qwen/qwen3-8b` with context length 4096 and parallelism 8.
- Updated the LM Studio client to bypass system HTTP proxies for localhost
  requests, avoiding accidental proxy `502 Bad Gateway` responses.
- Re-ran the MacBook Air M5 concurrency sweep with 10 requests per concurrency
  level for levels 1, 2, 4, and 8.
- Saved Day 2 raw results to
  `local_serving_baseline/results/concurrency_sweep_day2.jsonl`.
- Saved Day 2 summary table to
  `local_serving_baseline/results/concurrency_sweep_day2_summary.md`.
- Day 3: Reworked context sweep to generate stronger deterministic long
  prompts, repeat each context label five times, and emit both raw JSONL and a
  Markdown summary.
- Loaded `qwen/qwen3-8b` with context length 8192 and parallelism 1 for the
  context-length experiment.
- Found that an 8192-label prompt with about 3712 words exceeded the loaded
  context window after tokenizer expansion, so the script now caps prompt word
  count with `--max-prompt-words`.
- Re-ran context labels 1024, 2048, 4096, and 8192 with five requests each and
  zero request errors.
- Interpreted the 8192 row carefully: the prompt was capped at about 2926 words,
  so it is a high-context local baseline point rather than a tokenizer-accurate
  8192-token prompt.
- Saved Day 3 raw results to
  `local_serving_baseline/results/context_sweep_day3.jsonl`.
- Saved Day 3 summary table to
  `local_serving_baseline/results/context_sweep_day3_summary.md`.
- Day 4: Reworked output length sweep to use a long-output prompt that asks the
  model to continue until the API stops it.
- Added CLI options and Markdown summary output for the output-length sweep.
- Ran `max_tokens` values 64, 128, 256, and 512 with five requests each.
- Observed one non-null LM Studio error in the 64-token group; the summary
  counts it as an error and excludes error rows from latency and throughput
  averages.
- Saved Day 4 raw results to
  `local_serving_baseline/results/output_len_sweep_day4.jsonl`.
- Saved Day 4 summary table to
  `local_serving_baseline/results/output_len_sweep_day4_summary.md`.
- Added `docs/interview_qna.md` to collect likely interview follow-up questions
  and project-specific safe answers as the project evolves.
- Day 5: Rewrote `docs/local_serving_baseline.md` into a formal local serving
  baseline report covering environment, commands, Day 2/3/4 result tables,
  safe interpretations, and limitations.
- Converted `docs/interview_qna.md` into Chinese and added Day 5 questions about
  why the local baseline is documented separately and how the three local
  experiments connect to later scheduler work.
- Day 6: Added `analysis/plot_local_baseline.py`, a dependency-free SVG chart
  generator for the local serving baseline.
- Generated three local baseline figures under `analysis/figures/`: concurrency
  E2E/TPOT, context TTFT, and output length E2E/TPOT.
- Updated `docs/local_serving_baseline.md` to include the generated figures.
- Added Chinese interview Q&A entries for explaining why charts are useful, why
  E2E and TPOT are plotted in separate panels, and how to avoid overclaiming
  from Mac + LM Studio figures.
- Day 7: Rewrote `README.md` around the Week 1 local baseline narrative,
  including result tables, figures, reproduction commands, limitations, and
  next milestones.
- Added `docs/week1_summary.md` to summarize Week 1 deliverables, key lessons,
  and the Week 2 vLLM-alignment direction.
- Added Chinese interview Q&A entries for explaining Week 1 outcomes, why the
  local baseline matters for inference optimization, and how Week 2 will move
  toward vLLM contribution work.
