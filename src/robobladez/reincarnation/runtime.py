"""RBZ-RC-1 interpreter (rm7/rm8).

The BattleExecutable: a validated state machine evaluated continuously against
live telemetry. The Agent is NOT queried per tick; this compiled machine is.
Continuous controls + discrete states + transitions + bounded memory + ability
triggers. Fully deterministic given a seeded RNG.
"""
from __future__ import annotations
import math
from typing import Any

from ..model import Action
from .schema import ReincarnationManifest
from .validate import validate


class ReincarnationRuntime:
    """Interpret a ReincarnationManifest against observations (rm8: interpreter first)."""

    def __init__(self, manifest: ReincarnationManifest):
        validate(manifest)
        self.manifest = manifest
        self.current_state = manifest.initial_state
        self.memory: dict[str, float] = {
            m.name: m.initial for m in manifest.memory
        }
        self._state_map = {s.get("id"): s for s in manifest.states}
        self.tick = 0
        self.ability_ready: dict[str, bool] = {}

    def _obs_ctx(self, obs) -> dict[str, float]:
        """Map an Observation into named numeric context used by conditions.

        Telemetry vocabulary (rmdev2 Phase 1A): closing_speed is TRUE relative
        closing velocity (positive when approaching), plus tangential relative
        speed, radius/energy/integrity fractions, spins, and time.
        """
        dt = getattr(obs, "_dt", 1 / 240)
        if hasattr(obs, "self_pos"):
            delta = obs.opponent_pos - obs.self_pos
            dist = delta.norm()
            closing, rel_tang = 0.0, 0.0
            if dist > 1e-12:
                unit = delta.unit()
                rel_vel = obs.opponent_vel - obs.self_vel
                closing = -rel_vel.dot(unit)            # + = approaching
                rel_tang = abs(rel_vel.dot(unit.perp()))  # tangential relative speed
            self_rad = obs.self_pos.norm()
            opp_rad = obs.opponent_pos.norm()
            arena_r = obs.arena_radius
        else:
            dist, closing, rel_tang = 0.0, 0.0, 0.0
            self_rad = opp_rad = 0.0
            arena_r = 0.42
        self_energy = getattr(obs, "self_energy", 0.0)
        opp_energy = getattr(obs, "opponent_energy", 0.0)
        self_integrity = getattr(obs, "self_integrity", 100.0)
        opp_integrity = getattr(obs, "opponent_integrity", 100.0)
        # Fractions normalized to [0,1]; defaults chosen so unused units are neutral.
        ctx = {
            "distance": dist,
            "closing_speed": closing,
            "relative_tangential_speed": rel_tang,
            "self_radius_fraction": self_rad / arena_r if arena_r else 0.0,
            "opponent_radius_fraction": opp_rad / arena_r if arena_r else 0.0,
            "self_energy_fraction": min(1.0, self_energy / 100.0),
            "opponent_energy_fraction": min(1.0, opp_energy / 100.0),
            "self_integrity_fraction": min(1.0, self_integrity / 100.0),
            "opponent_integrity_fraction": min(1.0, opp_integrity / 100.0),
            "self_spin": getattr(obs, "self_omega", 0.0),
            "opponent_spin": getattr(obs, "opponent_omega", 0.0),
            "time": self.tick * dt,
            "round_time": getattr(obs, "round_no", 1) * 0.0,  # per-round timer set below
            "arena_radius": arena_r,
        }
        # Expose bounded memory slots to condition expressions.
        for name, val in self.memory.items():
            ctx[f"memory.{name}"] = val
        return ctx

    def decide(self, obs) -> Action:
        """Evaluate one tick: apply current state's action, evaluate transitions."""
        self.tick += 1
        ctx = self._obs_ctx(obs)
        state = self._state_map[self.current_state]
        action_spec = state.get("action", {})
        act = Action(
            radial=float(action_spec.get("radial", 0.0)),
            tangential=float(action_spec.get("tangential", 0.0)),
            torque=float(action_spec.get("torque", 0.0)),
            boost=float(action_spec.get("boost", 0.0)),
        ).clamped()

        # Bounded memory ops: SET and ADD (rmart P0.4).
        for mem in action_spec.get("memory", []):
            name, op, val = mem.get("name"), mem.get("op", "add"), mem.get("value", 0)
            if name not in self.memory:
                continue
            if op == "set":
                self.memory[name] = self._clamp_mem(name, float(val))
            elif op == "add":
                self.memory[name] = self._clamp_mem(name, self.memory[name] + float(val))

        # Evaluate transitions in order; first satisfied wins.
        for t in state.get("transitions", []):
            cond = t.get("if")
            if self._eval(cond, ctx):
                self.current_state = t.get("to")
                break
        return act

    def public_config(self) -> dict[str, Any]:
        """Policy-protocol compatibility: expose the manifest as a config."""
        return {
            "format": self.manifest.format,
            "reincarnation_id": self.manifest.reincarnation_id,
            "compute_class": self.manifest.compute_class,
            "initial_state": self.manifest.initial_state,
        }

    def _eval(self, cond, ctx) -> bool:
        if cond is None:
            return False
        op = cond.get("op")
        if op == "lt":
            return ctx.get(cond.get("lhs"), 0) < cond.get("threshold", 0)
        if op == "gt":
            return ctx.get(cond.get("lhs"), 0) > cond.get("threshold", 0)
        if op == "gte":
            return ctx.get(cond.get("lhs"), 0) >= cond.get("threshold", 0)
        if op == "lte":
            return ctx.get(cond.get("lhs"), 0) <= cond.get("threshold", 0)
        if op == "eq":
            return ctx.get(cond.get("lhs"), 0) == cond.get("threshold", 0)
        return False

    def _clamp_mem(self, name: str, val: float) -> float:
        for m in self.manifest.memory:
            if m.name == name:
                return max(-m.max_abs, min(m.max_abs, val))
        return val

    def snapshot(self) -> dict[str, Any]:
        return {
            "state": self.current_state,
            "memory": dict(self.memory),
            "tick": self.tick,
        }
