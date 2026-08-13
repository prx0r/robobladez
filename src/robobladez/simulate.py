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
    episode = compile_story(outcome.match, outcome.analysis)
    shots_dict = compile_shots(episode)
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
        "replay_digest": outcome.match.replay_digest,
        "reincarnations": {k: v.manifest.reincarnation_id
                           for k, v in outcome.avatars.items()},
        "episode_id": episode["episode_id"],
        "media": {
            "shots": media["shots"],
            "accepted": media["accepted"],
            "rejected": media["rejected"],
        },
    }


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
