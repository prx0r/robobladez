from pathlib import Path
import json
from .agent import AgentState
from .battle import run_battle
from .canon import CanonStore
from .zoo import make_body


def run_demo(out_dir, mechanical_runs: int = 40, strategic_rounds: int = 5,
             base_seed: int = 9000):
    """Run the hardened two-phase battle flow (reincarnation) end-to-end.

    Boris vs Morty: mechanical reveal -> authored sealed reincarnations ->
    best-of-N -> transactional evolution -> story + shot specs -> canon.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    boris = AgentState("boris")
    morty = AgentState("morty")

    outcome = run_battle(
        boris, make_body("balanced", "-boris"),
        morty, make_body("heavy", "-morty"),
        mechanical_runs=mechanical_runs, strategic_rounds=strategic_rounds,
        base_seed=base_seed,
    )

    # Canonical artifacts.
    from .replay import save_match, save_canonical
    save_match(outcome.match, out / "match.json")
    save_canonical(outcome.match, out / "match.canonical.json")

    # Mechanical baseline (public evidence) + analysis.
    (out / "mechanical_baseline.json").write_text(
        json.dumps(outcome.mechanical.to_dict(), indent=2), encoding="utf-8")
    (out / "analysis.json").write_text(
        json.dumps(outcome.analysis, indent=2), encoding="utf-8")
    (out / "battle_outcome.json").write_text(
        json.dumps(outcome.to_dict(), indent=2), encoding="utf-8")

    # Story -> shot specs (LTX downstream, renderer-agnostic).
    from .story import compile_story
    from .shots import compile_shots
    episode = compile_story(outcome.match, outcome.analysis)
    (out / "episode.json").write_text(json.dumps(episode, indent=2), encoding="utf-8")
    shots = compile_shots(episode)
    (out / "shots.json").write_text(json.dumps(shots, indent=2), encoding="utf-8")

    # Canon store (digest-verified).
    store = CanonStore(out / "canon.sqlite3")
    store.save_match(outcome.match)

    return {
        "mechanical_win_probability": outcome.mechanical.win_probability,
        "strategic_winner": outcome.winner_agent_id(),
        "match_id": outcome.match.match_id,
        "replay_digest": outcome.match.replay_digest,
        "reincarnations": {k: v.manifest.reincarnation_id
                           for k, v in outcome.avatars.items()},
        "canon_matches": store.count(),
    }
