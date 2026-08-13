from __future__ import annotations
import math
from .model import Vec2, BladeSpec, ArenaSpec, BladeState, Action, Event

EPS = 1e-12

def bowl_force(state: BladeState, arena: ArenaSpec) -> Vec2:
    r = state.pos.norm()
    if r < EPS:
        return Vec2(0.0,0.0)
    frac = r / arena.radius
    # Bowl gets less protective near the open rim, allowing energetic ring-outs.
    soften = 1.0
    if frac > arena.rim_softening_start:
        span = max(EPS, 1.0 - arena.rim_softening_start)
        soften = max(0.08, 1.0 - 0.92*(frac-arena.rim_softening_start)/span)
    mag = min(arena.max_bowl_force, arena.bowl_strength * r) * soften
    return state.pos.unit() * (-mag)

def control_force(state: BladeState, spec: BladeSpec, action: Action) -> Vec2:
    a = action.clamped()
    rhat = state.pos.unit()
    if rhat.norm2() < EPS:
        rhat = Vec2(1.0,0.0)
    that = rhat.perp()
    authority = spec.control_force * (0.20 + 0.80*a.boost)
    return rhat*(-a.radial*authority) + that*(a.tangential*authority)

def integrate_free(state: BladeState, spec: BladeSpec, arena: ArenaSpec, action: Action) -> None:
    a = action.clamped()
    f = bowl_force(state, arena) + control_force(state, spec, a)
    accel = f / spec.mass
    state.vel = state.vel + accel*arena.dt

    # Exponential drag is stable and timestep-friendly.
    state.vel = state.vel * math.exp(-spec.linear_drag*arena.dt)
    state.omega += (spec.control_torque*a.torque/spec.inertia) * arena.dt
    state.omega = max(-spec.max_spin, min(spec.max_spin, state.omega))
    state.omega *= math.exp(-spec.spin_drag*arena.dt)

    # Control has an explicit finite energy budget.
    control_load = (abs(a.radial)+abs(a.tangential))*0.5
    cost_rate = (0.38*a.boost*control_load + 0.16*abs(a.torque))
    state.energy = max(0.0, state.energy - cost_rate*arena.dt)
    if state.energy <= 0:
        # no control authority once depleted; already-applied control this tick is tiny
        pass

    state.pos = state.pos + state.vel*arena.dt
    if state.pos.norm() < arena.radius*0.28:
        state.center_time += arena.dt

def resolve_disk_collision(a: BladeState, b: BladeState, sa: BladeSpec, sb: BladeSpec,
                           arena: ArenaSpec, tick: int) -> Event | None:
    delta = b.pos-a.pos
    dist = delta.norm()
    min_dist = sa.radius+sb.radius
    if dist <= EPS or dist >= min_dist:
        return None

    n = delta/dist
    t = n.perp()

    # Positional correction to prevent persistent overlap.
    penetration = min_dist-dist
    inv_ma, inv_mb = 1/sa.mass, 1/sb.mass
    inv_sum = inv_ma+inv_mb
    a.pos = a.pos - n*(penetration*(inv_ma/inv_sum))
    b.pos = b.pos + n*(penetration*(inv_mb/inv_sum))

    # Contact point velocities include spin.
    va_c = a.vel + t*(a.omega*sa.radius)
    vb_c = b.vel - t*(b.omega*sb.radius)
    rv = vb_c-va_c
    vn = rv.dot(n)
    if vn >= 0:
        return None

    e = min(sa.restitution,sb.restitution)
    jn = -(1+e)*vn/inv_sum

    vt = rv.dot(t)
    denom_t = inv_sum + sa.radius*sa.radius/sa.inertia + sb.radius*sb.radius/sb.inertia
    jt_unc = -vt/denom_t
    mu = math.sqrt(sa.contact_friction*sb.contact_friction)
    jt = max(-mu*jn, min(mu*jn, jt_unc))

    J = n*jn + t*jt
    a.vel = a.vel - J*inv_ma
    b.vel = b.vel + J*inv_mb

    # Angular impulse from tangential contact.
    a.omega += (-sa.radius*jt)/sa.inertia
    b.omega += (-sb.radius*jt)/sb.inertia

    impulse = math.hypot(jn,jt)
    excess = max(0.0, impulse-arena.burst_impulse_threshold)
    if excess:
        damage = excess*arena.damage_scale
        a.integrity = max(0.0,a.integrity-damage)
        b.integrity = max(0.0,b.integrity-damage)

    return Event(
        tick=tick, t=tick*arena.dt, type="collision",
        actor=a.id, target=b.id,
        importance=min(1.0, impulse/max(arena.burst_impulse_threshold,EPS)),
        data={"normal_impulse":jn,"tangent_impulse":jt,"total_impulse":impulse}
    )

def total_mechanical_energy(state: BladeState, spec: BladeSpec) -> float:
    trans = 0.5*spec.mass*state.vel.norm2()
    spin = 0.5*spec.inertia*state.omega*state.omega
    return trans+spin
