# Jumpover Fall-Through Regression Contract

Status: bounded fidelity regression target. This document does not authorize a physics change.

## Purpose

Preserve the known Jumpover fall-through edge case as deterministic evidence before any later collision, camera, Widescreen, Remastered, or host-presentation change accidentally alters it.

The project already treats stock simulation as authoritative. This slice therefore asks one narrow question: can the current native build reproduce the established Jumpover fall-through from both known approach directions while an ordinary halfpipe traversal remains unchanged?

## Current status — 2026-10-08

**Historical reference: reproduced. Native: not yet attempted.** The dated evidence is in R-2026-10-08-PHYS-01 in `docs/RESEARCH-LEDGER.md`.

- **Source provenance gate (merged #841).** `tools/check_jumpover_source_preflight.py` verifies both recovered SMVs, input runs, 1.51 freeze and WRAM hashes, and direction-matched original Lua scripts against `analysis/generated/jumpover-fallthrough-source-preflight.json`. It explicitly reports `native_admitted: false`.
- **Trace-integrity gate (merged #842 plus empty-capture follow-up).** `tools/probe_jumpover_fallthrough.py` refuses missing/duplicate/out-of-order frames, shifted case/control starts, misaligned first-divergence traces, and captures that stop before the full post-crossing airborne witness. Empty captures cannot be interpreted as parity. These checks validate the reference *measurement* only, not a native physics match.

- **Anchor.** Each recovered SMV embeds its complete Snes9x 1.51 starting freeze. `tools/extract_smv_freeze.py` validates it and records hashes and symbolized fields in `analysis/generated/jumpover-fallthrough-anchors.json`. Both anchors are mid-race on Jumpover with P1 grounded before the halfpipe. The saved PC is inside the bank-82 racer update, so the anchor is not a race-loop frame boundary.
- **Reference replay.** `tools/probe_jumpover_fallthrough.py` replays each movie, unchanged and with a 60-frame held-input extension, in Snes9x 1.51-rr. Each run is repeated and the repeats are byte-identical. Results are in `analysis/generated/jumpover-fallthrough-reference-replay.json`. Frame k is the state after k movie frames.

  | Route | Lip contact | Leaves surface | First frame below control floor | Ordinary control (shoulder released on sample 42 only) |
  |---|---|---|---|---|
  | left | 44–47 | 48 | 64 (Y > 764; after the 53-frame movie ends) | wall hit at 44, floor contact from 54 |
  | right | 44–47 | 48 | 63 (Y > 759; inside the 73-frame movie) | wall hit at 44, floor contact from 54 |

  First divergence from the control is frame 43, P1 pitch (right also contact word). The contact-state divergence is frame 44 (left) / 43 (right).
- **Sensitivity.** The outcome depends on P1's pitch at the lip. Input acts on every second frame in this window: odd-sample shoulder releases and a one-frame sequence delay are byte-identical no-ops. A two-frame delay moves takeoff from frame 5 to 7 and gives the ordinary outcome.
- **Rejected harnesses.**
  - Writing P1 X (`7E:0411`) into the anchor WRAM is overwritten by the in-progress update, so the historical X sweep is not reproduced.
  - The pinned modern snesref core rejects the 1.51 freeze format (`#!snes9x`, not `#!s9xsnp`).

**Next discriminator (native).** The admission rule requires a fresh process and canonical stock state, so pick and justify one anchor route before any native run:

1. **Fresh-process input route.** Reach the Jumpover halfpipe approach from boot with an equivalent P1 state, then replay the movie's input sequence on the same 2-frame input phase. Feasibility is unknown. Takeoff must land within one 2-frame input step of the movie's takeoff, about 31 X units at anchor speed. The cheapest probe is to measure how wide the reference fall-through window is in approach X, using a pause-sequence X write like the historical scripts.
2. **Anchor transplant as a test harness.** Advance the 1.51 reference to a true race-loop frame boundary. Capture WRAM there, which includes the `7E:A000/C000` course planes. Inject it into a fresh native process that is idle at the same loop point in a Jumpover race. This is not canonical stock state. Whether the contract admits it is a decision for this document's owner. A modern snesref comparison would need the same transplant.

Either way, the native check compares the retained reference events: lip contact 44–47, the control-floor crossing at 64/63, and both controls staying ordinary.

## Scope

The regression owns only event-relative observation and fixture admission for the existing behavior. It must not:

- patch collision or contact code;
- change track geometry, activation, camera, physics, boost, or stunt semantics;
- normalize the two approach directions into one assumed cause;
- use absolute desktop frame numbers as the acceptance authority;
- turn into a general search for new glitches.

Use the existing canonical course identity and native/Snes9x evidence machinery. If the current repository already contains a stronger equivalent fixture, close this slice as duplicate rather than creating another authority.

## Four-case matrix

Capture exactly these cases from a fresh process and canonical stock state:

1. ordinary Jumpover traversal from the left that does not fall through;
2. the established left-side fall-through reproduction;
3. ordinary Jumpover traversal from the right that does not fall through;
4. the established right-side fall-through reproduction.

The ordinary cases are controls, not attempts to prove that all nearby trajectories are safe.

For each case retain the smallest event-relative window that includes:

- the last stable supported/contact state before the decisive transition;
- the first frame on which the falling case differs from its direction-matched control;
- the first unambiguous post-transition state;
- rider world position/velocity and the already-authoritative contact/collision state needed to explain that transition;
- course identity and build/source revision.

Anchor the window to semantic/contact transitions or the first divergent state. A capture may record absolute frame numbers as diagnostics, but acceptance must not depend on them.

## Admission rule

The fixture is sufficient when all of the following hold:

- both established fall-through routes reproduce from a fresh process;
- both direction-matched ordinary controls remain ordinary traversals;
- repeated runs identify the same first semantic divergence for each route;
- native and the accepted stock reference agree on the observed transition within the project's existing event-relative tolerance policy;
- guest state before the divergence is not altered by any host-only presentation feature used during capture;
- the retained artifact is small enough to diagnose a future regression without replaying an open-ended exploratory session.

If only one direction reproduces, retain that result as evidence but do not infer symmetry. Investigate the smallest input/state difference before changing authoritative code.

## Stop rule

Stop immediately after the four cases are admitted or a concrete first-divergence mismatch is isolated. A mismatch becomes its own bounded fidelity investigation.

Do not expand this work into a catalogue of collision exploits, search adjacent courses, or change simulation merely because the behavior looks undesirable. Expert-player reports may select another case later, but every additional case needs its own reproducible discriminator.

## Expected durable outputs

A production implementation should add only what is necessary to make this contract executable:

- one small deterministic input/capture fixture per distinct route when existing fixtures cannot be reused;
- one analyzer/checker that compares the event-relative observations;
- compact generated evidence identifying build, course, route, transition and observed state;
- focused unit coverage for malformed/missing evidence and the direction-matched control requirement.

The canonical work queue should be updated only after the regression is executable and retained evidence has passed.
