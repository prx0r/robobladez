# Architecture

## Decision

A **modular monolith**: a deterministic competition + canon + content compiler. The stable core
primitives are:

```text
Agent (persistent identity)
Daimon (emergent companion projection)
Body / Talisman (physical substrate)
Reincarnation (RBZ-RC-1 compiled match-self)
Arena
Match
Replay
Event
Canon
BehaviorProfile
StoryBeat
ShotSpec
RenderRequest / RenderArtifact
```

RoboBladez is the first domain. The reusable core is the competition/canon/media loop; a
prehistoric or other domain later replaces body/world rules and adds evidence/provenance while
reusing `Match`, `Replay`, `Event`, analytics, story, shots, media.

## The five actors (rm6) — never collapsed

```text
HUMAN        owner / founder / mentor / coach (no joystick, no mid-battle input)
AGENT        persistent AI competitor (survives seasons)
DAIMON       emergent persistent AI companion (from measured behavior, non-causal)
BODY         physical talisman (can change; Agent remains Agent)
REINCARNATION  the compiled, sealed battle-self that actually fights
```

`Agent != Reincarnation != Body != Daimon`.

## Reincarnation is the runtime

The Agent does NOT get queried per tick. Before a match it authors a RBZ-RC-1
Reincarnation (bounded state machine: states + transitions + continuous controls + memory),
which is validated, normalized, committed (canonical-bytes hash), and executed by an
interpreter.

```text
AgentVersion + OpponentModel + MechanicalReport + Ruleset + Arena
        ↓
ReincarnationAuthor
        ↓
ReincarnationAST (RBZ-RC-1)
        ↓
validate → normalize → commit canonical manifest
        ↓
compile/interpreter (ReincarnationRuntime)
        ↓
engine (deterministic)
```

## Hard boundaries

### Simulation truth
The simulator owns: legal actions, state transitions, collision/rule resolution, win
conditions, deterministic RNG, event ordering. `physics.py` is a tiny rigid-disk kernel;
a future PyBullet backend can implement the same physics contract without changing canon.

### Competitor intelligence
A policy/reincarnation may: read its legal observation, maintain permitted internal state
(ROUND-MEMORY), return an allowed action. It may NOT: alter the engine, alter the opponent,
alter the seed, edit committed code/config after lock, rewrite canon, or access wall
clock / filesystem / network (sandbox Phase 4).

### Emergence is evidence-bearing
Nothing is called "emergent" unless measured from interaction (Constitution rule 10):
- **Daimon** stages advance only on typed evidence (salience events, confirmed signatures,
  phenotype stability) — never `bool(winner)`.
- **Signatures** are confirmed only with cross-match, cross-opponent statistical support.

### Post-match evolution is transactional
Both agents are snapshotted pre-match; reflections + evidence derive from the same epoch;
deltas are applied atomically. Order-independent and replayable.

### Canon
A canonical match is identified by:
```text
engine_version
match_seed
arena_version
body_versions
reincarnation commitments (canonical AST hash)
```
The canonical AST bytes are the committed + revealed object (not Python source).

### Seed protocol
Strategies commit against a `MatchChallenge` BEFORE the exact simulation seed is revealed.
The match seed is derived from `H(server_nonce || commitA || commitB || challenge_id)`, so
agents can't pre-solve the exact launch and the organizer can't change the seed after seeing
policies.

### Media
Media is downstream and renderer-agnostic:
```text
Replay → Events → Story → ShotSpec → RenderRequest → [LTX] → RenderArtifact → QA → Episode
```
Media may compress and dramatize but cannot change the winner or event order (Constitution 7).
LTX is a replaceable backend (2.3 today, 2.5 later). QA is deterministic against the replay.

## Module map

| Module | Role |
|---|---|
| `engine.py`, `physics.py`, `model.py` | deterministic match kernel |
| `policy.py`, `reincarnation/` | policies + RBZ-RC-1 compiler/interpreter |
| `reincarnation_author.py` | Agent authors a Reincarnation from match context |
| `battle.py` | two-phase battle protocol (mechanical reveal → sealed → best-of-N) |
| `mechanical.py` | mechanical baseline report |
| `salience.py`, `signatures.py` | evidence-bearing emergence |
| `agent.py`, `evolution.py` | persistent identity, daimon, opponent models, reflection |
| `league.py`, `challenge.py` | season, round-robin, seed commit/reveal |
| `canon.py`, `replay.py` | canonical persistence |
| `analysis.py`, `story.py` | behavior phenotype → story beats |
| `shots.py`, `media.py` | ShotSpecs + renderer-agnostic media pipeline |
| `simulate.py` | full end-to-end CPU simulation (no LTX) |
| `meta.py`, `scripts/run_matrix.py` | matchup matrix + non-transitivity diagnosis |

## Why the tiny physics kernel first

The hardest problem is not 3D contact fidelity — it is the contract around determinism,
sealed reincarnations, simultaneous decisions, replay completeness, event semantics, canon
persistence, evidence-bearing emergence, and downstream media. The small kernel validates all
of that now.
