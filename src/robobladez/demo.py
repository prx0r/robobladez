from pathlib import Path
import json
from .model import BladeSpec,ArenaSpec
from .policy import CounterPolicy,AggressivePolicy,PassivePolicy
from .engine import run_match
from .replay import save_match,save_canonical
from .analysis import analyze_behavior
from .canon import CanonStore
from .story import compile_story
from .shots import compile_shots

def run_demo(out_dir):
    out=Path(out_dir); out.mkdir(parents=True,exist_ok=True)
    boris=BladeSpec("boris",mass=.058,radius=.033,contact_friction=.34,launch_spin=610)
    morty=BladeSpec("morty",mass=.052,radius=.031,control_force=.023,launch_spin=640)
    arena=ArenaSpec()

    # Public mechanical baseline: same bodies, passive policies.
    baseline=run_match(424241,arena,boris,morty,PassivePolicy(),PassivePolicy(),3)
    save_match(baseline,out/"mechanical_baseline.json")

    # Strategic match: policies are fingerprinted and committed.
    match=run_match(424242,arena,boris,morty,CounterPolicy(),AggressivePolicy(),5)
    save_match(match,out/"match.json")
    save_canonical(match,out/"match.canonical.json")

    analysis=analyze_behavior(match)
    (out/"analysis.json").write_text(json.dumps(analysis,indent=2),encoding="utf-8")
    episode=compile_story(match,analysis)
    (out/"episode.json").write_text(json.dumps(episode,indent=2),encoding="utf-8")
    shots=compile_shots(episode)
    (out/"shots.json").write_text(json.dumps(shots,indent=2),encoding="utf-8")

    store=CanonStore(out/"canon.sqlite3"); store.save_match(match)
    return {
      "mechanical_baseline_winner":baseline.winner,
      "strategic_winner":match.winner,
      "match_id":match.match_id,
      "replay_digest":match.replay_digest,
      "canon_matches":store.count()
    }
