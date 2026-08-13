"""Significance detection (rmdev2 Phase 8).

Don't render every event. A SignificanceDetector selects which canonical events
matter and emits beats that REFERENCE canonical event IDs (they never substitute
for them). The story may interpret events; it may not invent them.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any

from .canonical import CanonicalEvent

BEAT_FUNCTIONS = {
    "OPENING": 0.5,
    "MAJOR_COLLISION": 0.85,
    "LEAD_CHANGE": 0.9,
    "NEAR_RING_OUT": 0.8,
    "DECISIVE_COLLISION": 0.96,
    "ROUND_RESULT": 0.7,
    "MATCH_RESULT": 1.0,
    "STRATEGY_REVEAL": 0.75,
}


@dataclass
class StoryBeat:
    beat_id: str
    type: str
    basis_event_ids: list[str] = field(default_factory=list)
    importance: float = 0.0
    story_function: str = ""
    allowed_interpretation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SignificanceDetector:
    """Maps canonical events -> significant story beats (deterministic)."""

    def __init__(self):
        self._beat_index = 0

    def detect(self, events: list[CanonicalEvent]) -> list[StoryBeat]:
        beats: list[StoryBeat] = []
        # Index events per round.
        by_round: dict[int, list[CanonicalEvent]] = {}
        for e in events:
            by_round.setdefault(e.round, []).append(e)

        for rnd in sorted(by_round):
            round_events = sorted(by_round[rnd], key=lambda e: e.tick)
            # ROUND_RESULT for the round's final event.
            round_end = [e for e in round_events if e.type == "ROUND_ENDED"]
            # Major/decisive collisions.
            collisions = [e for e in round_events if e.type == "COLLISION"]
            if collisions:
                # Heuristic: the highest-impulse collision is the decisive one.
                decisive = max(collisions, key=lambda e: _impulse(e))
                if _impulse(decisive) > 0.6:
                    beats.append(self._beat("DECISIVE_COLLISION", [decisive.event_id]))
                for c in collisions[:1]:
                    beats.append(self._beat("MAJOR_COLLISION", [c.event_id]))
            for e in round_events:
                if e.type == "RING_OUT":
                    beats.append(self._beat("NEAR_RING_OUT", [e.event_id]))
                elif e.type == "SPIN_OUT":
                    beats.append(self._beat("NEAR_RING_OUT", [e.event_id]))
            if round_end:
                beats.append(self._beat("ROUND_RESULT", [round_end[-1].event_id]))

        # MATCH_RESULT from the final ROUND_ENDED.
        if events:
            last = max(events, key=lambda e: e.tick)
            beats.append(self._beat("MATCH_RESULT", [last.event_id]))
        return beats

    def _beat(self, kind: str, event_ids: list[str]) -> StoryBeat:
        self._beat_index += 1
        return StoryBeat(
            beat_id=f"b{self._beat_index:02d}",
            type=kind,
            basis_event_ids=event_ids,
            importance=BEAT_FUNCTIONS.get(kind, 0.5),
            story_function=kind.lower().replace("_", " "),
            allowed_interpretation=("The story may interpret these canonical events; "
                                    "it may not invent events or reverse outcomes."),
        )


def _impulse(e: CanonicalEvent) -> float:
    return float(e.payload.get("total_impulse", e.payload.get("impulse", 0.0)) or 0.0)
