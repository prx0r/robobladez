"""Diagnose whether the game is strategic (rmdev Phase 1.4).

Reads a matrix TSV produced by scripts/run_matrix.py and reports:
  - win-rate matrix
  - body advantage / policy advantage
  - seed sensitivity
  - termination-reason distribution
  - non-transitivity: does A beat B, B beat C, C beat A?
"""
from __future__ import annotations
import csv
from collections import defaultdict
from itertools import combinations


def load_matrix(path: str) -> list[dict]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def _wins(rows, group_key, opp_key):
    """Return dict group -> {opponent: (wins, losses, draws)}."""
    agg = defaultdict(lambda: defaultdict(lambda: [0, 0, 0]))
    for r in rows:
        g, o = r[group_key], r[opp_key]
        if g == o:
            continue
        if r["winner"] == g:
            agg[g][o][0] += 1
        elif r["winner"] == o:
            agg[g][o][1] += 1
        else:
            agg[g][o][2] += 1
    return agg


def win_rate_matrix(rows, group_key="policy_a", opp_key="policy_b"):
    agg = _wins(rows, group_key, opp_key)
    matrix = {}
    for g, opps in agg.items():
        matrix[g] = {}
        for o, (w, l, d) in opps.items():
            tot = w + l + d
            matrix[g][o] = round(w / tot, 3) if tot else None
    return matrix


def _non_transitive_cycles(matrix):
    """Find 3-cycles A beats B, B beats C, C beats A in a win-rate matrix."""
    nodes = list(matrix)
    cycles = []
    for a, b, c in combinations(nodes, 3):
        a_b = matrix[a].get(b)
        b_c = matrix[b].get(c)
        c_a = matrix[c].get(a)
        if a_b is None or b_c is None or c_a is None:
            continue
        if a_b > 0.5 and b_c > 0.5 and c_a > 0.5:
            cycles.append((a, b, c))
        # reverse orientation too
        a_c = matrix[a].get(c)
        c_b = matrix[c].get(b)
        b_a = matrix[b].get(a)
        if a_c > 0.5 and c_b > 0.5 and b_a > 0.5:
            cycles.append((a, c, b))
    return cycles


def seed_sensitivity(rows, group_key="policy_a", opp_key="policy_b"):
    """Fraction of matchups where seed changed the winner."""
    by_pair = defaultdict(set)
    for r in rows:
        g, o = r[group_key], r[opp_key]
        if g == o:
            continue
        key = tuple(sorted((g, o)))
        by_pair[key].add(r["winner"] or "draw")
    outcomes = sum(1 for wins in by_pair.values() if len(wins) > 1)
    return round(outcomes / max(1, len(by_pair)), 3)


def analyze(path: str) -> dict:
    rows = load_matrix(path)
    policy_matrix = win_rate_matrix(rows, "policy_a", "policy_b")
    body_matrix = win_rate_matrix(rows, "body_a", "body_b")

    # Dominance: policy that beats most others.
    policy_dominance = {
        g: sum(1 for o, v in opps.items() if v is not None and v > 0.5)
        for g, opps in policy_matrix.items()
    }

    # Termination reasons.
    reasons = defaultdict(int)
    for r in rows:
        for part in (r["reason"] or "").split(";"):
            if part:
                k = part.split(":")[0]
                reasons[k] += 1

    return {
        "matches": len(rows),
        "policies": list(policy_matrix),
        "bodies": list(body_matrix),
        "policy_dominance": dict(sorted(policy_dominance.items(),
                                        key=lambda kv: -kv[1])),
        "non_transitive_cycles": _non_transitive_cycles(policy_matrix),
        "policy_matrix": policy_matrix,
        "body_matrix": body_matrix,
        "seed_sensitivity": seed_sensitivity(rows),
        "termination_reasons": dict(reasons),
        "diagnosis": _diagnose(policy_matrix, body_matrix, reasons),
    }


def _diagnose(policy_matrix, body_matrix, reasons):
    n_pol = len(policy_matrix)
    # A dominant policy beats >60% of others.
    best_pol = max(
        (g for g in policy_matrix),
        key=lambda g: sum(1 for o, v in policy_matrix[g].items()
                          if v is not None and v > 0.5),
    )
    best_pol_beat = sum(1 for o, v in policy_matrix[best_pol].items()
                        if v is not None and v > 0.5)
    dominant = best_pol_beat > 0.6 * max(1, n_pol - 1)

    best_body = max(
        (g for g in body_matrix),
        key=lambda g: sum(1 for o, v in body_matrix[g].items()
                          if v is not None and v > 0.5),
    )
    best_body_beat = sum(1 for o, v in body_matrix[best_body].items()
                         if v is not None and v > 0.5)
    body_dominant = best_body_beat > 0.6 * max(1, len(body_matrix) - 1)

    notes = []
    if dominant:
        notes.append(f"DOMINANT POLICY: {best_pol} beats {best_pol_beat} others")
    else:
        notes.append("no single dominant policy")
    if body_dominant:
        notes.append(f"DOMINANT BODY: {best_body} beats {best_body_beat} others")
    else:
        notes.append("no single dominant body")
    if len(reasons) >= 3:
        notes.append("healthy termination mix: " + ",".join(sorted(reasons)))
    else:
        notes.append("termination mix too narrow")
    return " | ".join(notes)


if __name__ == "__main__":
    import sys, json
    if len(sys.argv) < 2:
        print("usage: python -m robobladez.meta <matrix.tsv>")
        sys.exit(1)
    print(json.dumps(analyze(sys.argv[1]), indent=2))
