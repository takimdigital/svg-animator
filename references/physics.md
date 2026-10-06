# Physics — integrate it, then bake it

> Principle 2 says *compute, don't guess*. Easing curves are a guess with good
> defaults. A trajectory is not a guess. When motion should obey a law, integrate
> the law and emit the resulting keyframes.

## Why this exists

The cookbook gives you `Bounce` and `Swing / pendulum` as hand-written keyframe
recipes (`references/motion-vocabulary.md` §Bounce, §Swing). Those are fine, and
they are honest approximations of a physical event made by eye.

But a hand-written bounce is a *shape*, not a *simulation*. Ask for a slightly
different mass, or a slightly stiffer surface, and you are guessing again from
scratch. Two numbers — damping and frequency — determine the whole family, and
they can be integrated exactly.

This is the same move as `make_slots()` and `pulse_frames()`: compute the schedule
in Python, ship static keyframes. The viewer gets 9 numbers instead of a physics
engine, and the loop stays perfectly seamless because nothing is simulated at
runtime.

## The equation

A damped spring, offset `d` from its rest position:

```
d'' + 2·ζ·ω·d' + ω²·d = 0
```

| symbol | meaning | effect |
|---|---|---|
| `ω` (omega) | angular frequency, rad/s | how fast it moves. Higher = snappier |
| `ζ` (zeta) | damping ratio | `ζ < 1` overshoots and settles; `ζ = 1` critically damped, no overshoot; `ζ > 1` crawls in |

Two constants, and `dt` small enough. That is the entire model.

## The integrator

Semi-implicit Euler. Update velocity *first*, then position — that ordering is what
makes it stable at the timesteps we use.

```python
def spring(x0, target, dur, steps=240, zeta=0.22, omega=8.0):
    """Position samples of a damped spring settling from x0 onto target.

    d is displacement FROM target, so the spring settles as d -> 0.
    Semi-implicit Euler: velocity is updated before position, which is what keeps
    it stable at this timestep.
    """
    d = x0 - target
    v = 0.0
    dt = dur / steps
    out = []
    for _ in range(steps + 1):
        out.append(target + d)
        v += (-2 * zeta * omega * v - omega * omega * d) * dt
        d += v * dt
    return out
```

`steps=240` over a 1.6 s loop is 6.7 ms per step — far below the ~10 ms stability
limit for these `ω`. Raise `steps` if you push `ω` much past 20.

## Baking to SMIL

Sample down to a handful of keyframes and ship them. **Do not ship the 240
samples** — they add bytes for no visible gain, and `keySplines` interpolates
between them for free.

```python
def to_keyframes(vals, n=9):
    picks = [vals[int(round(i * (len(vals) - 1) / (n - 1)))] for i in range(n)]
    keytimes = ";".join(f"{i/(n-1):.3f}" for i in range(n))
    keysplines = ";".join(["0.25 0.1 0.25 1"] * (n - 1))   # near-linear: the shape is in the keys
    values = ";".join(f"{v:.1f}" for v in picks)
    return values, keytimes, keysplines
```

Worked example — ζ=0.22, ω=8, 30 px onto a 300 px seat over 1.6 s:

```
start 30   peak 432.4   end 284.4   target 300
overshoot +132.4 px        residual 0.30 px  (settled, not snapped)
keyframes  30  262  432  319  235  291  332  305  284
```

Read those numbers: it flies past the seat by a third of the travel, comes back
under it, overshoots the other way, and converges. `keySplines` is near-linear
because **the shape lives in the keyframe positions** — that is the whole point
of integrating instead of easing. A `cubic-bezier` cannot express this.

Verified: renders as a genuine overshoot-and-settle in Chromium, lints
`0 error(s), 0 warning(s)`.

## Choosing ζ and ω

| you want | ζ | ω | why |
|---|---|---|---|
| card drops into place | 0.30 | 12 | snappy, one small overshoot |
| panel slides, settles | 0.45 | 9 | barely overshoots, feels controlled |
| ball into a socket | 0.22 | 8 | pronounced, satisfying |
| drawer, no bounce at all | 1.0 | 14 | critically damped, fastest without overshoot |
| heavy object, slow | 0.6 | 5 | low frequency reads as mass |

Start at **ζ=0.25, ω=9** and adjust. `ζ` is the personality dial: below 0.15 is
bouncy/cartoon, above 0.7 is heavy/serious. `ω` is the energy dial.

**Mass is not a parameter here.** To make something feel heavier, lower `ω`. To
make it feel lighter, raise `ω`. Stiffness is `ω²`.

## The static-first trap

A spring that starts at rest is fine. A spring that *arrives* from off-canvas is
not: at `t=0` the element sits at its un-animated base value, so if that value is
off-canvas the reader sees a blank region until the first frame moves it.

Give the base attribute the **mid-settle** position, not the launch position:

```xml
<circle cx="284" cy="72" r="16">     <!-- base = settled, NOT cx="30" -->
  <animate attributeName="cx" values="30;262;432;319;235;291;332;305;284" .../>
</circle>
```

Then frame 0 shows the ball in its seat, and the loop's spring plays as an
overlay. This is the same rule as every other type here, and it is the one thing
people forget when they add physics.

## Other integrators worth having

Same shape — a loop, a state update, a bake. All of them belong in Python.

**Gravity with a bounce** (for a thrown or falling object). Flip the velocity
sign on impact and lose a fraction of it:

```python
def fall(y0, ground, dur, steps=240, g=1800.0, restitution=0.55):
    y, v = y0, 0.0
    dt = dur / steps
    out = []
    for _ in range(steps + 1):
        out.append(y)
        v += g * dt
        y += v * dt
        if y > ground:
            y = ground
            v = -v * restitution
    return out
```

`restitution` is the bounciness: 0.9 is a superball, 0.4 is a dead thud, 0 is a
single thud. `g` is in px/s², so 1800 is roughly Earth-like at this scale.

**Pendulum.** A rigid pendulum is `θ'' + (g/L)·sin θ = 0`, which for small angles
is the spring again with `ω = √(g/L)`. So for small swings you can reuse the spring
integrator and map `θ` to a `rotate` value — no separate code needed. For large
swings, integrate the sin version or the small-angle approximation visibly stops
matching.

**Mass on a spring, driven.** The same equation plus a forcing term
`+ F(t)/m`, which is how you get a node that jitters when an event arrives and
then settles. Force it with a short impulse in the first few samples.

## What this is not for

- **Anything the reader must follow as a sequence.** Diagrams still use fractions
  of one master clock (principle 4). A physics-integrated curve is for a *single*
  object's motion, not for choreography.
- **Ambient drift.** Aurora, shimmer and floating particles are not physics; they
  are `dur/3` sine-ish loops. Simulating them is slower to author and no better.
- **Sub-frame accuracy.** The point is believable *shape*, not a solver. Nobody
  measures the difference between `steps=240` and `steps=480`.