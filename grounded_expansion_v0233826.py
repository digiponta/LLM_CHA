"""v0.2.33.82.6: transient, provenance-preserving proposition pagination.

Splits only explicit corpus ' / ' separators, never invents new facts.
Truth state comes from caller's existing Truth Gate. No disk writes.
"""
from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class PropositionCursor:
    seen: dict[str, set[str]] = field(default_factory=dict)

    @staticmethod
    def split(answer: str) -> list[str]:
        # Corpus convention: distinct subject statements separated by ' / '.
        # Do not naively split Japanese sentences on punctuation.
        result = []
        for fragment in answer.split(" / "):
            fragment = fragment.strip()
            if fragment and fragment not in result:
                result.append(fragment)
        return result

    def next(self, subject: str, answer: str) -> tuple[str | None, int, int]:
        items = self.split(answer)
        seen = self.seen.setdefault(subject, set())
        for item in items:
            if item not in seen:
                seen.add(item)
                return item, len(seen), len(items)
        return None, len(seen), len(items)

    def reset(self) -> None:
        self.seen.clear()
