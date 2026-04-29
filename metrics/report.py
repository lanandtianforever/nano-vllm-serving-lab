from __future__ import annotations

import json


def to_json(summary: dict) -> str:
    return json.dumps(summary, indent=2, ensure_ascii=False)
