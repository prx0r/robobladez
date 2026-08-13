# Mechanism: ENERGY

## Purpose
Define the finite energy budget that powers control authority. Energy is spent by boosting and
torque; once depleted, the blade loses control (but can still coast on inertia/spin). It is one
of two "resource" bars (with INTEGRITY).

## Canonical status
GAMEPLAY.

## Inputs
- `BladeState.energy`, `Action` (boost, radial, tangential, torque), `arena.dt`.

## State
- **Ephemeral**: `energy` on the blade state (persists across the match, not reset per round
  by default — reset to `energy_capacity` at launch).

## Transition
```
control_load = (|radial| + |tangential|) * 0.5
cost_rate = (0.38 * boost * control_load) + (0.16 * |torque|)
energy = max(0.0, energy - cost_rate * dt)
if energy <= 0: no control authority (action effectively zero; see ACTION-MODEL)
```
Energy is set to `energy_capacity` (default 100.0) at launch.

## Outputs
- Updated `energy`; gating of control authority.

## Invariants
1. `energy >= 0` (clamped).
2. Passive play (boost=0, torque=0) costs no energy.
3. Energy=0 ⇒ zero control authority (but chosen actions still recorded in replay).

## Information visibility
- **OBSERVABLE_DURING**: self and opponent `energy` are visible (`obs.self_energy`,
  `obs.opponent_energy`).

## Determinism
- Pure arithmetic.

## Failure modes
- None structural.

## Edge cases
- `boost=1` with heavy radial+tangential → fastest drain.
- Energy 0 mid-tick → control disabled next tick (grace via already-applied tiny control).

## Telemetry
- `energy` per blade per frame.

## Versioning
- Cost formula is `ENGINE_VERSION`-relevant.

## Security
- None (numeric).

## Tests
- `tests/test_physics.py` passive energy non-increase (energy conservation for passive play).

## Examples
**Normal**: `RushPolicy` (boost=1.0) drains energy quickly; `SpinSaverPolicy` preserves it.
**Adversarial**: A policy relies on control after energy=0 — blocked: engine gates control.

## Non-goals
- Does NOT define ability costs (ABILITY-SYSTEM).
- Does NOT define integrity/burst (INTEGRITY-BURST).
