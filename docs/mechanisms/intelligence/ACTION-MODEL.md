# Mechanism: ACTION MODEL

## Purpose
Define the exact, bounded set of legal actions a policy may emit, and how they are applied.
A constrained action space is what keeps the game a *competition of strategies* rather than a
free-for-all (Constitution rule 5; rm3 sandbox philosophy).

## Canonical status
GAMEPLAY.

## Inputs
- A `Policy` returning an `Action` from `decide(obs)`.

## State
- **Ephemeral**: the chosen `Action` per blade per tick.

## Transition
```
1. act = policy.decide(obs)
2. act = act.clamped()        # clamp all fields into legal ranges
3. if blade.energy <= 0: act = Action()      # zero control when depleted (but replay keeps chosen)
4. APPLY via integrate_free (physics)
```
`Action` (frozen dataclass), legal ranges:
```
radial:    -1.0 .. +1.0   (+1 inward, -1 outward)
tangential:-1.0 .. +1.0   (orbit direction)
torque:    -1.0 .. +1.0   (spin up/down)
boost:      0.0 ..  1.0   (scales control authority + energy cost)
```

## Outputs
- The (clamped) action is recorded in each `Frame.actions` and applied to physics.

## Invariants
1. Every action is clamped to legal ranges; out-of-range values are never applied raw.
2. Energy = 0 ⇒ no control authority (action effectively zero), but the *chosen* action is
   still recorded in the replay (so analysis sees intent).
3. Only these 4 fields exist; there is no free-form "do anything" action.

## Information visibility
- A policy's action is **PRIVATE** until both are committed (SIMULTANEOUS-DECISION). After
  the tick, both actions are recorded in the frame (OBSERVABLE in replay).

## Determinism
- Clamping is a pure function; actions are floats derived from observations. No RNG.

## Failure modes
- Action with non-finite values → `clamped()` clamps via `max/min`, but a NaN would
  propagate; audit's non-finite check would fail. (Future sandbox rejects non-finite.)

## Edge cases
- All-zero action (passive) — legal.
- `boost` out of [0,1] → clamped to 0 or 1.
- Energy exactly 0 mid-tick → control disabled next tick.

## Telemetry
- Recorded in `Frame.actions`: radial, tangential, torque, boost per blade per frame.

## Versioning
- The 4-field action space is the policy-API contract; adding a field is a
  `rbz-policy-*` version bump.

## Security
- The action schema is the enforcement boundary of the sandbox: an untrusted policy may
  ONLY emit this Action; it cannot touch physics/state (POLICY-RUNTIME).

## Tests
- `tests/test_engine.py` determinism tests (same obs ⇒ same clamped action).
- `tests/test_physics.py` energy/contact tests exercise action application.

## Examples
**Normal**: `RushPolicy` returns `Action(radial=0.9, tangential=0.9, torque=0, boost=1.0)`
→ clamped unchanged, applied with max authority.
**Adversarial**: A policy returns `Action(radial=99, tangential=-99, boost=5)` → clamped to
`Action(1.0, -1.0, 0.0, 1.0)`; it cannot exceed legal authority.

## Non-goals
- Does NOT define how actions map to force/torque (see SPIN-DYNAMICS, BLADE-BODY).
- Does NOT define observation (see OBSERVATION-MODEL).
