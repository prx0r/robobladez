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


def compile_shots(episode: dict, asset_library=None) -> dict:
    """Compile an episode dict (from story.compile_story) into ShotSpecs.

    If an AssetLibrary is provided, canonical talisman/daimon/arena assets are
    resolved into each ShotSpec's `references` so LTX never re-invents them.
    """
    from .assets import AssetLibrary
    lib = asset_library or AssetLibrary()
    replay_digest = episode.get("replay_digest", "")
    match_id = episode.get("match_id", "")
    winner = episode.get("winner")
    entity_versions = _entity_versions(episode)
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
    for aid, aid_versions in episode.get("characters", {}).items():
        shots.append(build_shot_spec(
            shot_id=f"{match_id}-intro-{aid}",
            canonicality="RECONSTRUCTION",
            prompt=f"Intro the competitor {aid} in its canonical talisman form.",
            duration_s=4.0,
            constraints=[f"identity {aid} preserved", "no outcome implied"],
            entity_versions=aid_versions,
            environment_version="arena:season-01",
            references=_competitor_references(lib, aid),
            qa=[f"identity {aid} preserved"],
            shot_class="competitor_intro",
        ))

    # Beats -> battle-event / result shots (KEYFRAME / RETAKE).
    for i, b in enumerate(episode.get("beats", [])[:10]):
        shot_class = shot_class_for(b.get("type", "battle_event"))
        is_result = b.get("type") == "round_result"
        canon_c = [f"round={b.get('round')}", "do not invent a different result"]
        if winner:
            canon_c.append(f"winner={winner}")
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
            camera={"style": "impact_close" if b.get("type") == "collision" else "result_wide"},
            references=arena_refs,
            qa=["event ordering matches replay", "winner/outcome not contradicted",
                "identity refs preserved"],
            shot_class=shot_class,
        ))

    return {
        "episode_id": episode.get("episode_id"),
        "match_id": match_id,
        "replay_digest": replay_digest,
        "renderer": "LTX-2.3/ComfyUI (replaceable)",
        "shots": [s.to_dict() for s in shots],
        "control_modes": list(SHOT_CLASS_CONTROL),
    }


def _entity_versions(episode: dict) -> list[str]:
    """Derive canonical entity_versions from episode characters (phenotype/daimon)."""
    versions = []
    for aid in episode.get("characters", {}):
        versions.append(f"{aid}:talisman:v0")
    return versions


def _competitor_references(lib, agent_id: str) -> list[dict]:
    """Resolve canonical talisman/daimon assets for an agent into reference dicts."""
    refs = []
    for asset in lib.references_for(agent_id):
        refs.append({"type": asset.asset_type, "view": asset.view,
                     "asset_key": asset.asset_key(), "uri": asset.file_uri,
                     "digest": asset.digest()})
    # Also include the canonical daimon entity if present (e.g. penelope).
    daimon_id = _daimon_for(agent_id)
    if daimon_id:
        for asset in lib.references_for(daimon_id):
            refs.append({"type": asset.asset_type, "view": asset.view,
                         "asset_key": asset.asset_key(), "uri": asset.file_uri,
                         "digest": asset.digest()})
    return refs


def _arena_references(lib) -> list[dict]:
    """Resolve canonical arena/world assets."""
    refs = []
    for entity in ("arena-s1", "world-s1"):
        for asset in lib.references_for(entity):
            refs.append({"type": asset.asset_type, "view": asset.view,
                         "asset_key": asset.asset_key(), "uri": asset.file_uri,
                         "digest": asset.digest()})
    return refs


def _daimon_for(agent_id: str) -> str:
    # Mapping of known agent -> daimon entity id (narrative projection).
    return {"boris": "penelope"}.get(agent_id, "")
