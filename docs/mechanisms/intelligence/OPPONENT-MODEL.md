# Mechanism: OPPONENT MODEL

## Purpose
Give a persistent competitor a structured model of how an opponent plays, built from observed
history. This is the substrate of recursive game theory: my model of you, your model of me,
and the counterplay both produce (rm5 #14). It is an ANALYTICS projection of past matches.

## Canonical status
ANALYTICS (never feeds back into the engine's sealed match).

## Inputs
- `AgentState` of the opponent (its daimon + history), and the match outcomes.
- Built incrementally by `AgentState.remember_match` → `OpponentModel.observe`.

## State
- **Persistent**: per-opponent `OpponentModel` stored on each agent (`agent.opponent_models`).

## Transition
```
FOR each match vs opponent O:
    model = agent.opponent_models.setdefault(O.id, OpponentModel(O.id))
    model.matches += 1
    if result == my_id: model.wins += 1
    model.dominant_elements.append(O.daimon.dominant())   # capped at 8, dedup consecutive
```
`OpponentModel` (src/robobladez/agent.py):
```
agent_id, matches, wins, dominant_elements, notes
```

## Outputs
- Per-opponent `OpponentModel`, exposed in `AgentState.profile()`.

## Invariants
1. Built only from public outcomes (winner + opponent daimon projection).
2. Does not reveal the opponent's internal policy state.
3. Monotonic in match count; appends, never silently rewrites history.

## Information visibility
- **PRIVATE** to the owning agent. Opponents cannot read it.
- **POST_MATCH/ANALYSIS**: can be revealed for spectator insight (rm5 #25).

## Determinism
- Pure aggregation of deterministic match outputs. No RNG.

## Failure modes
- None structural; stale models if not updated (ensure every match calls `remember_match`).

## Edge cases
- No matches yet against an opponent → model absent (policies must handle missing models).
- Opponent's daimon changes element mid-stream → `dominant_elements` records the transitions.

## Telemetry
- `matches`, `wins`, `dominant_elements` per opponent.

## Versioning
- Model fields are part of `AgentSnapshot` (versioned via `agent_snapshot`).

## Security
- Models are analytics; they must never be injected into the sealed engine's policy
  commitment (which is locked before the match).

## Tests
- `tests/test_agent.py::AgentTests::test_agent_remembers_and_models_opponent`.

## Examples
**Normal**: Boris vs Morty twice; Morty's model records matches=2 and both wins (or split).
**Adversarial**: An agent tries to read the rival's `opponent_models` during the match — it is
a private analytics object, not in the Observation schema; unreachable from `decide()`.

## Non-goals
- Does NOT predict next actions in real time (policy responsibility).
- Does NOT define strategic deception detection (see STRATEGIC-DECEPTION — planned).
