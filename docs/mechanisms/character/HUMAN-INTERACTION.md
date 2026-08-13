# Mechanism: HUMAN INTERACTION

## Purpose
Define how a human owner/mentor interacts with an Agent without becoming a joystick operator.
The human creates the genesis, then mentors/proposes/negotiates — but cannot secretly overwrite
the competitor (rm6). Every interaction is a canonical, append-only event.

## Canonical status
ANALYTICS + INFRA (shared history is a character signal; it never affects the sealed engine).

## Inputs
- `HumanInteractionEvent` (src/robobladez/agent.py):
```
type, human, agent, content, timestamp, agent_response, adopted
```

## State
- **Persistent**: `AgentState.interactions` (list of serialized events).
- The Agent's `goals` (also on AgentState) can be updated by the agent in response.

## Transition
```
human proposes (genesis | advice | approval | conversation)
        ↓
record HumanInteractionEvent on the agent
        ↓
agent may incorporate, ignore, or push back (its own cognition)
        ↓
`adopted` records whether it followed the advice
```
Human authority matrix (rm6):
- Genesis identity: Human **Primary**, engine validates.
- Long-term goals: Human proposes, Agent **chooses/updates**, Daimon advises.
- Body development: Agent **proposes**, Daimon advises, Human **approves/resources**.
- Opponent study / match strategy: Agent **primary**, Human may discuss, Daimon assists.
- Battle Avatar: Agent creates, Daimon may influence, Human has **no editing after commit**,
  Engine **locks**.
- Per-tick action / battle result: **none** for human — no joystick, no mid-battle prompts.

## Outputs
- An append-only `interactions` list on the agent; shared history between human and agent.

## Invariants
1. Interactions are append-only; never silently rewrite the agent.
2. The human can NOT edit a committed Battle Avatar or influence per-tick actions.
3. A `HumanInteractionEvent` is canonical: type, human, agent, content, adopted.
4. Interactions are analytics — they never feed into the sealed engine.

## Information visibility
- **PUBLIC** (canonical shared history), revealable post-match for narrative.

## Determinism
- Interaction storage is deterministic; the agent's *response* may involve LLM reasoning
  (NARRATIVE) but the stored event is canonical.

## Failure modes
- None structural.

## Edge cases
- `adopted=False` → agent ignored advice (itself a character signal: e.g. "Tom told me to
  attack early. I ignored him. He was right.").

## Telemetry
- `interaction_count` in `AgentState.profile()`.

## Versioning
- Interactions are versioned under the agent snapshot lineage (AGENT-VERSIONING).

## Security
- Human interactions must never bypass the engine (no "use superpower" button mid-match).

## Tests
- `tests/test_agent.py::test_human_interaction_is_append_only`.

## Examples
**Normal**: Human records `MENTOR_ADVICE` ("Morty exploits your rim movement"); agent stores it.
**Adversarial**: A human tries to force a mid-battle action — blocked: interactions are
between-match only, per-tick is the avatar's domain.

## Non-goals
- Does NOT define the agent's cognition (that is the Agent AI / LLM layer).
- Does NOT define reincarnation (REINCARNATION).
