# Combat Engine — Current State & Physics-Quality Ambition

## 1. What the combat engine IS right now

A **planar rigid-disk 2D kernel** (`physics.py`, `engine.py`). Honest and
deterministic, but deliberately NOT "physics simulation quality" in the
real-spinning-top sense. Its degrees of freedom:

```
position (x, y), velocity (vx, vy)     -> planar translation
angular spin omega                      -> one scalar (rotation rate)
mass m, radius r, inertia I = k·m·r²
restitution, contact_friction
linear_drag, spin_drag
control_force, control_torque           -> the policy's steering authority
energy_capacity, integrity              -> two resource bars
```

Collision is **disk-disk impulse** with normal + Coulomb-limited tangential
impulse; tangential contact velocity includes each blade's spin (so friction
exchanges translational/angular motion). The stadium is a 2D open-bowl
approximation (restoring force toward center, weakening near the rim).

Terminals: `ring_out`, `spin_out`, `burst`, `double_*`, `time_draw`. No invented
score at the limit.

### What it does NOT model (the gap to physics-simulation quality)

- **Precession / gyroscopic wobble** — real tops precess and nutate; we have a
  single scalar `omega`.
- **Tilt / tipping** — a real blade tips over its tip; we are strictly 2D.
- **Center-of-mass offset** — a blade's CoM is off-axis (that's what causes
  a real Beyblade to walk/precess); we model CoM == geometric center.
- **3D contact / body parts** — no ring, contact polygon, tip geometry, or
  radial mass profile. The `BodyVersion`/`BladeSpec` is a parameter set, not a
  body grammar.
- **Tip friction / rolling resistance** — our drag is uniform linear+spin.

**Why it's 2D first (deliberate):** the game-theory layer (sealed reincarnation,
mechanical reveal, evidence-bearing emergence) is the moat and is
backend-agnostic. The tiny kernel proves the competition contract now; a
fidelity upgrade can replace the physics backend without touching canon or
policy semantics (see `docs/PHYSICS_SCOPE.md`).

## 2. The ambition: push toward physics-simulation quality

The source material (`q2.txt`, `overview_robobladez.txt`) always wanted
real physics (PyBullet). The review discipline correctly **discarded the
quantum/PennyLane theatre** but kept the physics goal. The honest path to
"literally almost like a physics simulation":

```
V0 (now):       planar rigid-disk kernel          (2 scalar degrees, disk collision)
V1 (next):      add center-of-mass offset + precession
                -> a blade with off-axis CoM walks/precesses (the real source of
                   Beyblade behavior)
V2:             add tilt/tipping + tip contact
                -> ring_out/spin_out become emergent from tipping, not threshold hacks
V3 (ideal):     rigid-body 3D (PyBullet) OR custom validated 2.5D top model
                -> validate trajectories, spin decay, restitution, ring-out freq,
                   angular response against real tops
```

Each step keeps the `PhysicsBackendV2` adapter boundary and increments
`engine_version` — historical matches stay reproducible (Constitution rule 2).

**Design law:** the physics engine must never become the LLM/policy's playground.
Policies/reincarnations only emit `Action`; the engine owns physics.

## 3. How physics quality translates to LTX (and why it matters)

This is the key insight. **LTX does not decide what happened; it renders it.**
The more physically faithful the engine, the better the LTX control signals:

```
DETERMINISTIC ENGINE (trajectory, spin, tilt, contact)
        ↓
canonical replay + CanonicalEvent (pre_state / post_state)
        ↓
control frames (first/last), keyframes, guide plates
        ↓
LTX-2.5 renders the interstitial cinematic motion
```

- A real top's precession gives LTX a **visually distinctive, physically
  plausible spin** to render — it "looks like a real Beyblade."
- Tipping/CoM-offset produce **emergent ring-outs and spin-outs** that are
  *physically motivated*, so the rendered drama matches the simulation.
- Better physics = better `pre_state`/`post_state` = better first/last control
  frames = less for LTX to hallucinate.

So "physics simulation quality" isn't just fidelity for its own sake — it
directly makes the **deterministic truth → LTX dramatization** pipeline cheaper
and more consistent, because the renderer has richer, more truthful control
signals to obey.

### What stays true regardless of physics fidelity
- `Simulation decides truth; media dramatizes it.` (Constitution rule 7)
- The blade is a deterministic material thing; the Daimon only advises.
- Non-transitivity is the goal (currently NOT achieved — see `docs/ROADMAP.md`).

## 4. Current combat-engine status (honest)

- **Deterministic + reproducible**: verified (same seed → same digest).
- **Strategy audit exists**: `robobladez audit-reincarnations` — 6 author
  archetypes; current result **73% decisive, NO non-transitive cycles, `pressure`
  dominates, `adaptive` loses to everything**. The game is NOT yet balanced.
- **Physics fidelity**: 2D disk kernel. CoM-offset/precession/tilt are the
  next fidelity steps.

## 5. Files

- `docs/BLADE.md` — blade ontology (material, editing regime, game theory)
- `docs/PHYSICS_SCOPE.md` — the physics model + honesty boundary
- `docs/mechanisms/physics/*.md` — BLADE-BODY, CONTACT-COLLISION, SPIN-DYNAMICS,
  STADIUM, ENERGY, INTEGRITY-BURST, RINGOUT-SPINOUT, LAUNCH
- `src/robobladez/physics.py`, `engine.py`, `model.py` — the kernel
- Source material: `q2.txt`, `overview_robobladez.txt` (archived; quantum
  framing discarded, physics/ability structure kept)
