"""Run the body x policy x seed matchup matrix (rmdev Phase 1.3).

Writes per-match rows to a TSV (and optional DuckDB/Parquet later). Each row
captures body, policy, opponent, seed, winner, reason, duration, and stat
summaries. CPU-first: run headless anywhere.

Usage:
    python -m scripts.run_matrix --seeds 5 --rounds 3 --out matrix.tsv
"""
from __future__ import annotations
import argparse, csv, math, sys, os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from robobladez.engine import run_match
from robobladez.model import ArenaSpec
from robobladez.zoo import BODY_PRESETS, POLICY_ZOO


def run_one(seed, arena, spec_a, spec_b, pa, pb, rounds,
            body_a=None, policy_a=None, body_b=None, policy_b=None):
    m = run_match(seed, arena, spec_a, spec_b, pa, pb, rounds)
    # Aggregate stats across rounds.
    collisions = sum(1 for r in m.rounds for e in r.events if e.type == "collision")
    durations = [r.frames[-1].t for r in m.rounds if r.frames]
    reasons = {}
    for r in m.rounds:
        reasons[r.reason] = reasons.get(r.reason, 0) + 1
    # Energy/spin remaining from last frame of last round.
    energy_a = energy_b = spin_a = spin_b = None
    if m.rounds and m.rounds[-1].frames:
        fr = m.rounds[-1].frames[-1]
        if "a" in fr.states:
            energy_a = fr.states["a"]["energy"]
            spin_a = abs(fr.states["a"]["omega"])
        if "b" in fr.states:
            energy_b = fr.states["b"]["energy"]
            spin_b = abs(fr.states["b"]["omega"])
    return {
        "seed": seed,
        "body_a": body_a, "policy_a": policy_a,
        "body_b": body_b, "policy_b": policy_b,
        "winner": m.winner,
        "reason": ";".join(f"{k}:{v}" for k, v in reasons.items()),
        "duration": round(sum(durations), 3),
        "collisions": collisions,
        "energy_a": round(energy_a, 3) if energy_a is not None else "",
        "energy_b": round(energy_b, 3) if energy_b is not None else "",
        "spin_a": round(spin_a, 2) if spin_a is not None else "",
        "spin_b": round(spin_b, 2) if spin_b is not None else "",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--max_seconds", type=float, default=8.0)
    ap.add_argument("--out", default="matrix.tsv")
    ap.add_argument("--bodies", nargs="*", default=list(BODY_PRESETS))
    ap.add_argument("--policies", nargs="*", default=[p for p, _ in POLICY_ZOO])
    args = ap.parse_args()

    bodies = [b for b in args.bodies if b in BODY_PRESETS]
    policies = [p for p in args.policies if p in dict(POLICY_ZOO)]
    policy_fact = dict(POLICY_ZOO)

    arena = ArenaSpec(max_seconds=args.max_seconds)
    rows = []
    for ba in bodies:
        for pa_name in policies:
            for bb in bodies:
                for pb_name in policies:
                    # skip identical full spec + policy to halve work? Keep all
                    # for symmetry stats; dedup identical pairs.
                    if ba == bb and pa_name == pb_name:
                        continue
                    for s in range(args.seeds):
                        from robobladez.zoo import make_body
                        spec_a = make_body(ba, suffix=f"-{pa_name}")
                        spec_b = make_body(bb, suffix=f"-{pb_name}")
                        pa = policy_fact[pa_name]()
                        pb = policy_fact[pb_name]()
                        rows.append(run_one(s + 1, arena, spec_a, spec_b,
                                            pa, pb, args.rounds,
                                            body_a=ba, policy_a=pa_name,
                                            body_b=bb, policy_b=pb_name))

    cols = ["seed", "body_a", "policy_a", "body_b", "policy_b", "winner",
            "reason", "duration", "collisions", "energy_a", "energy_b",
            "spin_a", "spin_b"]
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows -> {args.out}")


if __name__ == "__main__":
    main()
