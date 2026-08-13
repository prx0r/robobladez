"""Policy + body archetypes per the canonical dev guide (rmdev Phase 1).

12 named policy archetypes and 8 named body archetypes. Each policy is a pure
Observation -> Action function (no engine access), sealable and fingerprintable.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import math

from .model import Action, Observation, BladeSpec
from .policy import CenterControlPolicy, AggressivePolicy, CounterPolicy, PassivePolicy


# ---------------------------------------------------------------------------
# 12 policy archetypes (rmdev 1.1)
# ---------------------------------------------------------------------------
@dataclass
class CenterPolicy:
    """Holds central control."""
    id: str = "center"
    target_radius: float = 0.15

    def public_config(self) -> dict:
        return asdict(self)

    def decide(self, obs: Observation) -> Action:
        r = obs.self_pos.norm() / obs.arena_radius
        radial = (self.target_radius - r) * 1.2
        return Action(radial=radial, tangential=0.15,
                      torque=0.05 if obs.self_omega < 300 else 0.0, boost=0.35)


@dataclass
class RushPolicy:
    """Maximizes early contact with high commitment."""
    id: str = "rush"
    boost: float = 1.0

    def public_config(self) -> dict:
        return asdict(self)

    def decide(self, obs: Observation) -> Action:
        to_opp = (obs.opponent_pos - obs.self_pos).unit()
        rhat = obs.self_pos.unit()
        that = rhat.perp()
        inward = -to_opp.dot(rhat)
        tangent = to_opp.dot(that)
        r = obs.self_pos.norm() / obs.arena_radius
        if r > 0.78:  # protect from self ring-out
            return Action(radial=1.0, tangential=tangent, torque=0.0, boost=0.7)
        return Action(radial=0.9 * inward, tangential=0.9 * tangent,
                      torque=0.0, boost=self.boost)


@dataclass
class OrbitPolicy:
    """Maintains tangential separation."""
    id: str = "orbit"
    target_fraction: float = 0.50
    orbit_dir: float = 1.0
    boost: float = 0.25

    def public_config(self) -> dict:
        return asdict(self)

    def decide(self, obs: Observation) -> Action:
        r = obs.self_pos.norm() / obs.arena_radius
        radial = (self.target_fraction - r) * 1.2
        tangential = self.orbit_dir * (1.0 if r > 0.2 else 0.2)
        return Action(radial=radial, tangential=tangential,
                      torque=0.1 if obs.self_omega < 300 else 0.0, boost=self.boost)


@dataclass
class CounterPolicyGuide:
    """Punishes closing velocity (subclass of the shipped CounterPolicy)."""
    id: str = "counter"

    def public_config(self) -> dict:
        return asdict(self)

    def decide(self, obs: Observation) -> Action:
        delta = obs.opponent_pos - obs.self_pos
        distance = delta.norm()
        closing = 0.0
        if distance > 1e-12:
            closing = -(obs.opponent_vel - obs.self_vel).dot(delta.unit())
        if distance < 0.115 and closing > 0.12:
            return Action(radial=0.35, tangential=0.65, torque=0.10, boost=0.72)
        return Action(radial=0.55, tangential=0.12, torque=0.03, boost=0.30)


@dataclass
class EdgeBaitPolicy:
    """Deliberately approaches the rim to lure a chase, then exploits overshoot."""
    id: str = "edge-bait"
    bait_fraction: float = 0.82
    boost: float = 0.40

    def public_config(self) -> dict:
        return asdict(self)

    def decide(self, obs: Observation) -> Action:
        r = obs.self_pos.norm() / obs.arena_radius
        to_opp = obs.opponent_pos - obs.self_pos
        dist = to_opp.norm()
        if r < self.bait_fraction - 0.05:
            return Action(radial=-0.8, tangential=0.3, torque=0.05, boost=self.boost)
        # At the bait point, wait then cut tangential to let them overshoot.
        return Action(radial=0.2, tangential=0.9 if dist < 0.15 else -0.9,
                      torque=0.05, boost=self.boost)


@dataclass
class SpinSaverPolicy:
    """Minimizes actuator cost to preserve energy/spin for a long match."""
    id: str = "spin-saver"
    boost: float = 0.05

    def public_config(self) -> dict:
        return asdict(self)

    def decide(self, obs: Observation) -> Action:
        r = obs.self_pos.norm() / obs.arena_radius
        radial = 0.8 if r > 0.7 else 0.0
        return Action(radial=radial, tangential=0.05, torque=0.0, boost=self.boost)


@dataclass
class LateBurstPolicy:
    """Conserves energy until the opponent weakens, then bursts."""
    id: str = "late-burst"
    conserve_boost: float = 0.08
    burst_boost: float = 1.0
    burst_opp_integrity: float = 60.0

    def public_config(self) -> dict:
        return asdict(self)

    def decide(self, obs: Observation) -> Action:
        r = obs.self_pos.norm() / obs.arena_radius
        opp_weak = obs.opponent_integrity < self.burst_opp_integrity or \
            obs.opponent_energy < 25.0
        if opp_weak:
            return Action(radial=0.7, tangential=0.5, torque=0.1,
                          boost=self.burst_boost)
        return Action(radial=0.5 if r > 0.6 else -0.1, tangential=0.15,
                      torque=0.0, boost=self.conserve_boost)


@dataclass
class PressurePolicy:
    """Constant controlled engagement, never fully committing."""
    id: str = "pressure"
    boost: float = 0.55

    def public_config(self) -> dict:
        return asdict(self)

    def decide(self, obs: Observation) -> Action:
        to_opp = (obs.opponent_pos - obs.self_pos).unit()
        rhat = obs.self_pos.unit()
        that = rhat.perp()
        inward = -to_opp.dot(rhat)
        tangent = to_opp.dot(that)
        r = obs.self_pos.norm() / obs.arena_radius
        radial = 0.8 * inward if r < 0.7 else 1.0
        return Action(radial=radial, tangential=0.4 * tangent,
                      torque=0.03, boost=self.boost)


@dataclass
class FeintPolicy:
    """Switches orbit direction based on opponent proximity (response-based)."""
    id: str = "feint"
    switch_distance: float = 0.12
    boost: float = 0.30

    def public_config(self) -> dict:
        return asdict(self)

    def decide(self, obs: Observation) -> Action:
        r = obs.self_pos.norm() / obs.arena_radius
        dist = (obs.opponent_pos - obs.self_pos).norm()
        direction = -1.0 if dist < self.switch_distance else 1.0
        return Action(radial=0.3, tangential=direction * 0.8,
                      torque=0.05, boost=self.boost)


@dataclass
class AdaptivePolicy:
    """Uses prior-round winner info to bias opening aggression."""
    id: str = "adaptive"
    base_boost: float = 0.45

    def public_config(self) -> dict:
        return asdict(self)

    def decide(self, obs: Observation) -> Action:
        r = obs.self_pos.norm() / obs.arena_radius
        # A draw or an unsettled previous round means more uncertainty -> probe.
        unsettled = not bool(obs.prior_round_winners) or \
            obs.prior_round_winners[-1] is None
        boost = self.base_boost + (0.25 if unsettled else -0.10)
        return Action(radial=0.6 if r > 0.5 else 0.2, tangential=0.25,
                      torque=0.05, boost=boost)


@dataclass
class ProberPolicy:
    """Uses early rounds for information; commits later."""
    id: str = "prober"
    info_rounds: int = 2
    probe_boost: float = 0.10
    commit_boost: float = 0.85

    def public_config(self) -> dict:
        return asdict(self)

    def decide(self, obs: Observation) -> Action:
        r = obs.self_pos.norm() / obs.arena_radius
        early = obs.round_no <= self.info_rounds
        if early:
            return Action(radial=0.3, tangential=0.7, torque=0.1,
                          boost=self.probe_boost)
        return Action(radial=0.7, tangential=0.4, torque=0.05,
                      boost=self.commit_boost)


@dataclass
class MixedPolicy:
    """Deterministic pseudo-random policy; outcome is still seed-fixed."""
    id: str = "mixed"
    seed: int = 7

    def public_config(self) -> dict:
        return asdict(self)

    def decide(self, obs: Observation) -> Action:
        import random
        rng = random.Random(self.seed * 31 + obs.tick)
        return Action(
            radial=rng.uniform(-0.4, 1.0),
            tangential=rng.uniform(-1.0, 1.0),
            torque=rng.uniform(-0.3, 0.6),
            boost=rng.uniform(0.0, 0.6),
        )


# ---------------------------------------------------------------------------
# 8 body archetypes (rmdev 1.2)
# ---------------------------------------------------------------------------
def _body(bid: str, **kw) -> BladeSpec:
    base = dict(
        mass=0.055, radius=0.032, inertia_factor=0.50, restitution=0.68,
        contact_friction=0.30, linear_drag=0.035, spin_drag=0.060,
        control_force=0.020, control_torque=0.000020, max_spin=900.0,
        launch_spin=620.0, launch_speed=0.65, energy_capacity=100.0,
        integrity=100.0,
    )
    base.update(kw)
    return BladeSpec(id=bid, **base)


BODY_PRESETS: dict[str, BladeSpec] = {
    "heavy": _body("heavy", mass=0.072, radius=0.036, inertia_factor=0.55,
                   contact_friction=0.34, control_force=0.017, launch_spin=540),
    "light": _body("light", mass=0.042, radius=0.029, inertia_factor=0.46,
                   contact_friction=0.26, control_force=0.025, launch_spin=700),
    "wide": _body("wide", mass=0.060, radius=0.038, contact_friction=0.32,
                  control_force=0.019, launch_spin=580),
    "compact": _body("compact", mass=0.048, radius=0.026, contact_friction=0.28,
                     control_force=0.024, launch_spin=660),
    "high-spin": _body("high-spin", mass=0.058, radius=0.032, spin_drag=0.030,
                       contact_friction=0.30, control_force=0.017, launch_spin=760),
    "grippy": _body("grippy", mass=0.062, radius=0.033, contact_friction=0.48,
                    control_force=0.019, launch_spin=600),
    "slippery": _body("slippery", mass=0.050, radius=0.031, contact_friction=0.12,
                      control_force=0.022, launch_spin=640),
    "balanced": _body("balanced"),
}


def make_body(name: str, suffix: str = "") -> BladeSpec:
    b = BODY_PRESETS[name]
    return BladeSpec(
        id=f"{name}{suffix}",
        mass=b.mass, radius=b.radius, inertia_factor=b.inertia_factor,
        restitution=b.restitution, contact_friction=b.contact_friction,
        linear_drag=b.linear_drag, spin_drag=b.spin_drag,
        control_force=b.control_force, control_torque=b.control_torque,
        max_spin=b.max_spin, launch_spin=b.launch_spin,
        launch_speed=b.launch_speed, energy_capacity=b.energy_capacity,
        integrity=b.integrity,
    )


POLICY_ZOO: list[tuple[str, object]] = [
    ("center", lambda: CenterPolicy()),
    ("rush", lambda: RushPolicy()),
    ("orbit", lambda: OrbitPolicy()),
    ("counter", lambda: CounterPolicyGuide()),
    ("edge-bait", lambda: EdgeBaitPolicy()),
    ("spin-saver", lambda: SpinSaverPolicy()),
    ("late-burst", lambda: LateBurstPolicy()),
    ("pressure", lambda: PressurePolicy()),
    ("feint", lambda: FeintPolicy()),
    ("adaptive", lambda: AdaptivePolicy()),
    ("prober", lambda: ProberPolicy()),
    ("mixed", lambda: MixedPolicy()),
]

BODY_ZOO: list[str] = list(BODY_PRESETS.keys())
