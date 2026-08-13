# Architecture

## Decision

Build a **modular monolith**, not a dinosaur-specific backend and not a distributed platform.

The stable core primitives are:

```text
Agent
Body
Arena
Policy
Match
Replay
Event
History
BehaviorProfile
StoryBeat
ShotSpec
```

RoboBladez is the first artificial-evolution domain. A prehistoric domain can later reuse
`Match`, `Replay`, `Event`, analytics, story, shots, and media while replacing body/world rules
and adding evidence/provenance.

## Hard boundaries

### Simulation truth

The simulator owns:

- legal actions
- state transitions
- collision/rule resolution
- win conditions
- deterministic RNG
- event ordering

### Competitor intelligence

A policy may:

- read its legal observation
- maintain permitted internal state
- return an allowed action

A policy may not:

- alter the engine
- alter the opponent
- alter the seed
- edit committed code/config after lock
- rewrite canon

### Canon

A canonical match is identified by:

```text
engine_version
match_seed
arena_version
body_versions
policy_commitments
```

For v0 the full configs are embedded in the replay.

### Media

Media is downstream:

```text
Replay → Events → Story → ShotSpec → LTX
```

Media may compress and dramatize but cannot change the winner or event order.

## Why the MVP has its own tiny physics kernel

The hardest architectural problem is not 3D contact fidelity. It is the contract around:

- determinism
- sealed policies
- simultaneous decisions
- replay completeness
- event semantics
- canon persistence
- analysis
- downstream media

The small kernel validates these now. PyBullet can later implement the same `PhysicsBackend`
contract without changing canon or policy semantics.
