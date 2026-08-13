# The Blade — What a Blade Is

The single most important object in RoboBladez. This spec makes the ontology
explicit and enforceable.

## 1. A blade is a deterministic material thing

A blade (`BladeSpec`) is a **fixed, immutable physical parameter set**. It is
NOT an actor, NOT a mind, NOT a strategy. It is a *boundary condition of the
physics* and nothing more.

```
mass, radius, inertia_factor      -> how heavy / spread it is
restitution, contact_friction     -> how it bounces / grabs
linear_drag, spin_drag            -> how it loses energy
control_force, control_torque     -> how much the policy can steer it
max_spin, launch_spin, launch_speed -> spin budget
energy_capacity, integrity        -> the two resource bars
```

There is no blade intelligence, no blade personality, no blade strategy.

**Why it must be material, not mind:** if the blade had intelligence, `Body`
and `Reincarnation` would collapse into one object and the game-theory layer
dissolves. The blade being *dumb* is precisely what lets the *policy* be smart.

**Determinism contract:** `BladeSpec + Arena + Policy + Seed = exact match`.
A blade is reproducible and hashable (`body_digest`).

## 2. The editing regime (who can edit, when)

A blade changes only as a **new public version, proposed by the Agent, before
the match**. Nothing else edits it.

| Actor | Edit mid-match? | Edit between matches? |
|---|---|---|
| **Engine** | No (frozen at match start) | N/A |
| **Policy / Reincarnation** | No (sealed) | No — it only *controls* the blade |
| **Agent** | No | **Yes** — proposes a new `BladeSpec` version |
| **Daimon** | No | **No** — only *advises* the Agent |
| **Human** | No | Approves / allocates resources |

### The two times a blade can differ

```
WITHIN a match:     body frozen. IMMUTABLE. (the fight is decided on this body)
BETWEEN matches:    Agent proposes body-v1 -> body-v2 (a NEW public version)
```

### Why weight editing is the game-theory gold

Because bodies are **public** and **versioned**, weight is a *strategic signal*,
not just a physical fact:

- Boris runs heavy for 3 matches -> opponents build anti-tank policies
- Boris evolves to light -> opponents' sealed policies are now miscalibrated
- This is **strategic deception in the body dimension**, mirrored in the policy
  dimension.

```
choose body (public, slow)  +  author reincarnation (sealed, fast)  =  strategy
       announced hand                 hidden hand
```

## 3. How the Daimon relates to the blade

The Daimon **never touches the blade**. It is non-causal (Constitution rule 8).
It can attach **advice** to a `BodyProposal` (e.g. "your mass is wrong for a
counter meta"), but it cannot change the mass.

**Why:** if a Daimon could edit the blade, `Daimon` and `Body` collapse, and the
Daimon's power becomes arbitrary physics-tampering instead of earned influence.
The Daimon's whole purpose is to *advise from history*, never override the engine.

## 4. How this adds up to tactics and game theory

**A. Deterministic-material substrate = fair, legible physics.** Both agents
read the same mechanical report; neither can cheat; only *belief* differs.

**B. Versioned bodies = commitment + reputation economy.** A body version is
public and immutable once announced. Enables reputation, counter-preparation,
and bluffing (signal one weight, deliver another).

**C. Reincarnation separate from body = incomplete information.** Opponent sees
your body (perfect info on equipment) but not your sealed battle-self (imperfect
info on intent). This is Oshi-Zumo / RPS structure: the body suggests one
strategy, the reincarnation delivers another.

**D. Two-level game:**
```
LEVEL 1 (slow, public):  body choice   -> reputation + meta
LEVEL 2 (fast, sealed):  reincarnation -> prediction + counter
```

## 5. The design constraint that makes it all work

Blade editing is **slow (between-match), public (versioned), and Agent-only**
(with Daimon advice + human approval). If weight could be edited fast or
secretly, the two-level structure collapses into a shallow twitch game.

## Enforced schema

See `src/robobladez/competition.py`:
- `BladeSpec` — the immutable material thing
- `BodyVersion` — a versioned, hash-bound blade (announced)
- `BodyProposal` — Agent proposes a new body; Daimon attaches advice (never edits)
- `CompetitionEntry` / `EntrySnapshot` — bind the announced body version + digest
