from __future__ import annotations
from itertools import combinations
from typing import Any
from pathlib import Path
import json

from .agent import AgentState, agent_snapshot
from .analysis import analyze_behavior
from .canon import CanonStore
from .engine import run_match
from .evolution import evolve_agent
from .model import ArenaSpec, BladeSpec
from .policy import Policy
from .replay import save_match
from .signatures import SignatureDetector


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
               seed: int = 2026, rounds: int = 3) -> dict[str, Any]:
    """Persistent season: evolves agents, projects daimons, detects signatures.

    Agents are tracked as AgentState across every pairing, so later matches are
    informed by earlier history. All of this is the projection/lineage layer
    (BUILD_NEXT 5-6); it never feeds back into the sealed engine (Constitution 8).
    """
    arena = ArenaSpec()
    agents = {aid: AgentState(agent_id=aid, genesis_seed=f"{seed}:{aid}")
              for aid, _, _ in entries}
    specs = {aid: spec for aid, spec, _ in entries}
    policies = {aid: pol for aid, _, pol in entries}
    detector = SignatureDetector()
    store = CanonStore(out_dir + "/canon.sqlite3") if out_dir else None

    matches: list[Any] = []
    pairings = list(combinations(entries, 2))
    for i, ((aid, _, _), (bid, _, _)) in enumerate(pairings):
        m = run_match(seed + i * 100003, arena, specs[aid], specs[bid],
                      policies[aid], policies[bid], rounds)
        matches.append(m)
        analysis = analyze_behavior(m)

        evolve_agent(agents[aid], m, aid, bid, agents[bid],
                     analysis[aid]["daimon_projection"]["affinities"])
        evolve_agent(agents[bid], m, bid, aid, agents[aid],
                     analysis[bid]["daimon_projection"]["affinities"])
        detector.register(m, aid)
        detector.register(m, bid)
        if store:
            store.save_match(m)
            store.save_agent_version(aid, 1, agent_snapshot(agents[aid], 1))
            store.save_agent_version(bid, 1, agent_snapshot(agents[bid], 1))

    pts = {aid: 0 for aid, _, _ in entries}
    for m in matches:
        if m.winner:
            pts[m.winner] += 3
        else:
            for aid, _, _ in entries:
                if aid in m.blades:
                    pts[aid] += 1

    result = {
        "season_seed": seed,
        "matches": len(matches),
        "standings": sorted(pts.items(), key=lambda kv: (-kv[1], kv[0])),
        "daimons": {aid: agents[aid].daimon.to_dict() for aid in agents},
        "signatures": {aid: [s.to_dict() for s in detector.signatures()]
                       for aid in agents},
        "agent_snapshots": {aid: agent_snapshot(agents[aid], 1) for aid in agents},
    }
    if out_dir:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        for m in matches:
            save_match(m, out / f"match_{m.winner or 'draw'}.json")
        (out / "season.json").write_text(json.dumps(result, indent=2))
    return result
