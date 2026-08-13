# Mechanism: STADIUM (Arena Bowl)

## Purpose
Define the arena bowl that constrains blade motion and creates the ring-out mechanic. It is an
intentional 2D open-bowl approximation, not a manufactured Beyblade stadium (PHYSICS_SCOPE).

## Canonical status
GAMEPLAY.

## Inputs
`ArenaSpec` (src/robobladez/model.py), defaults:
```
id="standard-open-bowl-v1", radius=0.42, dt=1/240, max_seconds=25.0,
bowl_strength=0.30, rim_softening_start=0.78, max_bowl_force=0.16,
launch_radius_fraction=0.48, launch_jitter_rad=0.035, min_spin=24.0,
spinout_grace_s=1.0, burst_impulse_threshold=0.055, damage_scale=90.0
```

## State
- **Persistent**: none (arena is a frozen spec).
- **Ephemeral**: the bowl force computed each tick.

## Transition
```
bowl_force(state):
  r = |pos|; frac = r / arena.radius
  soften = 1.0
  if frac > rim_softening_start: soften decays to min 0.08 near the rim
  magnitude = min(max_bowl_force, bowl_strength * r) * soften
  return -unit(pos) * magnitude        # restoring force toward center
```
The bowl gets *less protective* near the open rim, so a fast blade can cross the rim and
ring out.

## Outputs
- Restoring force vector per blade per tick.

## Invariants
1. Force always points toward center (`-unit(pos)`).
2. `|force| <= max_bowl_force`.
3. Restoring force weakens monotonically past `rim_softening_start`.
4. Deterministic given position.

## Information visibility
- The arena radius is **OBSERVABLE_DURING** (`obs.arena_radius`); the force law is public.

## Determinism
- Pure function of position; no RNG.

## Failure modes
- None structural.

## Edge cases
- At exact center (`r=0`) → zero force (guarded `if r < EPS`).
- `frac > 1` (already past rim) → softened force near 0; ring-out logic governs (RINGOUT-SPINOUT).

## Telemetry
- Blade position each frame; ring-out events.

## Versioning
- Arena parameters are part of `ENGINE_VERSION` semantics; a new arena id = new ruleset.

## Security
- None (numeric).

## Tests
- `tests/test_engine.py` determinism; `tests/test_physics.py` passive energy/stability.

## Examples
**Normal**: A blade orbits at 50% radius; bowl force gently restores any outward drift.
**Adversarial**: A blade boosted outward past the rim → softened force can't hold it →
`ring_out` terminal.

## Non-goals
- Does NOT define ring-out terminal (RINGOUT-SPINOUT).
- Does NOT define launch (LAUNCH).
