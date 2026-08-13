# RoboBladez + LTX-2.5

## Core rule

LTX does not decide what happened.

```text
MATCH
→ REPLAY
→ CANONICAL EVENT
→ SHOT SPEC
→ LTX
→ QA AGAINST REPLAY
```

## Shot routing

### Arena establishing
T2V or I2V.

### Character / talisman intro
I2V from canonical reference.

### Exact battle event
Use strongest available structural control:
- first/last frame
- keyframe
- motion/depth/pose/edge control
- V2V if a deterministic guide render exists

### Daimon manifestation
More generative freedom is acceptable because it is a narrative projection.

### Commentary/replay
Use deterministic replay graphics; LTX footage is dramatization only.

## Example ShotSpec

See `shot-spec.example.json`.
