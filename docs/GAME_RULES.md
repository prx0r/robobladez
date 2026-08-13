# Game Rules

## The unique mechanic

1. A body configuration is public.
2. A deterministic/mechanical baseline may be run.
3. Both agents receive the matchup evidence/history available to the league.
4. Each prepares a match-specific policy.
5. The policy is committed/locked before play.
6. Every decision step is simultaneous.
7. The simulation resolves the actions.
8. In multi-round matches, policy code remains fixed but its allowed internal state may update.
9. After the match, the policy and replay may be revealed for analysis.
10. Between matches, a new policy version may be produced.

## Match lengths

- BO1: prediction, surprise, exploit
- BO5: prediction + adaptation
- BO9/long: robustness + information gathering + meta-strategy

The MVP implements odd best-of-N.

## Genesis versus evolution

`GenesisSeed` should eventually be immutable. Everything thereafter is versioned:

```text
agent genesis
  → body v1
  → policy v1
  → matches
  → analysis
  → body/policy v2
```

No hidden manual retcon of results.

## Abilities

Do not use quantum-computing libraries to implement fictional abilities.

An ability should be a transparent game rule with:

```text
id
trigger
cost
cooldown
duration
state transition
visual projection
```

The MVP deliberately omits abilities until base strategic play is stable.
