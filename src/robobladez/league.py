from __future__ import annotations
from itertools import combinations
from typing import Any
from pathlib import Path
import json

from .agent import AgentState, agent_snapshot
from .battle import run_battle, ReportAwareStrategist
from .canon import CanonStore
from .engine import run_match
from .model import ArenaSpec, BladeSpec
from .policy import Policy
from .signatures import SignatureRegistry
from .salience import SalienceDetector


def round_robin(entries, seed: int = 1000, rounds: int = 3):
    arena = ArenaSpec()
    pts = {spec.id: 0 for spec, _ in entries}
    matches = []
    for i, ((sa, pa), (sb, pb)) in enumerate(combinations(entries, 2)):
        m = run_match(seed + i * 100003, arena, sa, sb, pa, pb, rounds)
        matches.append(m)
        if m.winner:
            pts[m.winner] += 3
        else:
            pts[sa.id] += 1
            pts[sb.id] += 1
    return matches, sorted(pts.items(), key=lambda kv: (-kv[1], kv[0]))


def run_season(entries: list[tuple[str, BladeSpec, Policy]],
               out_dir: str | None = None,
               seed: int = 2026, rounds: int = 3,
               mechanical_runs: int = 40) -> dict[str, Any]:
    """Persistent season via the hardened two-phase battle flow (rm8).

    Agents evolve through run_battle, which is transactional (both snapshot
    pre-match), uses a persistent SignatureRegistry, and assigns salience via
    typed evidence rather than `bool(winner)`. Never feeds back into the sealed
    engine (Constitution 8).
    """
    arena = ArenaSpec()
    agents = {aid: AgentState(agent_id=aid, genesis_seed=f"{seed}:{aid}")
              for aid, _, _ in entries}
    specs = {aid: spec for aid, spec, _ in entries}
    registry = SignatureRegistry()
    salience = SalienceDetector()
    store = CanonStore(out_dir + "/canon.sqlite3") if out_dir else None

    match_outcomes = []
    pairings = list(combinations(entries, 2))
    for i, ((aid, _, _), (bid, _, _)) in enumerate(pairings):
        outcome = run_battle(
            agents[aid], specs[aid], agents[bid], specs[bid], arena,
            mechanical_runs=mechanical_runs, strategic_rounds=rounds,
            base_seed=seed + i * 100003,
            strategist_a=ReportAwareStrategist(),
            strategist_b=ReportAwareStrategist(),
            registry=registry, salience_detector=salience,
        )
        match_outcomes.append(outcome)
        if store:
            store.save_match(outcome.match)
            store.save_agent_version(aid, 1, agent_snapshot(agents[aid], 1))
            store.save_agent_version(bid, 1, agent_snapshot(agents[bid], 1))

    pts = {aid: 0 for aid, _, _ in entries}
    for o in match_outcomes:
        winner_aid = o.winner_agent_id()
        if winner_aid:
            pts[winner_aid] += 3
        else:
            for aid, _, _ in entries:
                if aid in o.avatars:
                    pts[aid] += 1

    result = {
        "season_seed": seed,
        "matches": len(match_outcomes),
        "standings": sorted(pts.items(), key=lambda kv: (-kv[1], kv[0])),
        "daimons": {aid: agents[aid].daimon.to_dict() for aid in agents},
        "signatures": {aid: [c.to_dict() for c in registry.candidates(aid)]
                       for aid in agents},
        "salience": {aid: [c for o in match_outcomes
                           for c in o.salience.get(aid, [])]
                     for aid in agents},
        "agent_snapshots": {aid: agent_snapshot(agents[aid], 1) for aid in agents},
    }
    if out_dir:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        for i, o in enumerate(match_outcomes):
            from .replay import save_match
            save_match(o.match, out / f"match_{o.match.match_id}.json")
        (out / "season.json").write_text(json.dumps(result, indent=2))
    return result
