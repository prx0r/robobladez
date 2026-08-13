# Mechanism: LAUNCH

## Purpose
Define the deterministic initial state of each round. Launch includes a tiny seeded jitter so
two slots are not accidentally privileged, while remaining fully reproducible (rm3: "let it rip"
uncertainty from a fixed seed).

## Canonical status
GAMEPLAY (initial conditions are part of the deterministic match).

## Inputs
- `seed: int` for the round.
- `spec: BladeSpec`, `arena: ArenaSpec`.
- `spin_sign` (handedness) and a launch angle.

## State
- **Ephemeral**: the two initial `BladeState`s at round start.

## Transition
```
1. rng = random.Random(seed)                       # round seed
2. jitter = rng.uniform(-launch_jitter_rad, +launch_jitter_rad)
3. A: pos = (cos(j), sin(j)) * launch_radius_fraction * arena.radius
     vel = tangent * launch_speed * (+1)
     omega = launch_spin * (+1)
4. B: pos = (cos(pi - j), sin(pi - j)) * launch_radius_fraction * arena.radius
     vel = tangent * launch_speed * (+1)
     omega = launch_spin * (+1)
```
`launch_radius_fraction=0.48`, `launch_jitter_rad=0.035`, `launch_speed=0.65`,
`launch_spin=620` (defaults). Both spin the same handedness → rotationally symmetric.

## Outputs
- Two `BladeState`s (initial positions, velocities, omega, full energy/integrity).

## Invariants
1. Same seed ⇒ same launch (deterministic).
2. Both blades launch with the SAME spin handedness (no slot advantage).
3. Initial positions are symmetric across the arena center.

## Information visibility
- Launch is internal; both policies observe it via the first Observation.

## Determinism
- `random.Random(round_seed)` where `round_seed = match_seed + n*1000003`. The jitter is the
  ONLY RNG in the round; everything after is deterministic.

## Failure modes
- None; jitter is bounded by `launch_jitter_rad`.

## Edge cases
- `launch_radius_fraction=0` → both start at center (degenerate; not used).
- Same seed reused across two rounds → identical launch (by design of round-seed spacing).

## Telemetry
- Initial state is recorded in the first frame of the round.

## Versioning
- Launch parameters are part of `ArenaSpec`/`BladeSpec` → included in `ENGINE_VERSION` semantics.

## Security
- None (pure numeric init).

## Tests
- `tests/test_engine.py::test_exact_determinism` (same seed ⇒ same full replay incl. launch).

## Examples
**Normal**: seed 5 launches A at angle ~0 and B at ~π with a small jitter; both spin +.
**Adversarial**: Reusing the match seed for round 2 without the `+n*1000003` offset would
launch identically every round — the offset prevents degenerate repeat launches.

## Non-goals
- Does NOT define spin evolution (SPIN-DYNAMICS).
- Does NOT define terminal conditions (RINGOUT-SPINOUT).
