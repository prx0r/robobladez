# Mechanism: POST-MATCH REFLECTION

## Purpose
Generate a structured, metric-driven learning artifact after each match, so a persistent agent
"leaves a plan for its future self" — the modern, non-mystical form of the old persistence ideas
(rm5 #7, vsynthesis). This drives between-match evolution.

## Canonical status
ANALYTICS (feeds evolution; never the sealed engine).

## Inputs
- `match: MatchResult`, `self_id: str`, `opponent_id: str`.
- The match's `analyze_behavior` daimon affinities (for the daimon EMA).

## State
- **Persistent**: appended to `AgentState.match_history` as a reflection dict.

## Transition
```
1. count self/opponent collisions from match events
2. won = (match.winner == self_id)
3. what_worked / what_failed / beliefs / proposed_experiments  = rule-based
4. remember_match(opponent, affinities, opponent_daimon, result, reflection)
```
`reflect()` in `src/robobladez/evolution.py` produces a `PostMatchReflection`:
```
agent_id, opponent_id, result, what_worked[], what_failed[],
beliefs[], proposed_experiments[]
```
The reflection's `agent_id`/`opponent_id` are the persistent character ids, not blade ids.

## Outputs
- `PostMatchReflection` dict stored in `AgentState.match_history[-1]["reflection"]`.

## Invariants
1. Deterministic given the match (rule-based, no RNG).
2. Refers to the persistent agent, not the ephemeral blade.
3. Never modifies the sealed match or its digest.
4. Append-only: each match adds one reflection; history is capped at 200.

## Information visibility
- **PRIVATE** to the agent.
- **POST_MATCH/ANALYSIS**: revealable for commentary (rm5 #25).

## Determinism
- Pure function of match events. No RNG.

## Failure modes
- None structural; a match without events still produces a (mostly empty) reflection.

## Edge cases
- Draw match → `result=None`; `what_worked`/`what_failed` reflect a non-win.
- No collisions → both sides report "lost the contact/impulse trade" (false positive is
  acceptable; it is heuristic).

## Telemetry
- Per match: `what_worked`, `what_failed`, `beliefs`, `proposed_experiments`.

## Versioning
- Stored under the agent's current version in `agent_versions` (AGENT-VERSIONING).

## Security
- Reflections are analytics; never injected into a sealed policy. Future LLM summarization
  must be clearly labeled NARRATIVE (cannot change canonical match facts).

## Tests
- `tests/test_protocol.py::BattleTests` (reflections present with correct agent ids).
- `tests/test_agent.py::AgentTests::test_agent_remembers_and_models_opponent`.

## Examples
**Normal**: Boris wins; reflection records "won the match across the sealed-policy rounds".
**Adversarial**: A reflection is generated with `result` that contradicts the match winner —
prevented because `reflect` derives `result` from `match.winner` internally.

## Non-goals
- Does NOT mutate the policy (that is POLICY-EVOLUTION).
- Does NOT produce prose narration (LLM layer is NARRATIVE, downstream).
