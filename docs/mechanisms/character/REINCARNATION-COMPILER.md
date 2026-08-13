# Mechanism: REINCARNATION COMPILER

## Purpose
Define the core AI mechanic that differentiates RoboBladez from an ordinary bot tournament:
before each match, the persistent Agent **rewrites itself into a new executable incarnation** —
a sealed, compiled controller it authored specifically for the opponent — and THAT incarnation
enters the arena. "Battle Avatar" is the presentation term; **Reincarnation** is the actual
executable mechanism.

> Before each match, every AI rewrites itself into a sealed executable incarnation designed
> specifically for its opponent. The incarnations fight. Afterwards their code is revealed,
> studied, and used by the persistent AIs to design their next selves.

## Canonical status
GAMEPLAY (the compiled controller is what executes) + INFRA (the compilation/validation
pipeline is the correctness layer).

## Inputs
- Persistent `AgentState` (identity, memory, beliefs, opponent models, policy lineage, daimon).
- `opponent_version`, mechanical baseline, arena, historical matches, current rules.
- The Agent's own reasoning (LLM deliberation) that produces a Reincarnation AST.

## State
- **Persistent**: `ReincarnationLineage` — every reincarnation R001..R027 stored, hash-verified.
- **Ephemeral**: the compiled, locked `BattleExecutable` during the match.

## The three/four Boris objects
These MUST remain distinct (never collapsed):
```text
BORIS                 persistent strategic intelligence (survives seasons)
BORIS REINCARNATION   match-specific self-authored machine (compiled + sealed)
BORIS BODY            physical talisman (TALISMAN)
PENELOPE              Daimon intelligence (after MANIFEST)
```
`Agent != Reincarnation != Body != Daimon`.

## Transition (the reincarnation loop)
```
persistent Boris
    ↓ studies (opponent, baseline, arena, history, own weaknesses, meta)
    ↓ reasons ("I need to become the version of myself that beats Morty here")
    ↓ REINCARNATION — AI writes/synthesizes:
         Reincarnation (state machine + policy graph + thresholds + internal memory +
                        predictions + contingencies + ability triggers + adaptation rules +
                        fallback modes)
    ↓ compile + validate + lock
    ↓ BORIS_REINCARNATION_027
    ↓ THIS enters the arena
    ↓ deterministic battle → replay/result
    ↓ persistent Boris observes what his reincarnated self did
    ↓ learns → next reincarnation
```

## The LLM does not fight directly
```
LLM reasoning phase ──► self-authored controller ──► validator/compiler ──► locked
deterministic machine ──► battle
```
The AI is creative BEFORE the battle but cannot hallucinate physics or cheat during it.

## Outputs
- `ReincarnationManifest` (`RBZ-RC-1` versioned standard):
```
identity, parent_reincarnation, target_match, opponent_model_hash,
strategy_thesis, state_variables, states, transitions, actions,
ability_triggers, round_memory, resource_policy, fallback_behavior,
safety_limits, compiler_version, sdk_version, commitment_hash
```

## Reincarnation content (the executable mind)
Not merely a policy config — a continuous reactive controller:
```text
continuous policy (radial/tangential/torque/boost)
+ discrete state machine
+ event system
+ timers
+ internal memory
+ ability graph (triggers, targeting, duration, cost, cooldown, cancellation, cleanup)
+ fallback rules
```

## Compilation pipeline (rigorous — one of the strictest specs)
```
Agent reasoning
    ↓
Reincarnation AST
    ↓
validator:
    valid states? finite transitions? legal observations? legal actions?
    legal abilities? memory bounds? termination? deterministic RNG? instruction budget?
    ↓
canonical normalization
    ↓
hash
    ↓
compile
    ↓
BattleExecutable
```

## Bounded language (no arbitrary generated Python)
The AI authors within a bounded DSL so it cannot `import os` / `edit_simulator()`:
```text
4 continuous controls (radial, tangential, torque, boost)
5–8 observable variables
16–32 states max (MVP)
bounded memory
simple boolean/numeric conditions
3 ability archetypes: instant impulse | temporary parameter modifier | temporary field/zone
```
MVP simplicity is a restriction of the language, not a simplification of the concept.

## Computational budget (regulated resource)
Every incarnation gets a compute class:
```text
C1: 32 states, 256 transitions, 4 KB memory
C2: 128 states, 1024 transitions, 32 KB memory
...
```
Larger models cannot create absurdly huge machines; compute complexity becomes a regulated,
even league-relevant, resource.

## Information visibility
```text
AGENT         sees full reincarnation
DAIMON        sees full reincarnation
HUMAN OWNER   sees strategic summary only
OPPONENT      sees only commitment hash
AUDIENCE      sees strategy summary (optional)
AFTER MATCH   full reincarnation revealed (studied by opponents)
```

## Invariants
1. The reincarnation is sealed (commit hash) before the match; code cannot change mid-match.
2. Reincarnation is bound to (agent_version, opponent_version, seed).
3. Memory may evolve between rounds only through committed code (ROUND-MEMORY).
4. The reincarnation can only emit legal actions/abilities (bounded DSL).
5. Lineage is append-only and hash-verified (R001..R027 never overwritten).
6. The persistent Agent is never queried by an LLM per physics tick.

## Determinism
- The compiled controller is deterministic; any RNG uses the seeded `policy_rng`.
- The AST → validator → hash → compile pipeline is fully deterministic.

## Failure modes
| Failure | Detection | Response |
|---|---|---|
| Invalid AST (bad state/transition) | validator | reject, no compilation |
| Non-finite / non-deterministic RNG | validator + replay digest | reject |
| Instruction budget exceeded | validator | reject or down-class |
| Memory overflow | runtime bound | clamp/reject |
| Illegal action/ability | validator | reject |
| Policy timeout | sandbox (Phase 4) | idle action / forfeit |

## Edge cases
- First reincarnation (no parent) → genesis defaults.
- Daimon co-authoring after MANIFEST → composed `[Agent core + Daimon module]`.
- Opponent studied a revealed incarnation → recursive counter-incarnation (meta).

## Telemetry
- `reincarnation_id`, `commitment_hash`, parent lineage, compiled state/transition counts,
  compute class.

## Versioning
- `RBZ-RC-1` reincarnation format; `compiler_version` and `sdk_version` in the manifest.
- Lineage is append-only: `R001..R027` are historical sports artifacts (e.g. "R011 first
  introduced the center trap; R027 first used a recursive opponent model").

## Security
- The bounded DSL is the sandbox boundary: no arbitrary Python, no engine mutation.
- Compilation is the enforcement point separating LLM deliberation from physics.

## Tests
Required:
1. Two AIs can generate materially different reincarnations.
2. Reincarnations react intelligently during live combat.
3. One AI can study a revealed prior incarnation and generate a counter-incarnation.
4. Multi-round memory creates adaptation without rewriting the controller mid-match.

## Examples
**Normal**: Boris writes R027 with `OBSERVE → BAIT → SLIP_COUNTER → RECOVER → CENTER_CONTROL`
and seals it; Morty sees the hash; battle runs deterministically.
**Adversarial**: An Agent tries to author `import os` or unbounded memory — rejected by the
validator/bounded DSL.

## Non-goals
- Does NOT run the LLM per tick (that is the forbidden "GPT says turn left" path).
- Does NOT define ability mechanics themselves (ABILITY-SYSTEM).
- Does NOT define reincarnation as mere identity persistence (see REINCARNATION.md for the
  storage layer).
