# Peer Review of v1

## Verdict

v1 had the correct **system boundaries** but a simulation kernel too toy-like to justify the
RoboBlade label.

## Major defects

### P0 — Incorrect match winner on tied records

v1 used `max(wins, key=wins.get)` after the round loop. With draws, an odd best-of-N can finish
with equal nonzero wins (for example 1–1 with one draw). Python dictionary order could then award
the first competitor.

**v2 fix:** explicit comparison; equal wins => match draw.

### P0 — "Physics" did not model spinning tops

v1 body state contained position, velocity, energy and integrity but no angular spin or moment of
inertia. Contact was generic disk collision. "Spin Power" was therefore absent from the actual
state transition.

**v2 fix:** angular velocity, moment of inertia, spin drag, tangential contact velocity, frictional
angular impulse, spin-out.

### P1 — Policy commitments fingerprinted config, not implementation

A policy with the same ID/config but changed code could produce the same conceptual commitment.

**v2 fix:** commitment manifest contains class path + public config + SHA-256 of implementation
source where available.

### P1 — No replay-integrity digest

A stored replay could be edited without detection.

**v2 fix:** canonical JSON replay digest; CanonStore refuses invalid digests.

### P1 — Behavior semantics were mixed with narrative semantics

Element affinities looked like analytical truth.

**v2 fix:** raw measured phenotype is canonical analysis. Element/daimon mapping is explicitly
tagged `NARRATIVE_PROJECTION` and cannot affect gameplay.

### P1 — No actual mechanical baseline in demo

The gameplay thesis requires revealing body mechanics before strategic commitment.

**v2 fix:** demo emits `mechanical_baseline.json` from passive bodies before the strategic match.

### P2 — Aggressive policy was not really opponent-directed

The old action basis made "aggression" mostly an arbitrary boost.

**v2 fix:** aggressive policy projects the opponent direction into the arena radial/tangential
control basis and steers toward it.

## What v1 got right

- modular monolith
- canonical replay object
- simultaneous policy decision concept
- media strictly downstream
- no premature RL
- no quantum/consciousness runtime
- SQLite/Postgres as boring persistence
- external-infra adapter philosophy

Those survive.


## v2 self-review discovery: launch symmetry

During v2 stress testing, an early draft launched the second blade with the opposite spin/orbit
sign. That accidentally made both initial translational velocities point in the same global
direction and created a slot bias.

**Fix before release:** both bodies now launch in the same rotational handedness from mirrored
positions. A regression test verifies that swapping Counter/Aggressive policies across otherwise
identical bodies swaps the benefiting identity rather than preserving a "left slot" advantage.

## v2 self-review discovery: audit throughput

The first stress harness retained replay frames for every batch match. That is the wrong execution
mode for league-scale evaluation.

**Fix before release:** `record_frames=False` enables headless batch evaluation while preserving
events/results/digests. Full replays remain enabled for canonical production matches.
