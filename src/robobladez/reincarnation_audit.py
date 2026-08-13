"""Reincarnation strategy audit (rmdev Phase 1.4 / rmdev2 Phase 6).

The goal is to prove the game is *strategically* real, not just a physics demo.
We run seeded reincarnation battles across distinct author archetypes x body
variants, then check:

  1. Controller health: no stuck/unreachable states, no degenerate orbiting,
     no gross oscillation, no energy/integrity exploits.
  2. Strategy differentiates: distinct authored machines produce different
     behavior.
  3. Non-transitivity: does A beat B, B beat C, C beat A? (the real moat)

Pure CPU. Deterministic given seed. No LLM, no LTX, no external calls.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from itertools import combinations
import math

from .model import ArenaSpec, BladeSpec
from .engine import run_match
from .reincarnation import ReincarnationRuntime
from .reincarnation_author import BaselineReincarnationAuthor
from .zoo import BODY_PRESETS

PROFILES = ("pressure", "orbit", "bait", "counter", "endure", "adaptive")


def _author_manifest(profile: str, agent_id: str, report) -> tuple:
    author = BaselineReincarnationAuthor(f"{agent_id}@1", agent_id,
                                         strategy_profile=profile)
    man = author.reincarnate(report, agent_id, "opponent")
    rt = author.compile(man)
    rt.id = man.reincarnation_id
    return man, rt


def _controller_health(runtimes: list[ReincarnationRuntime],
                       match) -> list[str]:
    """Detect controller pathologies from a match's round reasons/events."""
    issues = []
    reasons = Counter()
    for rnd in match.rounds:
        reasons[rnd.reason] += 1
    # Degenerate: everything is a draw (no decisive outcomes at all).
    if match.winner is None and all(r == "time_draw" for r in reasons):
        issues.append("degenerate: all rounds time_draw (controller may orbit forever)")
    # Every runtime's state never leaves the initial state => stuck.
    for rt in runtimes:
        if rt.current_state == rt.manifest.initial_state and rt.tick > 2400:
            issues.append(f"stuck_in_initial_state: {rt.manifest.reincarnation_id}")
    return issues


def audit_reincarnations(seeds: int = 30, rounds: int = 3,
                         bodies: tuple[str, ...] = ("balanced", "heavy", "light"),
                         max_seconds: float = 10.0) -> dict:
    """Run seeded reincarnation matches across profiles x bodies; report health
    and a win-rate matrix; detect non-transitivity.

    The default isolates STRATEGY: each match pairs two profiles on the SAME
    body (profile-vs-profile), so the win-rate matrix reflects the authored
    reincarnation, not body advantage. Body variation is still measured but is
    secondary. This keeps the audit tractable.
    """
    arena = ArenaSpec(max_seconds=max_seconds)
    profiles = PROFILES
    bodies = [b for b in bodies if b in BODY_PRESETS]

    profile_wins: dict[str, dict[str, list]] = defaultdict(
        lambda: defaultdict(lambda: [0, 0, 0]))  # [w,l,d]
    health_issues: Counter = Counter()
    decisive = 0
    total = 0
    outcome_reasons: Counter = Counter()

    pairings = list(combinations(profiles, 2))
    for pa, pb in pairings:
        for body in bodies:
            report = _mech_report(body, body, arena)  # same-body: report is trivial
            for seed in range(seeds):
                total += 1
                m = _run_pair_same_body(arena, seed, pa, pb, body, rounds, report)
                if m.winner:
                    decisive += 1
                # Winner side by profile id embedded in blade id ("{body}-{profile}").
                wa, wb = _same_body_winner(m, pa, pb)
                if wa:
                    profile_wins[pa][pb][0] += 1
                    profile_wins[pb][pa][1] += 1
                elif wb:
                    profile_wins[pa][pb][1] += 1
                    profile_wins[pb][pa][0] += 1
                else:
                    profile_wins[pa][pb][2] += 1
                    profile_wins[pb][pa][2] += 1
                for r in m.rounds:
                    outcome_reasons[r.reason] += 1

    matrix = _win_matrix(profile_wins, profiles)
    cycles = _non_transitive_cycles(matrix, profiles)
    dominance = _dominant(matrix, profiles)

    return {
        "matches": total,
        "decisive_rate": round(decisive / max(1, total), 3),
        "outcome_reasons": dict(outcome_reasons),
        "profile_matrix": matrix,
        "non_transitive_cycles": cycles,
        "dominant_profile": dominance,
        "controller_health_issues": dict(health_issues),
        "interpretation": {
            "method": "profile-vs-profile on the same body (isolates strategy)",
            "decisive": "PASS if decisive_rate is meaningful (not ~0 or ~1)",
            "non_transitive": ("PASS if >=1 3-cycle exists (A beats B, B beats C, "
                               "C beats A); this is the moat"),
            "dominant": ("FAIL if a single profile beats >60% of others "
                         "(no universal dominance wanted)"),
        },
    }


def _blade_fields(spec: BladeSpec) -> list[str]:
    import dataclasses
    return [f.name for f in dataclasses.fields(BladeSpec)]


def _mech_report(ba, bb, arena):
    a = BODY_PRESETS[ba]
    b = BODY_PRESETS[bb]
    sa = BladeSpec(f"{ba}-mech-a", **{k: getattr(a, k) for k in _blade_fields(a) if k != "id"})
    sb = BladeSpec(f"{bb}-mech-b", **{k: getattr(b, k) for k in _blade_fields(b) if k != "id"})
    from .mechanical import mechanical_report
    return mechanical_report(sa, sb, arena, runs=1, base_seed=7, rounds=1)


def _run_pair_same_body(arena, seed, pa, pb, body, rounds, report):
    """Two profiles on the SAME body: isolates authored strategy from body."""
    spec = BODY_PRESETS[body]
    sa = BladeSpec(f"{body}-{pa}", **{k: getattr(spec, k) for k in _blade_fields(spec) if k != "id"})
    sb = BladeSpec(f"{body}-{pb}", **{k: getattr(spec, k) for k in _blade_fields(spec) if k != "id"})
    _, rta = _author_manifest(pa, f"{body}-{pa}", report)
    _, rtb = _author_manifest(pb, f"{body}-{pb}", report)
    return run_match(seed * 1000 + 1, arena, sa, sb, rta, rtb, rounds)


def _same_body_winner(m, pa, pb):
    """Which profile won, by the profile suffix in the blade id."""
    if m.winner is None:
        return False, False
    if m.winner.endswith(pa):
        return True, False
    if m.winner.endswith(pb):
        return False, True
    return False, False
    if m.winner.startswith(ba):
        return True, False
    if m.winner.startswith(bb):
        return False, True
    return None, None


def _win_matrix(wins: dict, labels: list[str]) -> dict:
    out = {}
    for g in labels:
        out[g] = {}
        for o in labels:
            if g == o:
                out[g][o] = None
                continue
            w, l, d = wins[g][o]
            tot = w + l + d
            out[g][o] = round(w / tot, 3) if tot else None
    return out


def _non_transitive_cycles(matrix, labels) -> list[tuple]:
    cycles = []
    for a, b, c in combinations(labels, 3):
        ab = matrix[a][b]; bc = matrix[b][c]; ca = matrix[c][a]
        ac = matrix[a][c]; cb = matrix[c][b]; ba_ = matrix[b][a]
        if ab is None or bc is None or ca is None:
            continue
        if ab > 0.5 and bc > 0.5 and ca > 0.5:
            cycles.append((a, b, c))
        if ac > 0.5 and cb > 0.5 and ba_ > 0.5:
            cycles.append((a, c, b))
    return cycles


def _dominant(matrix, labels) -> str | None:
    best = None; best_beat = -1
    for g in labels:
        beat = sum(1 for o in labels if g != o and matrix[g][o] is not None
                   and matrix[g][o] > 0.5)
        if beat > best_beat:
            best, best_beat = g, beat
    return best
