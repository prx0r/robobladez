# Physics Scope

## v2 model

The body is a planar rigid disk with:

- mass `m`
- radius `r`
- moment of inertia `I = k m r²`
- center position / velocity
- angular spin `ω`
- restitution
- Coulomb-limited contact friction
- linear/spin drag
- finite actuator force/torque
- finite energy budget

Disk-disk impacts use normal and tangential impulses. Tangential contact velocity includes each
blade's angular spin, so contact friction can exchange translational/angular motion.

The stadium is intentionally a **2D open bowl approximation**. Both competitors launch with the same spin/orbit handedness so the initial state is rotationally symmetric rather than accidentally privileging one slot:

```text
restoring force toward center
→ weakens near rim
→ center can cross open rim
→ ring-out
```

This is not claimed to reproduce a manufactured Beyblade stadium.

## Terminal conditions

- `ring_out`
- `spin_out`
- `burst`
- `double_*`
- `time_draw`

No arbitrary judge score is used at the time limit. It is a draw.

## Why this is honest

The game needs a stable deterministic ruleset before it needs physical validation.

Future physical-validation work should compare:

- trajectories
- spin decay
- collision restitution
- ring-out frequency
- angular response

against real tops or a 3D validated backend.

When that happens, implement `PhysicsBackendV2` and increment `engine_version`.
Do not silently change historical matches.
