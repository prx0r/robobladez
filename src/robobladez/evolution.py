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


def reflect(match: Any, self_id: str, opponent_id: str) -> PostMatchReflection:
    won = match.winner == self_id
    self_collisions = _count_events(match, self_id, "collision")
    opp_collisions = _count_events(match, opponent_id, "collision")

    what_worked: list[str] = []
    what_failed: list[str] = []
    if won:
        what_worked.append("won the match across the sealed-policy rounds")
    else:
        what_failed.append("failed to convert play into a match win")
    if self_collisions > opp_collisions:
        what_worked.append("won the contact/impulse trade")
    else:
        what_failed.append("lost the contact/impulse trade")

    beliefs = [
        f"opponent triggered {opp_collisions} collisions (contact-aggression model)",
    ]
    experiments: list[str] = []
    if not won and opp_collisions > self_collisions:
        experiments.append("test a counter that punishes opponent contact")

    return PostMatchReflection(
        agent_id=self_id,
        opponent_id=opponent_id,
        result=match.winner,
        what_worked=what_worked,
        what_failed=what_failed,
        beliefs=beliefs,
        proposed_experiments=experiments,
    )
