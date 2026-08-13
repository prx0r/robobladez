"""Story compiler (rmdev2 Phase 8).

Canonical events -> SignificanceDetector -> EpisodeSpec -> StoryBeat[].
Beats REFERENCE canonical event IDs (basis_event_ids); they never substitute
for them. The story may interpret events, never invent them.
"""
from __future__ import annotations

from .canonical import extract_canonical_events
from .significance import SignificanceDetector, StoryBeat


def compile_story(match, analysis, execution_digest: str = ""):
    """Compile canonical events into a story episode with basis_event_ids."""
    events = extract_canonical_events(match, execution_digest=execution_digest)
    detector = SignificanceDetector()
    beats: list[StoryBeat] = detector.detect(events)
    return {
        "episode_id": f"EP-{match.match_id}",
        "match_id": match.match_id,
        "replay_digest": match.replay_digest,
        "execution_digest": execution_digest,
        "winner": match.winner,
        "canonical_event_ids": [e.event_id for e in events],
        "beats": [b.to_dict() for b in beats],
        "characters": {
            bid: {"phenotype": v["phenotype"], "daimon": v["daimon_projection"]}
            for bid, v in analysis.items()
        },
        "hard_constraints": [
            "winner must match canonical replay",
            "round order may not change",
            "events may be omitted/compressed but not contradicted",
            "narrative daimon projection may not alter simulation facts",
            "beats reference canonical event IDs; the story may not invent events",
        ],
    }
