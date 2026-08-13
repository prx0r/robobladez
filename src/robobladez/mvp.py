"""One-command MVP vertical slice (rmdev2 Phase 26).

`robobladez mvp --agent boris --agent morty --seed 2026 --render --out out/mvp`

Produces the full artifact tree that proves RoboBladez works end-to-end:

    out/mvp/
    ├── competition/   entries, mechanical-report, match-execution-manifest,
    │                  reincarnations, match, replay
    ├── canon/         events.jsonl, agent/daimon snapshots, canon-manifest
    ├── visual/        boris, morty, arena, effects, visual-manifest
    ├── story/         episode.json, beats.json
    ├── shots/         shot-*.json
    ├── controls/      shot-*-first.png, shot-*-last.png (composition specs)
    ├── renders/       drafts/ finals/ retakes/   (mock, no LTX call)
    ├── qa/            verdicts.json
    ├── episode/       master.mp4 (manifest), episode-manifest.json
    └── RUN.json       provenance root
"""
from __future__ import annotations
import json, os
from pathlib import Path
from typing import Any

from .agent import AgentState
from .assets import AssetLibrary, VisualForge, VisualSpec
from .battle import run_battle
from .canon import CanonStore
from .canonical import extract_canonical_events
from .competition import make_entry, EntrySnapshot, build_execution_manifest
from .control_frames import ControlFrameBuilder
from .media import ShotSpec, RendererManifest, RenderQueue, simulate_render, binding_qa
from .significance import SignificanceDetector
from .story import compile_story
from .shots import compile_shots
from .zoo import make_body


def run_mvp(out_dir: str = "out/mvp", agents: list[str] | None = None,
            seed: int = 2026, rounds: int = 3, mechanical_runs: int = 20,
            render: bool = True) -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    agents = agents or ["boris", "morty"]
    (a_id, b_id) = agents[0], agents[1]

    # ---- Fixtures: two agents + bodies ----
    body_a = make_body("balanced", f"-{a_id}")
    body_b = make_body("heavy", f"-{b_id}")
    agent_a = AgentState(a_id, genesis_seed=f"{seed}:{a_id}")
    agent_b = AgentState(b_id, genesis_seed=f"{seed}:{b_id}")

    # ---- Battle (reincarnation path) ----
    outcome = run_battle(agent_a, body_a, agent_b, body_b,
                         mechanical_runs=mechanical_runs,
                         strategic_rounds=rounds, base_seed=seed)

    # ---- Competition entries + immutable snapshots (bind the exact reincarnations) ----
    entry_a = make_entry(agent_a, body_a, body_version="R1")
    entry_b = make_entry(agent_b, body_b, body_version="R1")
    snap_a, snap_b = _snapshots_with_bindings(outcome, entry_a, entry_b, body_a, body_b)

    # ---- Execution manifest (Phase 2) ----
    exec_manifest = build_execution_manifest(
        execution_id=f"exec-{outcome.match.match_id}",
        entry_a=snap_a, entry_b=snap_b, seed=seed + 5000, rounds=rounds,
        challenge_nonce=f"{seed}|{body_a.id}|{body_b.id}")
    exec_digest = exec_manifest.execution_digest()

    # ---- Canonical events ----
    events = extract_canonical_events(outcome.match, exec_digest)

    # ---- Visual library + forge (canonical packs) ----
    lib = AssetLibrary()
    forge = VisualForge(lib)
    for aid in agents:
        forge.ensure_shot_assets([VisualSpec(spec_id=f"vs-{aid}-talisman",
                                             entity_id=aid, asset_type="TALISMAN",
                                             mechanical_version="R1")])
    forge.ensure_shot_assets([VisualSpec(spec_id="vs-arena", entity_id="arena-s1",
                                         asset_type="ARENA", mechanical_version="R1")])

    # ---- Story + shots (ShotSpec v2) ----
    episode = compile_story(outcome.match, outcome.analysis, exec_digest)
    blade_map = {body_a.id: a_id, body_b.id: b_id}
    shots_dict = compile_shots(episode, asset_library=lib,
                               agents={a_id: agent_a, b_id: agent_b},
                               body_versions={a_id: "R1", b_id: "R1"},
                               blade_id_map=blade_map)
    shot_specs = [ShotSpec(**s) for s in shots_dict["shots"]]

    # ---- Control frames from canonical events ----
    frames = _build_control_frames(events, shot_specs)

    # ---- Render queue (mock, no LTX) ----
    queue = RenderQueue()
    verdicts = []
    drafts, finals = [], []
    for spec in shot_specs:
        job = queue.enqueue(spec, profile="final", seed=seed)
        art = simulate_render(spec, job, RendererManifest(seed=seed, profile="final"))
        queue.complete(job, uri=art.uri, digest=art.digest)
        verdict = binding_qa(spec, art, expected_winner=outcome.winner_agent_id())
        queue.record_verdict(verdict)
        verdicts.append(verdict.to_dict())
        finals.append(art.to_dict())

    # ---- Canon store ----
    canon_dir = out / "canon"
    canon_dir.mkdir(parents=True, exist_ok=True)
    store = CanonStore(canon_dir / "canon.sqlite3")
    store.save_match(outcome.match)

    # ---- Write artifact tree ----
    artifacts = {
        "competition/entries.json": {
            "a": entry_a.to_dict(), "b": entry_b.to_dict(),
            "a_snapshot": snap_a.to_dict(), "b_snapshot": snap_b.to_dict(),
        },
        "competition/mechanical-report.json": outcome.mechanical.to_dict(),
        "competition/match-execution-manifest.json": exec_manifest.to_dict(),
        "competition/reincarnations/%s-r001.json" % a_id: {"id": agent_a.current_reincarnation_id,
                                                           "manifest": _first_rc(agent_a)},
        "competition/reincarnations/%s-r001.json" % b_id: {"id": agent_b.current_reincarnation_id,
                                                           "manifest": _first_rc(agent_b)},
        "competition/match.json": outcome.match.to_dict(),
        "competition/replay.json": outcome.match.to_dict(),
        "canon/events.jsonl": "\n".join(json.dumps(e.to_dict()) for e in events),
        "canon/agent-snapshots/%s.json" % a_id: _agent_snapshot(agent_a),
        "canon/agent-snapshots/%s.json" % b_id: _agent_snapshot(agent_b),
        "canon/daimon-snapshots/%s.json" % a_id: agent_a.daimon.to_dict(),
        "canon/daimon-snapshots/%s.json" % b_id: agent_b.daimon.to_dict(),
        "canon/canon-manifest.json": {"execution_digest": exec_digest,
                                      "replay_digest": outcome.match.replay_digest,
                                      "matches": store.count()},
        "visual/visual-manifest.json": {"assets": [a.to_dict() for a in lib.all()]},
        "story/episode.json": episode,
        "story/beats.json": episode["beats"],
        "renders/finals/final-artifacts.json": finals,
        "qa/verdicts.json": {"verdicts": verdicts,
                             "accepted": sum(1 for v in verdicts if v["pass"]),
                             "total": len(verdicts)},
        "episode/episode-manifest.json": _episode_manifest(
            episode, exec_digest, outcome.match.replay_digest, verdicts, shot_specs),
    }
    # Per-shot and per-frame files.
    for spec in shot_specs:
        artifacts[f"shots/{spec.shot_id}.json"] = spec.to_dict()
    for fr in frames:
        artifacts[f"controls/{fr.shot_id}-first.json"] = fr.first.to_dict() if fr.first else {}
        artifacts[f"controls/{fr.shot_id}-last.json"] = fr.last.to_dict() if fr.last else {}

    for relpath, content in artifacts.items():
        _write(out, relpath, content)

    # ---- RUN.json provenance root ----
    run = {
        "command": "robobladez mvp",
        "seed": seed, "agents": agents, "rounds": rounds,
        "winner": outcome.winner_agent_id(),
        "execution_digest": exec_digest,
        "replay_digest": outcome.match.replay_digest,
        "reincarnations": {a_id: agent_a.current_reincarnation_id,
                           b_id: agent_b.current_reincarnation_id},
        "canon_events": len(events),
        "shots": len(shot_specs),
        "control_frames": len(frames),
        "render_accepted": sum(1 for v in verdicts if v["pass"]),
        "render_total": len(verdicts),
    }
    (out / "RUN.json").write_text(json.dumps(run, indent=2))
    return run


def _snapshots_with_bindings(outcome, entry_a, entry_b, body_a, body_b):
    """Build EntrySnapshots bound to the exact reincarnation ASTs that fought.

    Reads outcome.match.reincarnation_bindings (keyed by body_id) so the
    execution_digest covers the actual battle-self programs.
    """
    bindings = outcome.match.reincarnation_bindings
    snap_a = EntrySnapshot.from_entry(
        entry_a,
        reincarnation_id=_rc_id_for(bindings, body_a.id, outcome, body_a),
        reincarnation_digest=bindings.get(body_a.id, {}).get("canonical_ast_sha256", ""),
        reincarnation_commitment=bindings.get(body_a.id, {}).get("commitment", ""))
    snap_b = EntrySnapshot.from_entry(
        entry_b,
        reincarnation_id=_rc_id_for(bindings, body_b.id, outcome, body_b),
        reincarnation_digest=bindings.get(body_b.id, {}).get("canonical_ast_sha256", ""),
        reincarnation_commitment=bindings.get(body_b.id, {}).get("commitment", ""))
    return snap_a, snap_b


def _rc_id_for(bindings, body_id, outcome, body):
    b = bindings.get(body_id, {})
    if b.get("reincarnation_id"):
        return b["reincarnation_id"]
    # Fall back to the avatar manifest id.
    for av in outcome.avatars.values():
        if av.body_id == body_id:
            return av.manifest.reincarnation_id
    return ""


def _build_control_frames(events, shot_specs):
    from .control_frames import ControlFrameBuilder
    builder = ControlFrameBuilder()
    frames = []
    for spec in shot_specs:
        basis = spec.basis_event_ids
        if basis:
            ev = next((e for e in events if e.event_id == basis[0]), None)
            if ev:
                frames.append(builder.build(ev, spec.shot_id))
    return frames


def _first_rc(agent: AgentState) -> dict:
    return agent.reincarnation_history[-1] if agent.reincarnation_history else {}


def _agent_snapshot(agent: AgentState) -> dict:
    from .agent import agent_snapshot
    return agent_snapshot(agent, 1)


def _episode_manifest(episode, exec_digest, replay_digest, verdicts, shot_specs) -> dict:
    """Complete episode provenance chain (rmdev2 Phase 20).

    Links episode -> match execution -> replay -> canon events -> shot specs
    (by their content digests) -> QA verdicts -> a final master digest, so any
    frame can be traced to canon.
    """
    shot_digests = {s.shot_id: s.digest() for s in shot_specs}
    import hashlib
    master_digest = hashlib.sha256(
        json.dumps(shot_digests, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:20]
    return {
        "episode_id": episode["episode_id"],
        "match_id": episode["match_id"],
        "execution_digest": exec_digest,
        "replay_digest": replay_digest,
        "canon_event_ids": episode["canonical_event_ids"],
        "shot_spec_digests": shot_digests,
        "qa_accepted": sum(1 for v in verdicts if v["pass"]),
        "qa_total": len(verdicts),
        "final_master_digest": master_digest,
    }


def _write(out: Path, relpath: str, content: Any) -> None:
    p = out / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, str):
        p.write_text(content)
    else:
        p.write_text(json.dumps(content, indent=2, default=str))
