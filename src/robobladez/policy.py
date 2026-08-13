from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Protocol
import hashlib, inspect, json, math
from functools import lru_cache
from .model import Action, Observation

class Policy(Protocol):
    id: str
    def decide(self, obs: Observation) -> Action: ...
    def public_config(self) -> dict: ...

@lru_cache(maxsize=128)
def _class_code_fingerprint(cls: type) -> str:
    try:
        src = inspect.getsource(cls)
    except (OSError, TypeError):
        src = f"{cls.__module__}.{cls.__qualname__}"
    return hashlib.sha256(src.encode()).hexdigest()

def _code_fingerprint(policy: Policy) -> str:
    return _class_code_fingerprint(policy.__class__)

def manifest(policy: Policy) -> dict:
    return {
        "policy_id": policy.id,
        "class": f"{policy.__class__.__module__}.{policy.__class__.__qualname__}",
        "config": policy.public_config(),
        "code_sha256": _code_fingerprint(policy),
        "api_version": "rbz-policy-1",
    }

def commitment(policy: Policy, match_nonce: str) -> str:
    payload = {"manifest": manifest(policy), "match_nonce": match_nonce}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(canonical).hexdigest()

@dataclass
class PassivePolicy:
    id: str = "passive-v1"
    def public_config(self) -> dict: return asdict(self)
    def decide(self, obs: Observation) -> Action: return Action()

@dataclass
class CenterControlPolicy:
    id: str = "center-control-v2"
    inward: float = 0.65
    orbit: float = 0.15
    spin_conserve: float = 0.10
    def public_config(self) -> dict: return asdict(self)
    def decide(self, obs: Observation) -> Action:
        r = obs.self_pos.norm()/obs.arena_radius
        radial = self.inward if r > 0.35 else 0.10
        return Action(radial=radial, tangential=self.orbit,
                      torque=self.spin_conserve if obs.self_omega < 260 else 0.0,
                      boost=0.38)

@dataclass
class AggressivePolicy:
    id: str = "aggressive-v2"
    chase_gain: float = 0.85
    boost: float = 0.90
    def public_config(self) -> dict: return asdict(self)
    def decide(self, obs: Observation) -> Action:
        rfrac = obs.self_pos.norm()/obs.arena_radius
        if rfrac > 0.74:
            # An aggressive policy should still protect itself from trivial self-ring-outs.
            return Action(radial=1.0, tangential=0.08, torque=0.04, boost=0.82)
        # Convert opponent direction into arena radial/tangential basis.
        to_opp = (obs.opponent_pos - obs.self_pos).unit()
        rhat = obs.self_pos.unit()
        that = rhat.perp()
        desired_inward = -to_opp.dot(rhat)
        desired_tangent = to_opp.dot(that)
        return Action(radial=self.chase_gain*desired_inward,
                      tangential=self.chase_gain*desired_tangent,
                      torque=0.05, boost=self.boost)

@dataclass
class CounterPolicy:
    id: str = "counter-v2"
    center_bias: float = 0.55
    evade: float = 0.65
    punish_distance: float = 0.115
    def public_config(self) -> dict: return asdict(self)
    def decide(self, obs: Observation) -> Action:
        delta = obs.opponent_pos - obs.self_pos
        distance = delta.norm()
        closing = 0.0
        if distance > 1e-12:
            closing = -(obs.opponent_vel - obs.self_vel).dot(delta.unit())
        if distance < self.punish_distance and closing > 0.12:
            # lateral evade + conserve spin
            return Action(radial=0.35, tangential=self.evade, torque=0.10, boost=0.72)
        return Action(radial=self.center_bias, tangential=0.12, torque=0.03, boost=0.30)
