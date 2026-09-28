# Open questions and discriminating tests

This page is a compact map of uncertainties whose resolution would collapse multiple downstream unknowns. Detailed experiment ownership remains with the specialist docs and work queue.

## 1. How does runtime track ID select an RNC stream?

Known:

- runtime bot uses track IDs 0-44;
- nine stunt IDs occur every fifth slot;
- 45 RNC streams exist;
- nine RNC streams every fifth slot carry the 45-second stunt marker.

Conflict:

- historical/internal tour ordering and earlier provisional stream-name ordering may not match.

Smallest useful test:

Select one known event, trace `7E:00CE` through the course loader, record packed source pointer, RNC stream ordinal and decompressed destination. Repeat with one event in a different tour.

Payoff:

Resolves track-ID/stream/name mapping and gives the first firm bridge from frontend selection to decoded course payload.

## 2. What is the decompressed course schema?

Known:

- RNC decode is established;
- historical work reports 256-tile width, 64x64 structures and 8x8 tile relationships;
- visual and collision data may be separable;
- `7E:2080` is a historical breadcrumb.

Smallest useful test:

Trace first reads of one freshly decompressed payload and classify consumers by whether they affect rendering, collision or event logic.

Payoff:

Unlocks a real course parser, renderer, custom-course path and stronger Widescreen staging logic.

## 3. Can the recovered bot drive both reference and native runtimes?

Known:

- source exists;
- frontend state logic exists;
- deterministic SMVs exist;
- native game reaches title screen.

Smallest useful test:

Port only enough bot state/input abstraction to reach the same one-player race in native and `snesref`.

Payoff:

Unlocks the fidelity harness, menu automation and autonomous regression.

## 4. Which bot/TAS RAM labels are exactly correct in the canonical ROM?

Known:

Several labels are independently corroborated, but the recovered Lua also contains duplicates/variants.

Smallest useful test:

Log candidate addresses during a controlled flat race, jump, stunt and menu transition.

Payoff:

Rapidly seeds `SYMBOLS.md` and anchors physics/camera/frontend routines.

## 5. Where are culling, OAM emission and camera boundaries?

Known:

Widescreen requires them to be treated as separate gates.

Smallest useful test:

Trace one racer/object from just outside stock visibility through culling decision, object activation and final OAM emission.

Payoff:

Turns generic SNESRecomp Widescreen patterns into Uniracers-specific hooks.

## 6. How is unicycle animation indexed?

Known:

Developer evidence points to a multidimensional rendered corpus and dedicated compression tooling.

Smallest useful test:

Hold movement state controlled while varying one animation dimension at a time and correlate resulting graphics uploads/OAM tile selection with ROM source ranges.

Payoff:

Unlocks semantic HD Presentation substitution rather than image matching.

## 7. What exactly is the copier-detection path?

Known:

Developer-confirmed anti-piracy behavior depended on cartridge/copy-device differences.

Smallest useful test:

Use static comparison and runtime traces around known mapping/SRAM/cart-sensitive accesses, informed by historical emulator issues.

Payoff:

Prevents accidental removal or misclassification of intentional low-level behavior.

## 8. What did USJO know that the 2014 bot does not?

Known:

The 2014 realtime bot is recovered. USJO v13 remains missing and used savestate search for stunt optimization.

Smallest useful test:

Continue targeted archival recovery of `usjo13.lua` and descendants, but do not block engineering work on it.

Payoff:

Potential stunt evaluator, search logic, timing rules and additional memory semantics.
