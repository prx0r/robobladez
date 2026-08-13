# LTX Prompting Guide

## Shot grammar

Write prompts chronologically, like a cinematographer describing one shot.

Recommended order:

```text
MAIN ACTION
→ SECONDARY MOTION
→ SUBJECT APPEARANCE
→ ENVIRONMENT
→ CAMERA
→ LIGHT
→ AUDIO
→ END STATE
```

## Template

```text
[SHOT SCALE]. [SUBJECT] performs [MAIN ACTION] while [SECONDARY ACTION].
The scene is [ENVIRONMENT].
The camera [POSITION + MOVEMENT RELATIVE TO SUBJECT].
Lighting is [SOURCE + DIRECTION + QUALITY].
Audio: [AMBIENCE], then [SFX synchronized to event], with [dialogue/music if needed].
By the end of the shot, [EXPLICIT FINAL STATE].
```

## Good constraints

Prefer:
- concrete movement
- one dominant action
- explicit chronology
- explicit end state
- camera movement relative to the subject
- physical acting cues
- local sound events

Avoid:
- keyword soup
- contradictory camera moves
- many unrelated events in one short shot
- relying on generated readable text
- asking prompt text alone to enforce precise physics

## Example — precise transition

```text
A low tracking shot follows the subject from left to right. It begins near the center of frame and accelerates smoothly toward the outer edge while the camera remains parallel. At the midpoint, one impact occurs and the subject changes direction sharply. By the end of the shot it is moving away from the camera at reduced speed. Audio: continuous mechanical hum, one impact synchronized exactly with the collision, then lower ambient resonance.
```
