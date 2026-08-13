from __future__ import annotations
import math
from collections import Counter
from .model import BladeSpec,ArenaSpec
from .policy import AggressivePolicy,CounterPolicy,CenterControlPolicy,PassivePolicy
from .engine import run_match,verify_replay_digest,run_round

def _passive_energy_check():
    a=BladeSpec("energy-a"); b=BladeSpec("energy-b")
    rr=run_round(1,77,ArenaSpec(max_seconds=3.0),a,b,PassivePolicy(),PassivePolicy(),())
    first,last=rr.frames[0].states,rr.frames[-1].states
    def E(s,spec):
        vx,vy=s["vel"]["x"],s["vel"]["y"]
        return .5*spec.mass*(vx*vx+vy*vy)+.5*spec.inertia*s["omega"]**2
    e0=E(first[a.id],a)+E(first[b.id],b)
    e1=E(last[a.id],a)+E(last[b.id],b)
    return e0,e1,e1<=e0*(1+1e-9)

def run_audit(seeds:int=250)->dict:
    # Tier 1: cheap numerical/canon fuzzing. Short rounds, no frame retention.
    short=ArenaSpec(max_seconds=1.5)
    a=BladeSpec("audit-a")
    b=BladeSpec("audit-b",mass=.060,radius=.033,launch_spin=590)
    pa,pb=CounterPolicy(),AggressivePolicy()
    digest_ok=0; finite_rounds=0
    for seed in range(seeds):
        m=run_match(seed,short,a,b,pa,pb,3,record_frames=False)
        digest_ok+=int(verify_replay_digest(m))
        # run_round itself raises on any non-finite state
        finite_rounds+=len(m.rounds)

    # Tier 2: gameplay sanity over longer matches.
    long=ArenaSpec(max_seconds=10.0)
    matchups=[
        ("counter_vs_aggressive",CounterPolicy(),AggressivePolicy()),
        ("aggressive_vs_counter",AggressivePolicy(),CounterPolicy()),
        ("center_vs_aggressive",CenterControlPolicy(),AggressivePolicy()),
        ("aggressive_vs_aggressive",AggressivePolicy(),AggressivePolicy()),
    ]
    gameplay={}
    gameplay_seeds=max(4,min(12,seeds//25 or 4))
    for name,p1,p2 in matchups:
        winners=Counter(); reasons=Counter()
        for seed in range(gameplay_seeds):
            m=run_match(900000+seed,long,BladeSpec("left"),BladeSpec("right"),p1,p2,3,record_frames=False)
            winners[m.winner or "draw"]+=1
            for r in m.rounds: reasons[r.reason]+=1
        gameplay[name]={"matches":gameplay_seeds,"winners":dict(winners),"round_reasons":dict(reasons)}

    d1=run_match(987654321,short,a,b,pa,pb,5,record_frames=False).to_dict()
    d2=run_match(987654321,short,a,b,pa,pb,5,record_frames=False).to_dict()

    e0,e1,eok=_passive_energy_check()
    return {
      "numerical_fuzz_seeds":seeds,
      "deterministic_exact":d1==d2,
      "digest_valid_matches":digest_ok,
      "finite_rounds":finite_rounds,
      "passive_energy_initial":e0,
      "passive_energy_final":e1,
      "passive_energy_nonincreasing":eok,
      "gameplay_sample":gameplay,
      "interpretation":{
        "numerical":"PASS if deterministic, all digests valid, no non-finite exception, passive energy non-increasing",
        "gameplay":"Sanity only. v2 does NOT claim balanced or non-transitive strategy; those are M1 exit criteria."
      }
    }
