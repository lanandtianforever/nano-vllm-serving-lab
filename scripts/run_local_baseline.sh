#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
from local_serving_baseline.collect_metrics import collect_single_prompt

result = collect_single_prompt(
    model="qwen/qwen3-8b",
    prompt="Say hello and describe TTFT in one sentence.",
)
print(result)
PY
