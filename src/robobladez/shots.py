"""Shot compiler (rmdev Phase 13): story beats -> canonical ShotSpecs.

LTX is downstream of canonical simulation. This module maps an episode's beats
into ShotSpec objects (media.py) that are schema-valid and carry canonical
constraints (winner, event order, identity) so the renderer can dramatize but
never contradict canon (Constitution rule 7).
"""
from __future__ import annotations

from .media import (
    ShotSpec, build_shot_spec, shot_class_for,
    CONTROL_MODES, SHOT_CLASS_CONTROL,
)


def compile_shots(episode: dict, asset_library=None, agents=None,
                  body_versions=None, blade_id_map=None) -> dict:
    """Compile an episode dict (from story.compile_story) into ShotSpecs.

    If an AssetLibrary is provided, canonical talisman/daimon/arena assets are
    resolved into each ShotSpec's `references` so LTX never re-invents them.

    `agents` maps agent_id -> AgentState and `body_versions` maps agent_id ->
    body version string. `blade_id_map` maps blade_id (as keyed in
    episode["characters"]) -> agent_id, so body/agent identity never collide
    (rmreview #12/#20). When present, the daimon is resolved from the agent's
    actual DaimonState and entity versions use the real body version.
    """
    from .assets import AssetLibrary
    lib = asset_library or AssetLibrary()
    agents = agents or {}
    body_versions = body_versions or {}
    blade_id_map = blade_id_map or {}
    replay_digest = episode.get("replay_digest", "")
    match_id = episode.get("match_id", "")
    winner = episode.get("winner")
    entity_versions = _entity_versions(episode, agents, body_versions, blade_id_map)
    arena_refs = _arena_references(lib)
    shots: list[ShotSpec] = []

    # Shot 1: establishing arena (loose, T2V).
    shots.append(build_shot_spec(
        shot_id=f"{match_id}-establish",
        canonicality="RECONSTRUCTION",
        prompt=("Establish the fictional virtual arena and both competitors before "
                "the match. No outcome implied."),
        duration_s=5.0,
        constraints=["both competitors visible", "no outcome implication"],
        entity_versions=entity_versions,
        environment_version="arena:season-01",
        event_ids=[],
        references=arena_refs,
        qa=["no outcome implied", "identity preserved"],
        shot_class="establish_arena",
    ))

    # Shot 2: competitor intro (I2V with canonical refs).
    for blade_id in episode.get("characters", {}):
        aid = blade_id_map.get(blade_id, blade_id)  # blade_id -> agent_id
        agent = agents.get(aid)
        bv = body_versions.get(aid, "")
        shots.append(build_shot_spec(
            shot_id=f"{match_id}-intro-{aid}",
            canonicality="RECONSTRUCTION",
            prompt=f"Intro the competitor {aid} in its canonical talisman form.",
            duration_s=4.0,
            constraints=[f"identity {aid} preserved", "no outcome implied"],
            entity_versions=_entity_versions(episode, agents, body_versions,
                                             blade_id_map, only=aid),
            environment_version="arena:season-01",
            references=_competitor_references(lib, aid, agent, bv),
            qa=[f"identity {aid} preserved"],
            shot_class="competitor_intro",
        ))

    # Beats -> battle-event / result shots (KEYFRAME / RETAKE), ShotSpec v2.
    from .media import ControlPlanner
    planner = ControlPlanner()
    for i, b in enumerate(episode.get("beats", [])[:10]):
        shot_class = shot_class_for(b.get("type", "battle_event"))
        is_result = b.get("type") == "round_result"
        canon_c = [f"round={b.get('round')}", "do not invent a different result"]
        if winner:
            canon_c.append(f"winner={winner}")
        basis_events = b.get("basis_event_ids", [])
        preferred, fallback = planner.plan(
            canonicality="CANONICAL_EVENT" if not is_result else "RECONSTRUCTION",
            shot_class=shot_class,
            has_basis_events=bool(basis_events),
        )
        shots.append(build_shot_spec(
            shot_id=f"{match_id}-beat-{i:03d}",
            canonicality="CANONICAL_EVENT" if not is_result else "RECONSTRUCTION",
            prompt=f"Visualize canonical beat: {b.get('summary', b.get('type'))}. "
                   "Preserve event order and competitor identity.",
            duration_s=6.0 if b.get("importance", 0) >= 0.9 else 4.0,
            constraints=canon_c,
            entity_versions=entity_versions,
            environment_version="arena:season-01",
            event_ids=[f"{match_id}:{b.get('t', i)}"],
            basis_event_ids=basis_events,
            camera={"style": "impact_close" if b.get("type") == "collision" else "result_wide"},
            references=arena_refs,
            control={"preferred": preferred, "fallback": fallback},
            control_mode=preferred,
            qa=["event ordering matches replay", "winner/outcome not contradicted",
                "identity refs preserved"],
            shot_class=shot_class,
        ))

    return {
        "episode_id": episode.get("episode_id"),
        "match_id": match_id,
        "replay_digest": replay_digest,
        "renderer": "LTX-2.5/ComfyUI (replaceable)",
        "shots": [s.to_dict() for s in shots],
        "control_modes": list(SHOT_CLASS_CONTROL),
    }


def _entity_versions(episode: dict, agents=None, body_versions=None,
                     blade_id_map=None, only: str = "") -> list[str]:
    """Derive canonical entity_versions using the ACTUAL body version, not `v0`."""
    agents = agents or {}
    body_versions = body_versions or {}
    blade_id_map = blade_id_map or {}
    versions = []
    for blade_id in episode.get("characters", {}):
        aid = blade_id_map.get(blade_id, blade_id)
        if only and aid != only:
            continue
        bv = body_versions.get(aid, "")
        # rmart #24: never resolve an unversioned persistent entity.
        version_str = bv if bv else "R1"
        versions.append(f"{aid}:talisman:mech-{version_str}")
    return versions


def _competitor_references(lib, agent_id: str, agent=None,
                          body_version: str = "") -> list[dict]:
    """Resolve canonical talisman/daimon assets, version-constrained.

    The daimon is resolved from the agent's ACTUAL DaimonState (its `name`),
    not a hard-coded Boris->Penelope map (rmreview #11). The talisman lookup is
    constrained to the agent's mechanical body version.
    """
    refs = []
    for asset in lib.references_for(agent_id, mechanical_version=body_version):
        refs.append(_asset_ref(asset))
    # Daimon resolved from canon/agent state.
    daimon_entity = _daimon_entity_for(agent)
    if daimon_entity:
        for asset in lib.references_for(daimon_entity):
            refs.append(_asset_ref(asset))
    return refs


def _daimon_entity_for(agent) -> str:
    """Resolve the daimon entity id from the agent's DaimonState (if manifested).

    A latent/unnamed daimon has NO canonical manifestation asset yet (rmart #33):
    only a MANIFEST-stage daimon with a name resolves to an asset entity.
    """
    if agent is None or agent.daimon is None:
        return ""
    if agent.daimon.name and agent.daimon.stage == "manifest":
        return agent.daimon.name.lower()
    return ""


def _asset_ref(asset) -> dict:
    return {"type": asset.asset_type, "view": asset.view,
            "asset_key": asset.asset_key(), "uri": asset.file_uri,
            "mechanical_version": asset.mechanical_version,
            "digest": asset.digest()}


def _arena_references(lib) -> list[dict]:
    """Resolve canonical arena/world assets."""
    refs = []
    for entity in ("arena-s1", "world-s1"):
        for asset in lib.references_for(entity):
            refs.append(_asset_ref(asset))
    return refs
