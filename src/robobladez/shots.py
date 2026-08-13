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


def compile_shots(episode: dict) -> dict:
    """Compile an episode dict (from story.compile_story) into ShotSpecs."""
    replay_digest = episode.get("replay_digest", "")
    match_id = episode.get("match_id", "")
    winner = episode.get("winner")
    entity_versions = _entity_versions(episode)
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
