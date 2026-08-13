from __future__ import annotations
from collections import defaultdict
import math
from .model import MatchResult

def analyze_behavior(match: MatchResult) -> dict:
    # Raw phenotype is evidence. Element affinity is merely a narrative projection.
    acc={bid:defaultdict(float) for bid in match.blades}
    count={bid:0 for bid in match.blades}

    for rnd in match.rounds:
        for fr in rnd.frames:
            ids=list(fr.states)
            for bid in ids:
                s=fr.states[bid]; a=fr.actions[bid]
                speed=math.hypot(s["vel"]["x"],s["vel"]["y"])
                radius=math.hypot(s["pos"]["x"],s["pos"]["y"])
                x=acc[bid]; count[bid]+=1
                x["speed"]+=speed
                x["abs_spin"]+=abs(s["omega"])
                x["center"]+=1 if radius < match.arena["radius"]*0.28 else 0
                x["boost"]+=a["boost"]
                x["radial_in"]+=max(0,a["radial"])
                x["radial_out"]+=max(0,-a["radial"])
                x["orbit"]+=abs(a["tangential"])
                x["torque"]+=abs(a["torque"])
        for e in rnd.events:
            if e.type=="collision":
                for bid in (e.actor,e.target):
                    if bid in acc:
                        acc[bid]["collisions"]+=1
                        acc[bid]["impulse"]+=e.data.get("total_impulse",0)
            if e.type=="round_end" and e.actor in acc:
                acc[e.actor]["round_wins"]+=1

    out={}
    for bid,x in acc.items():
        n=max(1,count[bid]); nr=max(1,len(match.rounds))
        raw={
            "avg_speed":x["speed"]/n,
            "avg_abs_spin":x["abs_spin"]/n,
            "center_fraction":x["center"]/n,
            "avg_boost":x["boost"]/n,
            "inward_control":x["radial_in"]/n,
            "outward_control":x["radial_out"]/n,
            "orbit_control":x["orbit"]/n,
            "torque_control":x["torque"]/n,
            "collisions_per_round":x["collisions"]/nr,
            "impulse_per_round":x["impulse"]/nr,
            "round_win_fraction":x["round_wins"]/nr,
        }
        out[bid]={"phenotype":raw,"daimon_projection":project_daimon(raw)}
    return out

def project_daimon(p:dict)->dict:
    # Explicitly editorial mappings. They never affect the match outcome.
    norm_speed=min(1,p["avg_speed"]/1.0)
    norm_col=min(1,p["collisions_per_round"]/10)
    earth=.50*p["center_fraction"]+.30*(1-p["avg_boost"])+.20*(1-norm_speed)
    fire=.50*p["avg_boost"]+.30*norm_col+.20*p["inward_control"]
    air=.45*norm_speed+.35*p["orbit_control"]+.20*p["outward_control"]
    water=.40*p["orbit_control"]+.35*p["center_fraction"]+.25*(1-abs(.45-p["avg_boost"]))
    aether=.35*p["torque_control"]+.35*p["outward_control"]+.30*p["avg_boost"]
    raw={"earth":max(0,earth),"water":max(0,water),"fire":max(0,fire),
         "air":max(0,air),"aether":max(0,aether)}
    total=sum(raw.values()) or 1
    aff={k:v/total for k,v in raw.items()}
    return {
        "status":"NARRATIVE_PROJECTION",
        "affinities":aff,
        "dominant":max(aff,key=aff.get),
        "note":"Derived from measured playstyle; has no causal power in v2."
    }
