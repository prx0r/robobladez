# Gameplay Origin

Distilled from the highest-signal source material (`complete gameplay and project mechanics prompt.txt`,
`robobladez thesis.txt`, `overview_robobladez.txt`, `actually good blades.txt`). These are the *reasons* the
v2+ protocol exists. They are design law, not implementation detail.

## The five actors (rm6)

Human, Agent, Daimon, Talisman (Body), and Battle Avatar are DIFFERENT objects and must never
be collapsed into one:

```text
HUMAN            owner / founder / mentor / coach (not joystick operator)
AGENT            persistent AI competitor (survives season to season)
DAIMON           emergent persistent AI companion (arises from lived history)
TALISMAN (Body)  physical substrate (can change; Agent remains Agent)
BATTLE AVATAR    match-specific compiled strategy policy (sealed)
```

Key rules:
- **Human** creates the genesis, then mentors/proposes/negotiates — but cannot secretly
  overwrite the competitor. No joystick, no buttons, no mid-battle prompts.
- **Agent** is Boris, not `CounterPolicy()`. Its state: identity, genesis, memory, career,
  beliefs, opponent models, relationships, goals, body history, policy lineage, daimon
  relationship.
- **Daimon** is a literal persistent companion that does NOT exist fully at genesis: it
  coheres from measured behavior and, upon MANIFEST, becomes a second distinct perspective
  (advisor/mirror/counterweight) that may disagree with the Agent. It is a two-layer object:
  grounded ANALYTICS state + downstream NARRATIVE intelligence.
- **Battle Avatar** is the compiled strategic intention (policy + utility weights +
  contingencies + adaptation rules). The persistent Agent is NOT queried by an LLM every tick;
  the avatar is fast control (Observation → policy → Action).

This gives a triangular relationship (Human—Agent—Daimon) where three intelligences coexist,
and where "Battles don't just involve characters; battles CREATE the characters." Implemented in
`src/robobladez/agent.py` (`AgentState`, `DaimonState`, `HumanInteractionEvent`) and
`src/robobladez/battle.py` (`BattleAvatar`).

## The four core ideas

### 1. Mechanical reveal → sealed strategic response

The body matchup is exposed **before** the intelligence test.

```text
bodies fight passively (no policy)
        ↓
MechanicalMatchupReport (win prob, advantages, vulnerabilities)
        ↓
both competitors reason against known mechanical asymmetry
        ↓
each privately builds a specialized battle avatar
        ↓
avatar is sealed (fingerprinted + committed)
        ↓
best-of-N strategic fight
```

This is why a weaker body can still win: the *policy* exploits the opponent's mechanical tendencies.
Implemented in `src/robobladez/battle.py` (Phase 1: mechanical reveal; Phase 2: sealed response; Phase 3: best-of-N).

### 2. Persistent character ≠ body ≠ battle policy

Boris persists while his body and his specialized match-policy evolve.

```text
AgentState      persistent identity (genesis, history, opponent models, daimon)
BladeSpec       physical substrate (mass, radius, spin, friction)
BattleAvatar    a locked, specialized policy for one match only
```

The permanent competitor and the temporary avatar are separate objects. Between-match evolution creates a new
version; it never edits the old one (Constitution rule 9). Implemented in `src/robobladez/agent.py`,
`src/robobladez/battle.py`.

### 3. Behavior creates identity

Daimons and signature moves emerge from measured competitive history, not arbitrary authorship.

```text
measured battle behavior
        ↓
EMA phenotype (aggression, mobility, center control, resource use, ...)
        ↓
elemental affinity projection (Earth/Water/Fire/Air/Aether)
        ↓
manifestation stages -> naming event -> ability lineage
```

"Daimon" is a *symbolic projection of how the agent actually plays*. Penelope reflects Boris; she does not
determine him. Implemented in `src/robobladez/agent.py` (`DaimonState`) and `src/robobladez/signatures.py`.

### 4. Simulation creates canon; generative media dramatizes canon

The anime/show is downstream of a real competitive history.

```text
canonical replay (digest-verified)
        ↓
events + analysis
        ↓
story beats
        ↓
shot specs
        ↓
LTX / ComfyUI (external, GPU)
```

The media layer may compress but never reverse a canonical outcome (Constitution rule 7). Implemented in
`src/robobladez/canon.py`, `story.py`, `shots.py`.

## Match length tests different intelligence

| Format | What it rewards |
|--------|-----------------|
| 1-round | prediction; gimmicks can win |
| 5-round | balance of strategy + adaptation via precommitted logic |
| 10-round | policy robustness + emergence |

Players use all three to evolve different aspects of themselves.

## Source → modern mapping

| Source concept | Modern equivalent |
|----------------|-------------------|
| Daimon (baby → named) | `DaimonState` EMA + naming at stage ≥2 |
| Superpower (water gun → beam) | `ability_lineage` (placeholder for `SignatureDetector` results) |
| Talisman / node | `BladeSpec` |
| Battle avatar (locked algorithm) | `BattleAvatar` (sealed policy) |
| Mechanical phase before strategy | `mechanical_report()` → `MechanicalMatchupReport` |
| Post-battle review / prediction error | `PostMatchReflection` |
| PZL stored match | canonical replay + `replay_digest` |
| "program the seed but nothing else" | sealed, seed-deterministic engine |

## What was deliberately discarded

Quantum/PennyLane, GDL/GNN as gameplay substrate, IPFS requirement, consciousness claims, fine-tuned Phi-3
bootstrap, NanoSwarm/viscoelastic machinery. None are needed to produce the four core ideas; they add
opacity without improving the game.
