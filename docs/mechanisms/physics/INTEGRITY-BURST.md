# Mechanism: INTEGRITY / BURST

## Purpose
Define the second resource bar (integrity/structural health) and the "burst" terminal: a blade
breaks when its structure is destroyed by a sufficiently violent impact. This is the high-impact
KO mechanic.

## Canonical status
GAMEPLAY.

## Inputs
- `BladeState.integrity`, impact impulse from CONTACT-COLLISION, `ArenaSpec`
  (`burst_impulse_threshold`, `damage_scale`).

## State
- **Ephemeral**: `integrity` on the blade state.

## Transition
```
For a collision with total impulse `impulse`:
  excess = max(0, impulse - burst_impulse_threshold)
  if excess:
    damage = excess * damage_scale
    a.integrity = max(0, a.integrity - damage)
    b.integrity = max(0, b.integrity - damage)      # BOTH blades take burst damage
  terminal: if integrity <= 0 -> "burst"
```
`burst_impulse_threshold=0.055`, `damage_scale=90` (defaults).

## Outputs
- Reduced integrity; possible `burst` round terminal.

## Invariants
1. `integrity >= 0` (clamped).
2. Burst damage is symmetric (both blades damaged by the same impact).
3. Below the threshold, impacts cause NO structural damage (only momentum exchange).
4. `integrity <= 0` ends the round for that blade (burst).

## Information visibility
- **OBSERVABLE_DURING**: self and opponent integrity visible.

## Determinism
- Pure function of impulse.

## Failure modes
- None structural.

## Edge cases
- Impulse exactly at threshold → `excess=0`, no damage.
- Both blades burst in the same tick → `double_burst` round end (winner None).

## Telemetry
- `integrity` per frame; `burst` round reasons.

## Versioning
- Threshold/damage are `ENGINE_VERSION`-relevant.

## Security
- None (numeric).

## Tests
- `tests/test_engine.py` determinism; `tests/test_physics.py` collision energy.

## Examples
**Normal**: A hard head-on impact exceeds threshold → both blades lose integrity; if one hits 0
it bursts.
**Adversarial**: An extremely violent impact bursts both simultaneously → `double_burst`,
round draw.

## Non-goals
- Does NOT define energy (ENERGY).
- Does NOT define ring-out/spin-out (RINGOUT-SPINOUT).
