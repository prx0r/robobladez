from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class PostMatchReflection:
    """A competitor's structured, metric-driven plan for its future self.

    Explicit and non-mystical: what worked, what failed, updated beliefs about
    the opponent, proposed experiments. Between-match evolution creates a new
    version; it never edits a past competitor retrospectively (Constitution 9).
    """
    agent_id: str
    opponent_id: str
    result: str | None
    what_worked: list[str] = field(default_factory=list)
    what_failed: list[str] = field(default_factory=list)
    beliefs: list[str] = field(default_factory=list)
    proposed_experiments: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _count_events(match: Any, agent_id: str, event_type: str) -> int:
    n = 0
    for rnd in match.rounds:
        for ev in rnd.events:
            if ev.type == event_type and ev.actor == agent_id:
                n += 1
    return n
