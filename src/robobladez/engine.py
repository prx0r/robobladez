from __future__ import annotations
from dataclasses import asdict
import hashlib, json, math, random
from .model import *
from .policy import Policy, commitment, manifest
from .physics import integrate_free, resolve_disk_collision

ENGINE_VERSION = "rbz-core-0.2.0"

def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False)

def replay_digest_dict(d: dict) -> str:
    x = dict(d)
    x["replay_digest"] = ""
    return hashlib.sha256(canonical_json(x).encode()).hexdigest()

def _match_id(seed: int, a: str, b: str, arena: ArenaSpec) -> str:
    raw=f"{ENGINE_VERSION}|{seed}|{a}|{b}|{arena.id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:20]

def _initial_state(spec: BladeSpec, angle: float, arena: ArenaSpec, spin_sign: float) -> BladeState:
    r=arena.radius*arena.launch_radius_fraction
    pos=Vec2(math.cos(angle)*r, math.sin(angle)*r)
    tangent=pos.unit().perp()
    vel=tangent*(spec.launch_speed*spin_sign)
    return BladeState(spec.id,pos,vel,spec.launch_spin*spin_sign,
                      spec.energy_capacity,spec.integrity)

def _obs(tick, round_no, me, opp, arena, priors):
    return Observation(
        tick,round_no,me.pos,me.vel,me.omega,me.energy,me.integrity,
        opp.pos,opp.vel,opp.omega,opp.energy,opp.integrity,arena.radius,priors
    )

def _frame(tick,arena,states,actions):
    return Frame(
        tick,tick*arena.dt,
        {k:{
            "pos":{"x":v.pos.x,"y":v.pos.y},
            "vel":{"x":v.vel.x,"y":v.vel.y},
            "omega":v.omega,"energy":v.energy,"integrity":v.integrity,
            "center_time":v.center_time
        } for k,v in states.items()},
        {k:asdict(v) for k,v in actions.items()}
    )

def _terminal(state: BladeState, spec: BladeSpec, arena: ArenaSpec, t: float) -> str|None:
    if state.pos.norm()-spec.radius > arena.radius:
        return "ring_out"
    if state.integrity <= 0:
        return "burst"
    if t >= arena.spinout_grace_s and abs(state.omega) < arena.min_spin:
        return "spin_out"
    return None

def run_round(round_no:int,seed:int,arena:ArenaSpec,sa:BladeSpec,sb:BladeSpec,
              pa:Policy,pb:Policy,priors:tuple[str|None,...]=(),record_frames:bool=True) -> RoundResult:
    sa.validate(); sb.validate(); arena.validate()
    rng=random.Random(seed)
    j=rng.uniform(-arena.launch_jitter_rad,arena.launch_jitter_rad)
    a=_initial_state(sa,j,arena,1.0)
    b=_initial_state(sb,math.pi-j,arena,1.0)
    states={a.id:a,b.id:b}
    frames=[]; events=[]
    max_ticks=math.ceil(arena.max_seconds/arena.dt)

    for tick in range(max_ticks):
        t=tick*arena.dt

        # Both policies observe the identical pre-resolution world state.
        aa=pa.decide(_obs(tick,round_no,a,b,arena,priors)).clamped()
        ab=pb.decide(_obs(tick,round_no,b,a,arena,priors)).clamped()

        # Energy gates actuator authority without changing chosen action in replay.
        aa_eff=aa if a.energy>0 else Action()
        ab_eff=ab if b.energy>0 else Action()

        integrate_free(a,sa,arena,aa_eff)
        integrate_free(b,sb,arena,ab_eff)

        ev=resolve_disk_collision(a,b,sa,sb,arena,tick)
        if ev: events.append(ev)

        if not a.finite() or not b.finite():
            raise FloatingPointError(f"non-finite state at tick {tick}")

        if record_frames and tick%4==0:
            frames.append(_frame(tick,arena,states,{a.id:aa,b.id:ab}))

        ta=_terminal(a,sa,arena,t+arena.dt)
        tb=_terminal(b,sb,arena,t+arena.dt)
        if ta or tb:
            if ta and not tb:
                winner=b.id; reason=ta
            elif tb and not ta:
                winner=a.id; reason=tb
            else:
                winner=None; reason=f"double_{ta or tb}"
            events.append(Event(tick,t,"round_end",winner,None,1.0,
                                {"reason":reason}))
            return RoundResult(round_no,seed,winner,reason,frames,events)

    events.append(Event(max_ticks-1,arena.max_seconds,"round_end",None,None,0.6,
                        {"reason":"time_draw"}))
    return RoundResult(round_no,seed,None,"time_draw",frames,events)

def run_match(seed:int,arena:ArenaSpec,sa:BladeSpec,sb:BladeSpec,
              pa:Policy,pb:Policy,rounds:int=5,record_frames:bool=True,
              reincarnation_bindings:dict[str,dict]|None=None) -> MatchResult:
    if rounds<1 or rounds%2==0: raise ValueError("rounds must be positive odd")
    if sa.id==sb.id: raise ValueError("blade ids must differ")
    mid=_match_id(seed,sa.id,sb.id,arena)
    nonce=f"{mid}|{seed}|{ENGINE_VERSION}"
    manifests={sa.id:manifest(pa),sb.id:manifest(pb)}
    commits={sa.id:commitment(pa,nonce),sb.id:commitment(pb,nonce)}
    wins={sa.id:0,sb.id:0}
    results=[]; priors=()
    majority=rounds//2+1

    for n in range(1,rounds+1):
        rr=run_round(n,seed+n*1000003,arena,sa,sb,pa,pb,priors,record_frames=record_frames)
        results.append(rr)
        priors=priors+(rr.winner,)
        if rr.winner:
            wins[rr.winner]+=1
        if wins[sa.id]>=majority or wins[sb.id]>=majority:
            break

    if wins[sa.id]>wins[sb.id]:
        winner=sa.id
    elif wins[sb.id]>wins[sa.id]:
        winner=sb.id
    else:
        winner=None

    bindings = {
        k: dict(v) for k, v in (reincarnation_bindings or {}).items()
    } if reincarnation_bindings else {}
    m=MatchResult(mid,ENGINE_VERSION,seed,asdict(arena),
                  {sa.id:asdict(sa),sb.id:asdict(sb)},
                  manifests,commits,results,wins,winner,
                  reincarnation_bindings=bindings)
    d=m.to_dict()
    m.replay_digest=replay_digest_dict(d)
    return m

def verify_replay_digest(match: MatchResult) -> bool:
    return match.replay_digest == replay_digest_dict(match.to_dict())
