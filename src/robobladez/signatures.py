"""Career-level signature detection (rm8, P0).

A signature move is NOT a repeated 5-frame window inside one match. It is a
recurring decisive pattern with statistical support across DISTINCT matches and
(ideally) DISTINCT opponents. Only CONFIRMED signatures count toward structural
Daimon evolution.

The registry is persistent per agent: evidence accumulates across a career, and
a pattern is promoted only when it has support across >=2 distinct matches with
a positive outcome lift.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any

from .model import MatchResult


@dataclass
class SignatureCandidate:
    candidate_id: str
    agent_id: str
    pattern_cluster: list[dict[str, Any]]
    match_ids: list[str] = field(default_factory=list)
    opponent_ids: list[str] = field(default_factory=list)
    occurrences: int = 0
    wins: int = 0
    losses: int = 0
    status: str = "candidate"  # candidate|confirmed|retired

    @property
    def outcome_lift(self) -> float:
        """P(win | pattern) - P(win | no pattern); needs a baseline to be exact.

        As a self-contained proxy we use wins / occurrences. Confirmation also
        requires min_occurrences and distinct-match support.
        """
        return (self.wins / self.occurrences) if self.occurrences else 0.0

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


class SignatureRegistry:
    """Persistent per-agent signature accumulator (rm8).

    Evidence accumulates across matches. A pattern is CONFIRMED only when:
      - occurrences >= min_occurrences (default 2)
      - distinct match_ids >= min_matches (default 2)
      - wins >= 1
    and the confirmation is stable under replay ordering (dedup per match).
    """

    def __init__(self, window: int = 5, min_occurrences: int = 2,
                 min_matches: int = 2, min_opponents: int = 1):
        self.window = window
        self.min_occurrences = min_occurrences
        self.min_matches = min_matches
        self.min_opponents = min_opponents
        self._by_agent: dict[str, dict[tuple, dict]] = {}

    def _counts(self, agent_id: str) -> dict:
        return self._by_agent.setdefault(agent_id, {})

    def register(self, match: MatchResult, blade_id: str, agent_id: str,
                 opponent_id: str) -> None:
        """Accumulate evidence for one match; dedup windows per match."""
        seq = _sequence_for(match, blade_id)
        won = match.winner == blade_id
        counts = self._counts(agent_id)
        for i in range(len(seq) - self.window + 1):
            key = tuple(tuple(int(v) for v in f.values()) for f in seq[i:i + self.window])
            rec = counts.setdefault(key, {
                "occurrences": 0, "wins": 0, "losses": 0,
                "match_ids": set(), "opponent_ids": set(),
            })
            # Count each (match) once regardless of how many windows match,
            # but track total window occurrences separately for lift.
            if match.match_id not in rec["match_ids"]:
                rec["match_ids"].add(match.match_id)
                rec["opponent_ids"].add(opponent_id)
                if won:
                    rec["wins"] += 1
                else:
                    rec["losses"] += 1
            rec["occurrences"] += 1

    def confirmed_signature_ids(self, agent_id: str) -> list[str]:
        """IDs of signatures that meet career-level confirmation thresholds."""
        ids = []
        for pattern, rec in self._counts(agent_id).items():
            if (rec["occurrences"] >= self.min_occurrences
                    and len(rec["match_ids"]) >= self.min_matches
                    and len(rec["opponent_ids"]) >= self.min_opponents
                    and rec["wins"] >= 1):
                ids.append(f"sig-{agent_id}-{hash(pattern) & 0xffff:04x}")
        return ids

    def candidates(self, agent_id: str) -> list[SignatureCandidate]:
        out = []
        for pattern, rec in self._counts(agent_id).items():
            sig_id = f"sig-{agent_id}-{hash(pattern) & 0xffff:04x}"
            confirmed = (rec["occurrences"] >= self.min_occurrences
                         and len(rec["match_ids"]) >= self.min_matches
                         and len(rec["opponent_ids"]) >= self.min_opponents
                         and rec["wins"] >= 1)
            out.append(SignatureCandidate(
                candidate_id=sig_id,
                agent_id=agent_id,
                pattern_cluster=[{
                    "radial": f[0], "tangential": f[1], "torque": f[2],
                    "boost": f[3], "speed": f[4], "spin": f[5],
                } for f in pattern],
                match_ids=sorted(rec["match_ids"]),
                opponent_ids=sorted(rec["opponent_ids"]),
                occurrences=rec["occurrences"],
                wins=rec["wins"],
                losses=rec["losses"],
                status="confirmed" if confirmed else "candidate",
            ))
        out.sort(key=lambda c: (c.wins, c.occurrences), reverse=True)
        return out[:12]
