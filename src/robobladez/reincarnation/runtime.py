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
        """Map an Observation into named numeric context used by conditions."""
        opp_d = ((obs.opponent_pos - obs.self_pos).norm() if hasattr(obs, "self_pos") else 0)
        self_speed = obs.self_vel.norm() if hasattr(obs, "self_vel") else 0.0
        return {
            "distance": opp_d,
            "closing_speed": max(0.0, self_speed),
            "time": self.tick * getattr(obs, "_dt", 1 / 240),
            "self_energy": getattr(obs, "self_energy", 0.0),
            "self_integrity": getattr(obs, "self_integrity", 100.0),
            "opponent_energy": getattr(obs, "opponent_energy", 0.0),
            "opponent_integrity": getattr(obs, "opponent_integrity", 100.0),
            "arena_radius": getattr(obs, "arena_radius", 0.42),
        }

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

        # Update bounded memory slots from the state spec if declared.
        for mem in action_spec.get("memory", []):
            name, val = mem.get("name"), mem.get("value")
            if name in self.memory:
                self.memory[name] = self._clamp_mem(name, self.memory[name] + val)

        # Evaluate transitions in order; first satisfied wins.
        for t in state.get("transitions", []):
            cond = t.get("if")
            if self._eval(cond, ctx):
                self.current_state = t.get("to")
                break
        return act

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
