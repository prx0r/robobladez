# Mechanism: BLADE BODY

## Purpose
Define the physical body (the "talisman"/node) that a competitor inhabits. It is the fair,
neutral substrate subject to physics. Current `BladeSpec` is a scalar set; a full body grammar
(core/ring/contact/tip/actuator) is a planned extension (rm5 #6).

## Canonical status
GAMEPLAY (body parameters determine mechanics) + INFRA (they are part of match identity).

## Inputs
`BladeSpec` (src/robobladez/model.py), defaults:
```
id, mass=0.055, radius=0.032, inertia_factor=0.50, restitution=0.68,
contact_friction=0.30, linear_drag=0.035, spin_drag=0.060,
control_force=0.020, control_torque=0.000020, max_spin=900.0,
launch_spin=620.0, launch_speed=0.65, energy_capacity=100.0, integrity=100.0
```

## State
- **Persistent**: a body is a frozen spec; a match freezes its body versions.
- **Ephemeral**: `BladeState` during a match (pos, vel, omega, energy, integrity).

## Transition
```
1. validate(): mass>0, radius>0, inertia>0, 0<=restitution<=1, contact_friction>=0
2. inertia = inertia_factor * mass * radius²
3. body is frozen for the match (BODY-EVOLUTION governs between-match change)
```

## Outputs
- Validated `BladeSpec`; derived `inertia`; runtime `BladeState`.

## Invariants
1. `inertia > 0` (validated).
2. Body parameters are immutable within a match.
3. Two bodies with the same spec are mechanically identical.

## Information visibility
- **PUBLIC_BEFORE_MATCH**: body geometry and public stats are known to both competitors
  (mechanical baseline uses them).

## Determinism
- All scalar fields; no RNG.

## Failure modes
- Invalid spec (mass/radius/inertia ≤ 0) → `ValueError` from `validate()`.

## Edge cases
- `inertia_factor=0` → zero inertia → division by zero in physics; `validate()` rejects.

## Telemetry
- The body spec is serialized into `MatchResult.blades`.

## Versioning
- Body versions are tracked (`body_versions`); changing a body creates a new version
  (BODY-EVOLUTION). Never overwrite.

## Security
- The engine validates bodies; untrusted bodies (Phase 4) are just parameter sets, not code.

## Tests
- `tests/test_engine.py::test_invalid_specs_rejected`.

## Examples
**Normal**: `make_body("heavy")` → mass=0.072, radius=0.036, control_force=0.017.
**Adversarial**: A body with `radius=0` → rejected by `validate()`.

## Non-goals
- Does NOT define body *evolution legality* (BODY-EVOLUTION).
- Does NOT define the full body grammar / construction budget (planned; rm5 #6).
