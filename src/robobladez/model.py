from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any
import math

@dataclass(frozen=True)
class Vec2:
    x: float
    y: float

    def __add__(self, o: "Vec2") -> "Vec2": return Vec2(self.x + o.x, self.y + o.y)
    def __sub__(self, o: "Vec2") -> "Vec2": return Vec2(self.x - o.x, self.y - o.y)
    def __mul__(self, k: float) -> "Vec2": return Vec2(self.x * k, self.y * k)
    def __truediv__(self, k: float) -> "Vec2": return Vec2(self.x / k, self.y / k)
    def dot(self, o: "Vec2") -> float: return self.x*o.x + self.y*o.y
    def cross(self, o: "Vec2") -> float: return self.x*o.y - self.y*o.x
    def norm2(self) -> float: return self.dot(self)
    def norm(self) -> float: return math.sqrt(self.norm2())
    def unit(self) -> "Vec2":
        n = self.norm()
        return Vec2(0.0, 0.0) if n == 0 else self/n
    def perp(self) -> "Vec2": return Vec2(-self.y, self.x)
    def finite(self) -> bool: return math.isfinite(self.x) and math.isfinite(self.y)

@dataclass(frozen=True)
class BladeSpec:
    id: str
    mass: float = 0.055                # kg-like game units
    radius: float = 0.032              # metres-like
    inertia_factor: float = 0.50       # solid disk I = factor*m*r^2
    restitution: float = 0.68
    contact_friction: float = 0.30
    linear_drag: float = 0.035
    spin_drag: float = 0.060
    control_force: float = 0.020        # fictional RoboBlade actuator
    control_torque: float = 0.000020
    max_spin: float = 900.0             # rad/s
    launch_spin: float = 620.0
    launch_speed: float = 0.65
    energy_capacity: float = 100.0
    integrity: float = 100.0

    @property
    def inertia(self) -> float:
        return self.inertia_factor * self.mass * self.radius * self.radius

    def validate(self) -> None:
        if self.mass <= 0 or self.radius <= 0 or self.inertia <= 0:
            raise ValueError("mass/radius/inertia must be positive")
        if not (0 <= self.restitution <= 1):
            raise ValueError("restitution must be in [0,1]")
        if self.contact_friction < 0:
            raise ValueError("contact_friction must be nonnegative")

@dataclass(frozen=True)
class ArenaSpec:
    id: str = "standard-open-bowl-v1"
    radius: float = 0.42
    dt: float = 1/240
    max_seconds: float = 25.0
    bowl_strength: float = 0.30         # F ≈ -k*r (planar bowl approximation)
    rim_softening_start: float = 0.78   # fraction of arena radius
    max_bowl_force: float = 0.16
    launch_radius_fraction: float = 0.48
    launch_jitter_rad: float = 0.035
    min_spin: float = 24.0
    spinout_grace_s: float = 1.0
    burst_impulse_threshold: float = 0.055
    damage_scale: float = 90.0

    def validate(self) -> None:
        if self.radius <= 0 or self.dt <= 0 or self.max_seconds <= 0:
            raise ValueError("invalid arena dimensions/time")

@dataclass(frozen=True)
class Action:
    radial: float = 0.0       # +1 inward, -1 outward
    tangential: float = 0.0   # +/- around arena
    torque: float = 0.0       # +/- change own spin
    boost: float = 0.0        # 0..1 scales control authority/cost

    def clamped(self) -> "Action":
        c = lambda v: max(-1.0, min(1.0, float(v)))
        return Action(c(self.radial), c(self.tangential), c(self.torque),
                      max(0.0, min(1.0, float(self.boost))))

@dataclass
class BladeState:
    id: str
    pos: Vec2
    vel: Vec2
    omega: float
    energy: float
    integrity: float
    center_time: float = 0.0

    def finite(self) -> bool:
        return (self.pos.finite() and self.vel.finite()
                and all(math.isfinite(x) for x in (self.omega,self.energy,self.integrity)))

@dataclass(frozen=True)
class Observation:
    tick: int
    round_no: int
    self_pos: Vec2
    self_vel: Vec2
    self_omega: float
    self_energy: float
    self_integrity: float
    opponent_pos: Vec2
    opponent_vel: Vec2
    opponent_omega: float
    opponent_energy: float
    opponent_integrity: float
    arena_radius: float
    prior_round_winners: tuple[str|None, ...] = ()

@dataclass
class Event:
    tick: int
    t: float
    type: str
    actor: str | None = None
    target: str | None = None
    importance: float = 0.0
    data: dict[str, Any] = field(default_factory=dict)

@dataclass
class Frame:
    tick: int
    t: float
    states: dict[str, dict[str, Any]]
    actions: dict[str, dict[str, float]]

@dataclass
class RoundResult:
    round_no: int
    seed: int
    winner: str | None
    reason: str
    frames: list[Frame]
    events: list[Event]

@dataclass
class MatchResult:
    match_id: str
    engine_version: str
    seed: int
    arena: dict[str, Any]
    blades: dict[str, dict[str, Any]]
    policy_manifests: dict[str, dict[str, Any]]
    policy_commitments: dict[str, str]
    rounds: list[RoundResult]
    wins: dict[str, int]
    winner: str | None
    replay_digest: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
