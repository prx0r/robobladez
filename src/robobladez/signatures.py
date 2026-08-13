from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any

from .model import MatchResult


@dataclass
class Signature:
    name: str
    pattern: list[dict[str, Any]]
    hit_count: int = 0
    win_count: int = 0
    match_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _sequence_for(match: MatchResult, blade_id: str) -> list[dict[str, Any]]:
    seq: list[dict[str, Any]] = []
    for rnd in match.rounds:
        for frame in rnd.frames:
            if blade_id not in frame.actions:
                continue
            a = frame.actions[blade_id]
            s = frame.states[blade_id]
            vx, vy = s["vel"]["x"], s["vel"]["y"]
            px, py = s["pos"]["x"], s["pos"]["y"]
            seq.append({
                "radial": 1 if a["radial"] > 0.5 else (-1 if a["radial"] < -0.5 else 0),
                "tangential": 1 if a["tangential"] > 0.5 else (-1 if a["tangential"] < -0.5 else 0),
                "torque": 1 if a["torque"] > 0.5 else (-1 if a["torque"] < -0.5 else 0),
                "boost": 1 if a["boost"] > 0.5 else 0,
                "speed": 1 if (vx * vx + vy * vy) ** 0.5 > 0.5 else 0,
                "spin": 1 if abs(s["omega"]) > 260 else 0,
            })
    return seq


class SignatureDetector:
    """Detect signature moves from recurring decisive patterns.

    A signature is only declared after the same windowed action/state pattern
    repeatedly precedes a win. This is measured from replay, never preauthored.
    Naming / lore is a downstream concern (BUILD_NEXT stage 6).
    """

    def __init__(self, window: int = 5, min_occurrences: int = 2):
        self.window = window
        self.min_occurrences = min_occurrences
        self._counts: dict[tuple, dict] = {}

    def register(self, match: MatchResult, blade_id: str) -> None:
        seq = _sequence_for(match, blade_id)
        won = match.winner == blade_id
        for i in range(len(seq) - self.window + 1):
            key = tuple(tuple(int(v) for v in f.values()) for f in seq[i:i + self.window])
            if key not in self._counts:
                self._counts[key] = {"occurrences": 0, "wins": 0, "match_ids": []}
            self._counts[key]["occurrences"] += 1
            if won:
                self._counts[key]["wins"] += 1
                if match.match_id not in self._counts[key]["match_ids"]:
                    self._counts[key]["match_ids"].append(match.match_id)

    def signatures(self) -> list[Signature]:
        found: list[Signature] = []
        for pattern, stats in self._counts.items():
            if stats["occurrences"] >= self.min_occurrences and stats["wins"] >= 1:
                found.append(Signature(
                    name=f"sig-{len(found)+1}",
                    pattern=[{
                        "radial": f[0], "tangential": f[1], "torque": f[2],
                        "boost": f[3], "speed": f[4], "spin": f[5],
                    } for f in pattern],
                    hit_count=stats["occurrences"],
                    win_count=stats["wins"],
                    match_ids=stats["match_ids"],
                ))
        found.sort(key=lambda s: (s.win_count, s.hit_count), reverse=True)
        return found[:12]
