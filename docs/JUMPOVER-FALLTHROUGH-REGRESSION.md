# Jumpover Fall-Through Regression Contract

Status: bounded fidelity regression target. This document does not authorize a physics change.

## Purpose

Preserve the known Jumpover fall-through edge case as deterministic evidence before any later collision, camera, Widescreen, Remastered, or host-presentation change accidentally alters it.

The project already treats stock simulation as authoritative. This slice therefore asks one narrow question: can the current native build reproduce the established Jumpover fall-through from both known approach directions while an ordinary halfpipe traversal remains unchanged?

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
