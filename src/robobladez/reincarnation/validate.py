"""RBZ-RC-1 validation (rm8).

Rejects malformed, illegal, or unbounded reincarnations before they are hashed
or executed. This is the bounded-language enforcement point (rm7: freedom within
lawful embodiment — no arbitrary Python).
"""
from __future__ import annotations
from typing import Any

from .schema import COMPUTE_CLASSES, CONTROLS, ReincarnationManifest


class ValidationError(ValueError):
    pass


def validate(manifest: ReincarnationManifest) -> None:
    """Raise ValidationError if the manifest is not a legal RBZ-RC-1 machine."""
    if manifest.format != "RBZ-RC-1":
        raise ValidationError("format must be RBZ-RC-1")
    if not manifest.initial_state:
        raise ValidationError("initial_state required")
    if manifest.compute_class not in COMPUTE_CLASSES:
        raise ValidationError(f"unknown compute_class {manifest.compute_class}")
    budget = COMPUTE_CLASSES[manifest.compute_class]

    state_ids = [s.get("id") for s in manifest.states]
    if len(set(state_ids)) != len(state_ids):
        raise ValidationError("duplicate state ids")
    if not state_ids:
        raise ValidationError("at least one state required")
    if manifest.initial_state not in state_ids:
        raise ValidationError("initial_state not present in states")
    if len(manifest.states) > budget["max_states"]:
        raise ValidationError(f"too many states for {manifest.compute_class}")

    n_transitions = 0
    for s in manifest.states:
        action = s.get("action", {})
        for k in action:
            if k not in CONTROLS:
                raise ValidationError(f"illegal control {k!r}")
            v = action[k]
            if not _finite(v):
                raise ValidationError(f"non-finite action value for {k}")
        transitions = s.get("transitions", [])
        n_transitions += len(transitions)
        for t in transitions:
            if t.get("to", "") not in state_ids:
                raise ValidationError(f"transition target {t.get('to')!r} unknown")
            cond = t.get("if")
            if cond is not None and not _finite(cond.get("threshold", 0)):
                raise ValidationError("non-finite transition threshold")
    if n_transitions > budget["max_transitions"]:
        raise ValidationError(f"too many transitions for {manifest.compute_class}")

    # Memory bound.
    total_mem = sum(_mem_bytes(m) for m in manifest.memory)
    if total_mem > budget["max_memory_bytes"]:
        raise ValidationError(f"memory exceeds {manifest.compute_class} budget")

    # Non-finite constants everywhere.
    _assert_all_finite(manifest)


def _mem_bytes(m) -> int:
    return {"u8": 1, "i16": 2, "f32": 4}.get(m.type, 8)


def _finite(v) -> bool:
    import math
    return isinstance(v, (int, float)) and math.isfinite(float(v))


def _assert_all_finite(manifest) -> None:
    import math
    def check(obj):
        if isinstance(obj, dict):
            for v in obj.values():
                check(v)
        elif isinstance(obj, (list, tuple)):
            for v in obj:
                check(v)
        elif isinstance(obj, (int, float)):
            if not math.isfinite(float(obj)):
                raise ValidationError("non-finite constant")
    check(manifest.executable_payload())
