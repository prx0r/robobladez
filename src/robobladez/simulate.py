"""Full end-to-end stack simulation (no LTX call).

Runs the ENTIRE RoboBladez pipeline on CPU:
  agent/bodies -> mechanical reveal -> sealed reincarnation -> deterministic
  battle -> replay/canon -> analysis -> evolution -> story -> shot specs ->
  render queue -> SIMULATED render -> QA.

This is the "does the whole thing work end to end" harness. LTX/ComfyUI is never
called; a RendererManifest + mock RenderArtifact substitutes for the real GPU
render so the pipeline can be validated and tested offline.
"""
from __future__ import annotations
from typing import Any

from .agent import AgentState
from .battle import run_battle
from .canon import CanonStore
from .media import ShotSpec, produce_episode
from .replay import save_match
from .shots import compile_shots
from .story import compile_story
from .zoo import make_body


def simulate_full_stack(entries: list[tuple[str, Any, Any]],
                        out_dir: str | None = None,
                        seed: int = 2026,
                        rounds: int = 3,
                        mechanical_runs: int = 20,
                        profiles: str = "final") -> dict:
    """Run the complete stack for a set of (agent_id, body, policy) entries.

    Every pairing is a full two-phase reincarnation battle, followed by the
    media pipeline for the decisive match. Returns organized artifacts.
    """
    from itertools import combinations
    agents = {aid: AgentState(agent_id=aid, genesis_seed=f"{seed}:{aid}")
              for aid, _, _ in entries}
    specs = {aid: spec for aid, spec, _ in entries}
    if out_dir:
        from pathlib import Path
        Path(out_dir).mkdir(parents=True, exist_ok=True)
    store = CanonStore(out_dir + "/canon.sqlite3") if out_dir else None

    battles = []
    for i, ((aid, _, _), (bid, _, _)) in enumerate(combinations(entries, 2)):
        outcome = run_battle(agents[aid], specs[aid], agents[bid], specs[bid],
                             mechanical_runs=mechanical_runs,
                             strategic_rounds=rounds,
                             base_seed=seed + i * 100003)
        battles.append(outcome)
        if store:
            store.save_match(outcome.match)
            if out_dir:
                from pathlib import Path
                out = Path(out_dir)
                out.mkdir(parents=True, exist_ok=True)
                save_match(outcome.match, out / f"match_{outcome.match.match_id}.json")

    # Media pipeline for the last (or a decisive) battle.
    outcome = battles[-1]
    # Build an execution manifest (rmdev2 Phase 2) for provenance.
    exec_manifest = _execution_manifest_for(outcome, entries, seed)
    exec_digest = exec_manifest.execution_digest()
    episode = compile_story(outcome.match, outcome.analysis, exec_digest)
    # Build the canonical visual library and seed the competitors' assets so the
    # shot compiler resolves REAL references (rmreview P0.7), not an empty lib.
    asset_library, body_versions = _seed_visual_library(entries, seed)
    blade_id_map = {spec.id: aid for aid, spec, _ in entries}
    shots_dict = compile_shots(episode, asset_library=asset_library,
                               agents=agents, body_versions=body_versions,
                               blade_id_map=blade_id_map)
    specs = [ShotSpec(**s) for s in shots_dict["shots"]]
    media = produce_episode(specs, winner=outcome.winner_agent_id(),
                            profiles=profiles, seed=seed)

    standings = {aid: 0 for aid, _, _ in entries}
    for o in battles:
        w = o.winner_agent_id()
        if w:
            standings[w] += 3
        else:
            for aid, _, _ in entries:
                if aid in o.avatars:
                    standings[aid] += 1

    return {
        "battles": len(battles),
        "battle_winner": outcome.winner_agent_id(),
        "standings": sorted(standings.items(), key=lambda kv: (-kv[1], kv[0])),
        "execution_digest": exec_digest,
        "replay_digest": outcome.match.replay_digest,
        "reincarnations": {k: v.manifest.reincarnation_id
                           for k, v in outcome.avatars.items()},
        "episode_id": episode["episode_id"],
        "media": {
            "shots": media["shots"],
            "accepted": media["accepted"],
            "rejected": media["rejected"],
            "canonical_refs": {
                agent_id: _count_refs(shots_dict, agent_id)
                for agent_id, _, _ in entries
            },
        },
    }


def _execution_manifest_for(outcome, entries, seed):
    """Build a MatchExecutionManifest for the battle's two entries."""
    from .competition import make_entry, EntrySnapshot, build_execution_manifest
    from .agent import AgentState
    spec_map = {aid: spec for aid, spec, _ in entries}
    agent_list = list(outcome.avatars.keys())
    snapshots = {}
    for aid in agent_list:
        a = AgentState(aid)
        spec = spec_map.get(aid)
        if spec is None:
            continue
        snapshots[aid] = EntrySnapshot.from_entry(
            make_entry(a, spec, body_version="R1"))
    order = sorted(snapshots)
    if len(order) < 2:
        return None
    rounds = outcome.match.rounds[-1].round_no if outcome.match.rounds else 3
    return build_execution_manifest(
        execution_id=f"exec-{outcome.match.match_id}",
        entry_a=snapshots[order[0]], entry_b=snapshots[order[1]],
        seed=seed + 5000, rounds=rounds,
        challenge_nonce=f"{seed}|{order[0]}|{order[1]}")


def _seed_visual_library(entries, seed: int):
    """Generate canonical talisman + arena assets for each competitor."""
    from .assets import AssetLibrary, VisualForge, VisualSpec
    lib = AssetLibrary()
    forge = VisualForge(lib)
    body_versions = {}
    for aid, spec, _ in entries:
        bv = f"R{abs(hash(aid + str(seed))) % 20 + 1}"
        body_versions[aid] = bv
        forge.ensure_shot_assets([
            VisualSpec(spec_id=f"vs-{aid}-talisman", entity_id=aid,
                       asset_type="TALISMAN", mechanical_version=bv)
        ])
    forge.ensure_shot_assets([
        VisualSpec(spec_id="vs-arena-s1", entity_id="arena-s1",
                   asset_type="ARENA", mechanical_version="R1")
    ])
    return lib, body_versions


def _count_refs(shots_dict, agent_id: str) -> int:
    n = 0
    for s in shots_dict["shots"]:
        for r in s.get("references", []):
            if agent_id in r.get("asset_key", ""):
                n += 1
    return n


if __name__ == "__main__":
    import json
    from .policy import CounterPolicy, AggressivePolicy, CenterControlPolicy
    entries = [
        ("boris", make_body("balanced", "-boris"), CounterPolicy()),
        ("morty", make_body("heavy", "-morty"), AggressivePolicy()),
        ("alice", make_body("light", "-alice"), CenterControlPolicy()),
    ]
    print(json.dumps(simulate_full_stack(entries, seed=2026, rounds=3,
                                         mechanical_runs=10), indent=2))
