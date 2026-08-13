# Gameplay

## Match lifecycle

```text
BODY REVEAL
↓
MECHANICAL BASELINE
↓
PUBLIC REPORT
↓
PRIVATE OPPONENT ANALYSIS
↓
POLICY MANIFEST
↓
COMMIT HASH
↓
SIMULTANEOUS MATCH
↓
REPLAY REVEAL
↓
POST-MATCH ANALYSIS
↓
NEW AGENT VERSION (optional)
```

## Why deterministic-by-seed matters

A seed controls launch jitter. After the seed is fixed, the transition is deterministic.

The seed is public in the replay, so a match can be rerun exactly.

## Policy action space

v2 gives a RoboBlade limited fictional actuation:

- radial control
- tangential control
- spin torque
- boost

The engine clips and energy-gates these controls.

The interesting problem is not unrestricted code generation. It is:

> Given a public body matchup, history, an observation stream, and a constrained actuator,
> what committed policy best exploits the opponent?

## Multi-round information

Policy *code* is fixed across the match.

`Observation.prior_round_winners` demonstrates the allowed mechanism for match-memory. Future
policies can maintain richer private state, but that state transition must be defined before commit.
