# Build Order

## M0 — prove the constitution

Already scaffolded in this ZIP:

- seeded deterministic match
- simultaneous actions
- sealed policy commitment
- replay
- event log
- analysis
- canon DB
- story beats
- shot specs

Exit criterion: same inputs produce byte-equivalent semantic match data.

## M1 — mechanical game

Replace/simple-extend physics with validated spinning-top dynamics.

Add:

- angular velocity / moment of inertia
- contact geometry
- proper bowl surface
- spin decay
- ring-out
- mechanical baseline mode

Do not add AI training yet.

## M2 — real strategy game

Add:

- richer observation schema
- constrained action API
- policy execution limits
- public/private information model
- match-specific policy commit/reveal
- between-round internal memory

## M3 — league

Add:

- entrants
- scheduling
- rankings
- matchup matrix
- replay browser
- opponent dossiers
- versioned bodies/policies

## M4 — emergence

Add:

- phenotype history
- daimon naming thresholds
- signature detection
- policy lineage
- meta/counter-meta detection
- non-transitive matchup analysis

## M5 — media

Add:

- character/asset bible
- event-to-story LLM adapter
- shot continuity graph
- ComfyUI API adapter
- LTX render queue
- QA/retry
- FFmpeg assembly

## M6 — open league

Only after sandboxing is solid:

- external policy submission
- resource limits
- packaging
- deterministic verification
- public replay artifact
