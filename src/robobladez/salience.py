"""Salience detection (rm8, P0).

Replace `salient: bool` with typed, evidence-bearing canonical events. A "career
event" is only awarded when a measurable condition is met for a specific agent —
NOT merely because the match was decisive. This prevents both competitors from
accumulating "career-defining" events in every match.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any

# Typed salience event kinds (rm8 detailed review §4).
SALIENCE_KINDS = (
    "UPSET",
    "TITLE_WIN",
    "TITLE_LOSS",
    "STREAK_STARTED",
    "STREAK_BROKEN",
    "COMEBACK",
    "RIVALRY_TURN",
    "SIGNATURE_CONFIRMED",
    "META_INNOVATION",
    "REINCARNATION_BREAKTHROUGH",
)


@dataclass(frozen=True)
class SalienceEvidence:
    """A single, typed, deduplicated career event for one agent."""
    type: str
    agent_id: str
    match_id: str
    metric: str = ""
    before: float = 0.0
    threshold: float = 0.0
    note: str = ""

    def evidence_id(self) -> str:
        """Stable dedup key: a given (type, agent, match) is one event."""
        return f"{self.type}|{self.agent_id}|{self.match_id}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SalienceDetector:
    """Computes salience evidence for a match, per agent.

    Unlike the old `salient=bool(match.winner)`, an ordinary decisive match does
    NOT automatically produce career events. Only measurable conditions do
    (upsets vs. baseline expectation, etc.). It needs match context such as the
    pre-match win probability and recent streaks.
    """
    # P(match win) is estimated from the mechanical baseline win_probability.
    UPSET_THRESHOLD = 0.30

    def detect(self, match: Any, agent_id: str, opponent_id: str,
               win_probability: dict[str, float] | None = None,
               prior_streak: int = 0, opponent_prior_streak: int = 0) -> list[SalienceEvidence]:
        won = match.winner == agent_id
        lost = match.winner == opponent_id
        events: list[SalienceEvidence] = []
        if not (won or lost):
            return events  # draws carry no salience

        wp = (win_probability or {}).get(agent_id)
        # UPSET: the agent won despite being mechanically/statistically unlikely.
        if won and wp is not None and wp < self.UPSET_THRESHOLD:
            events.append(SalienceEvidence(
                type="UPSET", agent_id=agent_id, match_id=match.match_id,
                metric="pre_match_win_probability", before=wp,
                threshold=self.UPSET_THRESHOLD,
                note="agent won against a favorable opponent"))
        # COMEBACK: won after losing the prior round (capped prior streak < 0 means loss).
        if won and prior_streak < 0:
            events.append(SalienceEvidence(
                type="COMEBACK", agent_id=agent_id, match_id=match.match_id,
                metric="prior_streak", before=float(prior_streak), threshold=0.0,
                note="agent reversed a losing streak"))
        # STREAK_BROKEN: agent won, ending the opponent's active win streak.
        if won and opponent_prior_streak >= 2:
            events.append(SalienceEvidence(
                type="STREAK_BROKEN", agent_id=agent_id, match_id=match.match_id,
                metric="opponent_prior_streak", before=float(opponent_prior_streak),
                threshold=2.0, note="ended opponent's streak"))
        return events
