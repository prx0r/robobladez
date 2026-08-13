# Mechanism: CONTACT / COLLISION

## Purpose
Define rigid-disk contact: how two blades exchange linear and angular momentum when they
touch. This is real rigid-body impulse mechanics (normal + Coulomb-limited tangential),
including spin coupling — the source of burst damage and much of the game's physical depth.

## Canonical status
GAMEPLAY.

## Inputs
- Two `BladeState`s and `BladeSpec`s; `ArenaSpec` (burst threshold, damage scale); tick.

## State
- **Ephemeral**: velocities and omegas of both blades after resolution.

## Transition
```
1. if distance >= sum(radii) or distance==0: no collision
2. n = delta/dist; t = n.perp()
3. positional correction for penetration
4. contact velocities include spin: va_c = va + t*(wa*ra); vb_c = vb - t*(wb*rb)
5. rv = vb_c - va_c; vn = rv·n
   if vn >= 0 (separating): no impulse
6. jn = -(1+e)*vn / (inv_ma+inv_mb)                  # normal impulse, e=min(restitution)
7. vt = rv·t; jt = clamp(-vt / denom_t, -mu*jn, +mu*jn)   # Coulomb limit, mu=sqrt(fa*fb)
8. apply J = n*jn + t*jt to both; update omega via angular impulse
9. impulse = |J|; excess = max(0, impulse - burst_impulse_threshold)
   if excess: integrity -= excess * damage_scale (BOTH blades)   # burst (INTEGRITY-BURST)
```
`burst_impulse_threshold=0.055`, `damage_scale=90` (ArenaSpec defaults).

## Outputs
- Updated velocities/omegas; a `collision` `Event` with impulses + importance.

## Invariants
1. Contact velocity includes spin (spin can be exchanged).
2. No impulse if the pair is separating (`vn>=0`).
3. Tangential impulse is Coulomb-limited by `mu*|jn|` (no infinite friction).
4. Deterministic given pre-contact state.

## Information visibility
- Impact is observable via the collision event (analytics); not exposed to policies as an
  out-of-band signal (they infer from velocity/omega changes).

## Determinism
- Pure impulse math; no RNG.

## Failure modes
- Overlapping states → positional correction prevents tunneling/overlap drift.
- Non-finite after resolution → `FloatingPointError` (audit).

## Edge cases
- Perfectly head-on (vn maximal) → max normal impulse.
- Grazing (vn≈0) → small/normal impulse, mostly tangential.
- `restitution=0` (perfectly inelastic) → `e=0`, no bounce.

## Telemetry
- `normal_impulse`, `tangent_impulse`, `total_impulse`, `importance` per collision event.

## Versioning
- Collision parameters (restitution, friction, burst threshold) are `ENGINE_VERSION`-relevant.

## Security
- None (numeric).

## Tests
- `tests/test_physics.py` (energy non-increase, spin decay) and `tests/test_engine.py`
  determinism across many seeds.

## Examples
**Normal**: Two blades collide with moderate closing speed; impulses resolve, some integrity
loss if above burst threshold.
**Adversarial**: A very high-speed impact → `excess` large → burst damage → possible `burst`
terminal (INTEGRITY-BURST).

## Non-goals
- Does NOT define terminal conditions (RINGOUT-SPINOUT, INTEGRITY-BURST).
- Does NOT define control forces (SPIN-DYNAMICS / BLADE-BODY actuation).
