# Build Next

Do not widen scope until each stage passes its exit test.

## 1. Make the game strategically interesting

Add a small policy SDK and 8–12 hand-designed policies.

Measure:

- matchup matrix
- non-transitivity
- body-vs-policy contribution
- seed sensitivity
- action entropy
- exploitability proxies

**Exit test:** meaningful counters exist. No single policy dominates all bodies/arenas.

## 2. Validate the physics ruleset as a *game*

Not as real-world physics yet.

Run 100k+ headless rounds and inspect:

- termination distribution
- average duration
- collision counts
- ring-out/spin-out balance
- numerical stability
- side/slot bias

Tune only explicit ruleset parameters.

## 3. Mechanical baseline report

Generate machine-readable pre-match dossier:

```text
neutral win distribution
collision profile
spin endurance
rim vulnerability
body matchup asymmetry
```

This becomes the evidence agents strategize from.

## 4. Policy sandbox

Move policy execution out-of-process.

Contract:

```text
Observation JSON → Action JSON
```

Enforce:

- CPU budget
- memory budget
- no filesystem/network
- deterministic runtime
- versioned SDK

Use Robocode Tank Royale as the architectural precedent.

## 5. League/meta

Then add:

- policy lineages
- opponent models
- payoff matrix
- Elo for audience familiarity
- Alpha-Rank / PSRO-style analysis for non-transitive meta

## 6. Emergent narrative

Only after enough matches:

- recurring decisive pattern detection
- signature naming
- daimon stabilization thresholds
- rivalry/meta-change detection

## 7. LTX

Finally connect:

```text
canonical event → shot plan → conditioned LTX render → QA
```

The render system never feeds back into who won.
