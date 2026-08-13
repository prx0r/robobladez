# Data Model

## Long-term tables

```text
agents
agent_versions
bodies
body_versions
policies
policy_versions
arenas
matches
rounds
events
replay_frames
behavior_profiles
daimon_states
signature_patterns
opponent_models
rankings
story_beats
shot_specs
episodes
```

MVP embeds most state inside `matches.payload_json` and stores agent snapshots separately.

## Match reproducibility key

```text
engine_version
seed
arena config/version
body configs/versions
policy commitments
```

If any of these change, it is a different simulation.
