# Mechanism: SPIN DYNAMICS

## Purpose
Define how a blade's angular spin evolves under control torque, spin drag, and contact.
Spin is a first-class resource: it powers contact, decays passively, and its loss triggers
spin-out (rm5, PHYSICS_SCOPE).

## Canonical status
GAMEPLAY.

## Inputs
- `BladeState.omega`, `BladeSpec` (inertia, spin_drag, max_spin, control_torque),
- `Action.torque`, `arena.dt`.

## State
- **Ephemeral**: `omega` on the blade state.

## Transition
```
omega += (control_torque * torque / inertia) * dt
omega = clamp(omega, -max_spin, +max_spin)
omega *= exp(-spin_drag * dt)          # exponential (stable) spin drag
```
Contact can also change omega via tangential impulse (CONTACT-COLLISION).

## Outputs
- Updated `omega`; `spin_drag` decay is energy-lossy.

## Invariants
1. `|omega| <= max_spin` (clamped each step).
2. Passive spin decays monotonically toward 0 (no spontaneous spin-up).
3. Spin magnitude is the input to the spin-out terminal (RINGOUT-SPINOUT).

## Information visibility
- **OBSERVABLE_DURING**: both blades' `omega` is visible to each policy.

## Determinism
- Pure arithmetic; exponential drag is timestep-stable and deterministic.

## Failure modes
- None structural; `inertia=0` would divide by zero (rejected at BLADE-BODY validate).

## Edge cases
- `omega` exactly 0 → `min_spin` threshold logic treats as spin-out after grace.
- `torque` at max vs spin already at `max_spin` → clamped, no further spin-up.

## Telemetry
- `omega` per blade per frame (in replay).

## Versioning
- `spin_drag`, `max_spin`, `control_torque` are part of `ENGINE_VERSION` semantics.

## Security
- None (numeric).

## Tests
- `tests/test_physics.py::test_spin_decays_passively`.

## Examples
**Normal**: `SpinnerPolicy` sets torque=1.0 until `omega` reaches target, then reduces.
**Adversarial**: A policy emits torque beyond range → clamped by ACTION-MODEL before physics.

## Non-goals
- Does NOT define contact spin exchange (CONTACT-COLLISION).
- Does NOT define energy (ENERGY).
