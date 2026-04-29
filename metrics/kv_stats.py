from __future__ import annotations

from dataclasses import dataclass


@dataclass
class KVStats:
    prefix_cache_hits: int = 0
    prefix_cache_lookups: int = 0

    @property
    def hit_rate(self) -> float:
        if self.prefix_cache_lookups == 0:
            return 0.0
        return self.prefix_cache_hits / self.prefix_cache_lookups
