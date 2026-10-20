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

## 3. What prevents a first independently accepted complete USA event?

**Confirmed:** The recovered bot, historical SMV and shared native/`snesref` race-entry route already exist. Both guests have reached scored Zoo, Bowl and Dragster results. The old question about merely reaching a native race is settled; see [autonomous play and input](autonomous-play-and-input.md).

**Unknown/conflict:** The best Zoo witness still has nonzero unmasked stack/sound WRAM differences at sampled frames. Genuine original/native post-NMI source phases and the first persistent consumed divergence remain unclosed. A scored result and same relative next-event entry are insufficient to certify continuous course equivalence.

**Smallest useful test:** Use one source-and-binary-qualified Zoo case to compare the actual first causally relevant post-NMI read/write, original fetched PC, native executed marker and unchanged input stream; independently reopen retained raw guest memory. Keep original movie, fresh original and native clock origins distinct.

**Payoff:** Separates a harmless transient from a gameplay-affecting divergence and gives independent QA a falsifiable first-event acceptance candidate. [QA01 evidence authority](../QA01-INDEPENDENT-FIRST-USA-EVENT-ACCEPTANCE-20261018.md) owns detailed obligations and release adjudication.

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

## 8. Which USJO v13-specific behavior remains unrecovered?

**Confirmed:** The 2014 real-time Tabletop bot is preserved, and the recovered Dessyreqt workspace already contains USJO v14, v14a, a backup and a test sibling. V14 adds 16-bit boost reads; v14a has a more elaborate stunt-search and delayed HUD/message-credit evaluator. Exact v13 bytes remain unavailable.

**Unknown:** Whether v13 contained a distinct optimization rule absent from the recovered later versions. Missing a numbered intermediate version is not evidence that its capabilities are lost.

**Smallest useful test:** Compare pinned recovered v14/v14a source and available v8 against specific historical v13 claims; search for v13 only if a behavior or provenance question remains unresolved.

**Payoff:** Avoids redundant archival hunts while preserving a precise target for genuinely missing stunt-search behavior. See [autonomous play and input](autonomous-play-and-input.md).
