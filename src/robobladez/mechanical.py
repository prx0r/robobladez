"""Mechanical baseline system (rmdev Phase 2).

For each body-vs-body matchup, run neutral (passive) simulations to reveal the
*mechanical* truth before any strategy is committed. This is what makes a match
about reasoning against known mechanical asymmetry.

The report is deterministic given (bodies, arena, seed, run count) and is given
to both competitors before they commit their sealed strategic policies.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any
import math

from .engine import run_match
from .model import ArenaSpec, BladeSpec
from .policy import PassivePolicy


@dataclass
class MechanicalMatchupReport:
    a: str
    b: str
    arena: str
    neutral_runs: int
    win_probability: dict[str, float] = field(default_factory=dict)
    avg_duration_s: float = 0.0
    termination_reasons: dict[str, int] = field(default_factory=dict)
    per_body: dict[str, dict[str, float]] = field(default_factory=dict)
    advantages: dict[str, list[str]] = field(default_factory=dict)
    vulnerabilities: dict[str, list[str]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _aggregate(match, body_id: str) -> dict[str, float]:
    """Summarize a blade's mechanical performance across a match."""
    speeds, spins, centers = [], [], []
    collisions = 0
    for rnd in match.rounds:
        for fr in rnd.frames:
            st = fr.states.get(body_id)
            if not st:
                continue
            vx, vy = st["vel"]["x"], st["vel"]["y"]
            speeds.append(math.hypot(vx, vy))
            spins.append(abs(st["omega"]))
            px, py = st["pos"]["x"], st["pos"]["y"]
            centers.append(1.0 if math.hypot(px, py) < match.arena["radius"] * 0.28 else 0.0)
        for e in rnd.events:
            if e.type == "collision" and (e.actor == body_id or e.target == body_id):
                collisions += 1
    n = max(1, len(speeds))
    return {
        "avg_speed": sum(speeds) / n,
        "avg_spin": sum(spins) / n,
        "center_fraction": sum(centers) / n,
        "collisions_per_round": collisions / max(1, len(match.rounds)),
    }


def _classify(a_id: str, b_id: str, pa: dict[str, float], pb: dict[str, float],
              win_a: float) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Derive readable advantages/vulnerabilities from mechanical stats.

    These are deliberately heuristic and clearly non-causal, meant only to give
    a competitor a legible baseline. They never feed back into the engine.
    """
    adv_a, vul_a = [], []
    adv_b, vul_b = [], []
    # Spin endurance / center stability vs mobility trade-offs.
    if pa["avg_spin"] > pb["avg_spin"] * 1.05:
        adv_a.append("higher spin endurance")
        vul_b.append("lower spin endurance (late spin-out risk)")
    if pa["center_fraction"] > pb["center_fraction"] * 1.1:
        adv_a.append("better center stability")
        vul_b.append("weaker center control")
    if pa["avg_speed"] > pb["avg_speed"] * 1.05:
        adv_a.append("higher mobility")
        vul_b.append("lower mobility")
    if pa["collisions_per_round"] > pb["collisions_per_round"] * 1.1:
        adv_a.append("more contact leverage")
        vul_b.append("loses the contact trade")
    if win_a > 0.55:
        adv_a.append("favored in neutral engagement")
        vul_b.append("mechanically disadvantaged")
    elif win_a < 0.45:
        vul_a.append("mechanically disadvantaged")
        adv_b.append("favored in neutral engagement")
    return {a_id: adv_a, b_id: adv_b}, {a_id: vul_a, b_id: vul_b}


def mechanical_report(sa: BladeSpec, sb: BladeSpec, arena: ArenaSpec | None = None,
                      runs: int = 100, base_seed: int = 5000,
                      rounds: int = 3) -> MechanicalMatchupReport:
    arena = arena or ArenaSpec()
    passive = PassivePolicy()
    wins = {sa.id: 0, sb.id: 0}
    reasons: dict[str, int] = {}
    durations: list[float] = []
    agg_a = {"avg_speed": 0.0, "avg_spin": 0.0, "center_fraction": 0.0,
             "collisions_per_round": 0.0}
    agg_b = dict(agg_a)
    for r in range(runs):
        m = run_match(base_seed + r * 999983, arena, sa, sb, passive, passive, rounds)
        if m.winner == sa.id:
            wins[sa.id] += 1
        elif m.winner == sb.id:
            wins[sb.id] += 1
        else:
            wins["draw"] = wins.get("draw", 0) + 1
        for rr in m.rounds:
            reasons[rr.reason] = reasons.get(rr.reason, 0) + 1
            if rr.frames:
                durations.append(rr.frames[-1].t)
        for k in agg_a:
            agg_a[k] += _aggregate(m, sa.id)[k]
            agg_b[k] += _aggregate(m, sb.id)[k]
    n = max(1, runs)
    agg_a = {k: v / n for k, v in agg_a.items()}
    agg_b = {k: v / n for k, v in agg_b.items()}

    total = max(1, sum(wins.values()))
    win_prob = {k: round(v / total, 3) for k, v in wins.items()}
    win_a = win_prob.get(sa.id, 0.0)
    adv, vul = _classify(sa.id, sb.id, agg_a, agg_b, win_a)

    return MechanicalMatchupReport(
        a=sa.id, b=sb.id, arena=arena.id, neutral_runs=runs,
        win_probability=win_prob,
        avg_duration_s=round(sum(durations) / max(1, len(durations)), 3),
        termination_reasons=dict(sorted(reasons.items(), key=lambda kv: -kv[1])),
        per_body={sa.id: {k: round(v, 4) for k, v in agg_a.items()},
                  sb.id: {k: round(v, 4) for k, v in agg_b.items()}},
        advantages=adv,
        vulnerabilities=vul,
    )
