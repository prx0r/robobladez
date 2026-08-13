# Mechanism Spec Template

Every mechanism in RoboBladez is specified with this exact template. A mechanism is a
single well-bounded rule, process, or object that the engine or a projection layer guarantees.
Use this file as the required skeleton for every document under `docs/mechanisms/`.

> A mechanism doc is only "done" when every section below is answered without ambiguity,
> including the sections that might be "not applicable" (write "N/A" explicitly, do not omit).

---

# Mechanism: <NAME>

## Purpose
Why this mechanism exists. What problem it solves for the game, the canon, or the media layer.

## Canonical status
One of:
- **GAMEPLAY** — part of the deterministic engine; affects who wins. (Highest rigor.)
- **ANALYTICS** — derived from gameplay but never feeds back into it.
- **NARRATIVE** — projection/dramatization; explicitly non-causal.
- **INFRA** — plumbing (storage, versioning) with no gameplay meaning.

## Inputs
Exact input objects and their types (reference the dataclass/schema names).

## State
- **Persistent**: state that survives across matches (schema, keyed by what).
- **Ephemeral**: state that exists only within a match/round.

## Transition
Formal sequence of steps, in order. Use numbered steps or a `STATE(t) → STATE(t+1)` diagram.
This section MUST be unambiguous — a reader must be able to implement it exactly.

## Outputs
Objects/events emitted (event type names, telemetry fields).

## Invariants
Things that can never be violated, even under bugs/attacks. Each invariant should be
independently testable (property tests reference these).

## Information visibility
Who can see what, and when. Use the PUBLIC/PRIOR/POST visibility classes:
- **PUBLIC_BEFORE_MATCH** — visible to both competitors before strategy commit.
- **PRIVATE** — visible only to the owning agent (and to analysis post-match).
- **OBSERVABLE_DURING** — visible to the agent each tick.
- **POST_MATCH** — revealed only after the match (e.g. policy reveal).
- **NEVER** — never revealed to competitors (e.g. opponent internal state).

## Determinism
How RNG and time are handled. Reference `policy_rng`, seed derivation, and the rule that
policies may not use wall clock / `os.urandom` / unseeded `random`.

## Failure modes
Timeout, invalid action, non-finite state, corrupted replay, disconnected policy, etc.
For each: detection, response, and effect on determinism/canon.

## Edge cases
Tie, double KO, ring-out simultaneous, energy = 0, spin below min at tick 0, policy that
returns out-of-range action, empty prior_round_winners, etc.

## Telemetry
Exact metric names emitted for this mechanism (used by analysis/narrative).

## Versioning
What increments version, and how historical instances stay reproducible.

## Security
Sandbox implications: what an untrusted policy could try and how this mechanism is
isolated from it.

## Tests
Required tests: unit, property/invariant, determinism, fuzz. Reference `tests/` files where
they exist, or list the required tests if not yet implemented.

## Examples
- **Normal**: a typical execution trace.
- **Adversarial**: an attempt to violate an invariant or exploit the mechanism.

## Non-goals
What this mechanism explicitly does NOT establish (prevents scope creep and ambiguity).
