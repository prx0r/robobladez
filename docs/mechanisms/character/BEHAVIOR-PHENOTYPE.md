# Mechanism: BEHAVIOR PHENOTYPE

## Purpose
Reduce a match's raw telemetry into a compact, interpretable profile of *how* an agent played —
the evidence base from which daimons and signatures are projected. This is core idea #3
(behavior creates identity) and the bridge between GAMEPLAY and NARRATIVE.

## Canonical status
ANALYTICS. The phenotype is derived truth; the elemental projection is NARRATIVE.

## Inputs
- `MatchResult` (frames: positions/velocities/omega/energy; actions: radial/tangential/torque/
  boost; events: collision/round_end).

## State
- **Ephemeral**: computed per analysis call. Persistent only via `DaimonState` EMA.

## Transition
```
FOR each round, FOR each frame:
    accumulate per blade: speed, |spin|, center_fraction, boost, radial_in/out,
                          orbit, torque, collisions, impulse
normalize by sample count
phenotype = { avg_speed, avg_abs_spin, center_fraction, avg_boost, inward_control,
              outward_control, orbit_control, torque_control,
              collisions_per_round, impulse_per_round, round_win_fraction }
```
`analyze_behavior` (src/robobladez/analysis.py) returns per blade `{phenotype, daimon_projection}`.

## Outputs
- `phenotype: dict` — raw measured metrics.
- `daimon_projection: dict` — `{status:"NARRATIVE_PROJECTION", affinities, dominant, note}`.

## Invariants
1. Phenotype is a pure function of the match replay (deterministic).
2. Elemental affinities sum to 1.0.
3. `daimon_projection.status == "NARRATIVE_PROJECTION"` — explicitly non-causal.
4. The phenotype can never change the match outcome (it is computed after the match).

## Information visibility
- **POST_MATCH**: phenotype + projection are analyzable/revealable.

## Determinism
- Pure aggregation; no RNG.

## Failure modes
- Empty frames (record_frames=False) → `max(1,count)` guards division; metrics may be 0.
- A blade absent from a frame → skipped (guarded).

## Edge cases
- No collisions → `collisions_per_round=0`.
- Constant zero action → boost=0, orbit=0, center=1.

## Telemetry
- All phenotype metrics + `daimon_projection.affinities`.

## Versioning
- The projection formula is a ruleset choice; changing it changes projections but not canon
  (projections are versioned as NARRATIVE).

## Security
- Analytics-only; never injected into the engine.

## Tests
- `tests/test_engine.py::test_analysis_separates_projection` (affinities normalize; separated).

## Examples
**Normal**: An aggressive blade → high `avg_boost`, high `collisions_per_round`, low
`center_fraction`; projection dominant Fire.
**Adversarial**: Attempting to make the projection affect the winner — structurally impossible
(computed post-match, non-causal).

## Non-goals
- Does NOT establish identity over time (DAIMON-EMERGENCE).
- Does NOT detect signatures (SIGNATURE-MOVES).
