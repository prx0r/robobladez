# Media Pipeline

## Canonical principle

The simulation is ugly and authoritative.
The episode is beautiful and subordinate.

```text
MatchResult
  ↓
Replay
  ↓
Event importance
  ↓
Story beats
  ↓
Shot specs
  ↓
LTX / ComfyUI
  ↓
episode
```

## What LTX receives

Each shot should contain:

```text
subjects
canonical visual versions
arena
start state
end state
action
camera
duration
continuity constraints
```

The MVP emits compact shot JSON.

## Identity continuity

Later maintain a `SeriesBible` containing:

- competitor appearance
- blade appearance
- daimon manifestation
- recurring arena grammar
- signature-move visualization
- camera grammar
- musical motifs
- previous episode summaries

## QA

Generated clips should be rejected if they:

- swap competitor identity
- reverse the result
- show impossible event order
- contradict the canonical arena/state
- invent a decisive event

The same replay can generate many projections:

- raw/debug viewer
- sports replay
- short clip
- anime episode
- commentary breakdown
