# Regional Presentation Switch

Status: planned Windows x64 Modern-product feature.

This document owns the regional-presentation feature that lets the shipped game present itself as either the North American **Uniracers** release or the European **Unirally** release without introducing a second authoritative gameplay ruleset.

## Product intent

The feature is an easter egg, not a settings-menu item and not a separate PAL gameplay mode.

At the stock title-family surface:

- retained title-transition evidence identifies `7E:009F == 0x84` as the title-family state and `0xD7` as the navigable main menu;
- secret recognition is admitted on `0x84`, not `0xD7`, so controller Left/Right/A inputs cannot steal ordinary main-menu navigation;
- typing `PAL` on a keyboard selects the European presentation profile;
- typing `NTSC` selects the North American presentation profile;
- controller-only users use:
  - **PAL / Unirally:** Left, Left, Left, L, A;
  - **NTSC / Uniracers:** Right, Right, Right, R, A.
- input is interpreted semantically through the host control layer, not through hard-coded SDL scancodes or controller device codes;
- the matcher is active only on the accepted idle top-level title surface;
- partial sequences time out and reset;
- unrelated input fails closed and ordinary title navigation remains authoritative;
- selecting the already-active profile is a no-op;
- successful switching is intentionally understated: no explanatory toast, settings row, achievement or menu disclosure is required.

The sequence is short enough to be practical on a controller, asymmetric enough to remember, and unlikely to occur accidentally during normal title navigation.

## Non-goals

This feature does **not**:

- switch the authoritative simulation from NTSC cadence to PAL cadence;
- reproduce historical 50 Hz slowdown;
- change physics, collision, AI, RNG, stunt scoring, race timing, progression, SRAM structure or replay semantics;
- boot a second Europe-retail executable/runtime;
- reinterpret profile identity, records or completed-run provenance;
- expose a general regionalization framework before evidence requires one;
- change Authentic-mode reference behavior.

The authoritative gameplay guest remains the canonical USA retail-derived runtime. The feature is a host-owned regional **presentation** profile.

## Verified retail identities

The project corpus contains both retail ROMs:

| Release | File | CRC32 | SHA-1 | Header title | Region |
| --- | --- | --- | --- | --- | --- |
| USA retail | `reference/roms/retail/Uniracers_USA.sfc` | `383858c7` | `cb249cf7301bdd985e6fe4bc4c942bf4f86d7d83` | `UNIRACERS` | `0x01` |
| Europe retail | `reference/roms/retail/Unirally_Europe.sfc` | `d8583ed7` | `d39ec113ef153ec9b7bacf12ed4a47f1a6d63a06` | `UNIRALLY` | `0x02` |

Both are 2 MiB and use reset vector `$8858`.

## What is already known

The regional releases are not binary-identical, but most of the player-visible content is shared.

Established project facts:

- USA retail vs Europe retail differs in 505,912 bytes across 26,390 contiguous diff runs.
- Both contain 45 valid RNC Method-1 course streams.
- 38 of 45 course streams are byte-identical by content.
- Seven course payloads differ:
  1. Switcher
  2. Last One
  3. Jumpover
  4. Down+Up
  5. Highroad
  6. Hairpin Hill
  7. Vertical
- Down+Up and Vertical each append resource `0x22` in Europe retail.
- Switcher changes one promoted header coordinate from `(99,26)` to `(99,22)`.
- The remaining changed streams retain their high-level resource lists and therefore contain lower-level course-local edits rather than wholesale resource-family substitution.
- PAL/NTSC timing and checkpoint code genuinely differ, and historical PAL/NTSC records are not directly comparable.
- core stunt weight tables and the recovered trick-praise table are conserved in the current comparative census.
- no evidence currently supports PAL-only tours, racers, modes or a broadly different frontend architecture.
- public and local evidence both establish distinct Uniracers versus Unirally title branding.

These facts justify a presentation profile while explicitly warning against assuming the two ROMs are content-identical.

## Presentation-profile contract

Introduce a semantic regional presentation state with two values:

- `RegionalPresentation::NorthAmerica`
- `RegionalPresentation::Europe`

Do not name the internal state `PalMode` or `NtscMode`; those names imply timing/simulation behavior that this feature deliberately does not own.

The state may control only evidence-backed presentation differences.

Expected first consumers:

1. title/logo artwork;
2. any other startup/frontend occurrence of the product name;
3. regional legal/copyright/startup presentation if direct capture proves a difference;
4. regional title animation/layout adjustments required by the alternate logo;
5. later, any course-local visual-only regional delta proven safe to reproduce without changing gameplay topology.

The profile must not become an implicit permission to fork arbitrary UI, gameplay or data.

## Switch transition design

A successful regional secret should not hard-cut the title branding if the original frontend already provides a suitable transition language. The preferred product behavior is to make the switch feel like a hidden stock frontend destination rather than a modern settings toggle.

Current design order:

1. **Prefer an original Uniracers frontend/title transition primitive.** The leading candidate is the stock horizontal menu/title movement already used by the frontend. Reuse its timing, easing, palette behavior and compositing characteristics as literally as practical.
2. **Direction follows the secret.**
   - `PAL` / Left Left Left L A should move the current North American presentation **leftward** and reveal Europe / Unirally from the opposite side.
   - `NTSC` / Right Right Right R A should move the current European presentation **rightward** and reveal North America / Uniracers from the opposite side.
   This makes the input sequence and visual response share one spatial grammar.
3. If the matched title-transition evidence shows that the original title-to-menu animation is a better fit than the horizontal menu movement, prefer that exact stock transition instead.
4. If neither stock transition is safe to replay in isolation, use the smallest faithful fallback already present in the game, such as a brief palette fade. Do not invent a custom modern wipe while an original transition is available.

The regional state change itself remains host-owned presentation state. The animation must not reboot or replace the authoritative guest runtime merely to create a visual effect.

### Transition evidence experiment

Extend the matched USA/Europe title comparison to retain enough consecutive frames to characterize the stock transition itself rather than only endpoint screenshots.

At minimum, capture:

- the title-family state around frames 300, 360 and 420;
- the transition into first main-menu presentation;
- settled main menu;
- any ordinary left/right frontend transition that demonstrably scrolls one menu surface into another.

For each candidate transition, record:

- source and destination guest/frontend states;
- duration in guest frames and presented frames;
- horizontal/vertical displacement per frame;
- whether the transition is tilemap/camera movement, palette fade, layer enable/disable, sprite animation or a combination;
- easing/step pattern;
- whether audio continues uninterrupted;
- whether guest input is suppressed during the transition;
- whether replaying the visual primitive can remain presentation-only;
- whether the same primitive exists identically in both retail regions.

Acceptance criterion: choose the most recognizably stock transition that can be driven by regional presentation state without changing simulation, progression or guest timing. The selected transition must have a deterministic test/retained frame sequence before shipping.

## Persistence policy

Default to **NorthAmerica / Uniracers** on first launch.

The regional presentation selection is host-owned global product state, not profile progression and not guest SRAM. On every platform build with a supported durable host-storage mechanism, the selected regional presentation **must persist across clean game shutdown and a later relaunch**. A player who discovers and selects Unirally should therefore continue to see Unirally on the next launch until they enter the NTSC code, and vice versa.

Persistence is platform-capability-aware rather than desktop-specific:

- desktop builds should use the established durable host-state store;
- console/mobile/web or future ports should use the platform adapter's normal durable product-state mechanism when one exists;
- a platform that genuinely has no durable writable host storage may fall back to session-only regional state without blocking the feature;
- transient storage failure must not mutate guest state or invent a different gameplay identity.

The setting is global to the installation/user product state, not per Modern profile. Changing racer/profile must not change regional presentation.

Acceptance requirements:

- switching does not mutate guest SRAM;
- switching does not change run-record identity or PB comparability;
- on persistence-capable builds, switching survives a clean shutdown and fresh process;
- a fresh installation/no stored value defaults to NorthAmerica;
- Authentic mode ignores the Modern regional-presentation setting even when it is durably stored;
- malformed/unknown persisted values fail safely to NorthAmerica;
- persistence failure leaves the currently running presentation well-defined and does not grant any guest authority.

The hidden nature of the easter egg is not a reason to avoid persistence. Config-file discoverability is secondary to preserving the user's chosen regional identity.

## Secret-input contract

### Keyboard

At the accepted idle title surface, consume ordinary text input into a tiny rolling matcher.

- `PAL` -> Europe / Unirally
- `NTSC` -> NorthAmerica / Uniracers

Requirements:

- case-insensitive;
- text-entry semantics, not physical-key positions;
- matcher resets after a short inactivity timeout;
- matcher resets on leaving the accepted title surface;
- typing characters while another product text-entry modal is active must not feed this matcher.

### Controller

At the same title surface:

- Left, Left, Left, L, A -> Europe / Unirally
- Right, Right, Right, R, A -> NorthAmerica / Uniracers

Requirements:

- use semantic SNES/product inputs after host mapping;
- require ordered press edges rather than held-state snapshots;
- use the same inactivity timeout/reset policy as keyboard;
- ordinary title navigation must not be delayed waiting for a possible secret;
- sequence recognition must be observational until the final input commits a switch;
- gamepad family is irrelevant: Xbox/PlayStation/Switch/other adapters map into the same semantic L/R/A/directional actions.

## Required experiments before presentation scope is frozen

The project already has enough comparative tooling that open questions should be closed by narrow deterministic experiments rather than broad archaeology.

### Experiment A: complete frontend framebuffer diff

Purpose: identify every player-visible USA/Europe retail presentation difference outside races.

Run both verified retail ROMs in the same trustworthy reference-emulator pipeline and capture matched checkpoints for:

- boot/legal screens;
- logo/title entry and settled title;
- attract/demo transitions where practical;
- top-level menu;
- one-player mode entry;
- two-player mode entry;
- VS entry;
- League entry;
- Options;
- racer/name selection;
- tour/track selection;
- representative race, circuit and stunt results;
- Records/high-score surfaces;
- ending/award surfaces reachable with existing deterministic fixtures.

Normalize only emulator-output framing needed for image comparison. Do not normalize away actual PAL art/layout differences.

For each matched checkpoint retain:

- raw screenshots;
- exact ROM identity;
- emulator/core identity;
- frame/tick used for capture;
- pixel-diff summary;
- bounding boxes of changed regions;
- classification: branding / text / legal / layout / animation / unexplained.

Stop rule: every visible frontend difference becomes either a named presentation-profile consumer or a documented intentional exclusion.

### Experiment B: title-logo asset extraction/provenance

Purpose: recover the exact Europe-retail Unirally title art and identify whether the logo requires distinct palette/layout/animation data.

Tasks:

- locate/decode the USA and Europe title-logo source data;
- establish exact source ranges or extraction recipe;
- compare palette, tile/bitmap composition, dimensions and positioning;
- determine whether the animation code/path is shared with different data or region-specific;
- produce retained lossless reference images for HD remaster work;
- record provenance/hash binding so future HD work cannot accidentally derive Unirally from a hand-redrawn approximation.

Acceptance: the future renderer can choose either regional logo through one semantic asset family without duplicating unrelated title-screen work.

### Experiment C: seven changed-course visual/topology diff

Purpose: decide whether any Europe-retail course differences belong in the presentation profile.

Only these courses need positive investigation because the other 38 RNC payloads are byte-identical by content:

| # | Course | Known delta |
| ---: | --- | --- |
| 4 | Switcher | changed payload; one header coordinate differs |
| 16 | Last One | +64 decoded bytes |
| 20 | Jumpover | +64 decoded bytes |
| 26 | Down+Up | +321 decoded bytes; resource `0x22` appended |
| 27 | Highroad | +192 decoded bytes |
| 35 | Hairpin Hill | +64 decoded bytes |
| 36 | Vertical | +161 decoded bytes; resource `0x22` appended |

For each course:

1. decode USA and Europe payloads;
2. produce structural diffs of headers, coarse/fine layout records and resource-local data;
3. capture matched in-game viewpoints or produce a trustworthy static course visualization;
4. classify each difference as:
   - visual-only;
   - collision/topology affecting;
   - spawn/progression affecting;
   - timing/region adaptation;
   - unknown.
5. determine the semantics of resource `0x22` sufficiently to classify the Down+Up/Vertical additions.

Decision rule:

- visual-only differences may be candidates for `RegionalPresentation::Europe`;
- anything that changes collision, route topology, race semantics, spawn authority, timing, AI interaction or records remains canonical-USA behavior in Modern;
- uncertain differences remain excluded until proven presentation-only.

### Experiment D: audio/SPC regional comparison

Purpose: close the question of whether regional presentation requires any audio asset switch.

Compare the retail ROMs for:

- SPC driver/program identity where recoverable;
- music sequence/sample data;
- title/menu cues;
- sound-effect data;
- track ordering/selection tables.

Where static identity is unclear, capture deterministic audio from matched title/menu/race scenes and compare after accounting only for host PAL/NTSC pacing.

Expected result is shared content; evidence, not expectation, closes the task.

Decision rule: do not create a regional audio branch unless a content difference is proven.

### Experiment E: text and legal-string inventory

Purpose: find region-specific user-visible strings without assuming every binary string delta is rendered.

Tasks:

- extract candidate frontend/boot text from both retail ROMs;
- align string/table candidates;
- cross-reference each difference against framebuffer captures;
- classify cartridge-header/internal identifiers separately from rendered presentation;
- retain only rendered or otherwise player-visible differences as implementation requirements.

### Experiment F: secret-input collision test

Purpose: ensure the controller codes cannot reasonably trigger during normal title use.

Replay representative title/frontend input traces and prove:

- neither sequence occurs accidentally;
- partial sequence tracking never swallows or delays ordinary navigation;
- timeout/reset behavior is deterministic;
- switching is impossible during races/results/text-entry modals/Authentic mode;
- mapped controller types produce identical semantic sequences.

## Current implementation status

The policy-only phase has advanced into a tested product substrate on this branch:

- `native/product/regional_presentation.hpp` owns the shared semantic `RegionalPresentation` type;
- `regional_presentation_secret.{hpp,cpp}` implements the pure keyboard/controller recognizer with title-surface, Modern-mode, text-entry and timeout gating;
- `regional_presentation_runtime.{hpp,cpp}` initializes recognition from host state and changes only `HostProductState::regional_presentation`, returning `SaveRequired` only for a real regional transition;
- `regional_presentation_input_policy.hpp` binds admission to the proven `0x84` title-family state, keeps `0xD7` main-menu navigation guest-owned, and provides SDL-free keyboard-letter admission;
- host-state schema v6 accepts `regional_presentation=north_america|europe` as a known additive field, so older/sparse v6 files default safely to NorthAmerica and canonical re-save writes the explicit value;
- host-state/store tests cover Europe serialization/round-trip; standalone regional tests cover PAL/NTSC text, both controller codes, repeated-selection no-op, timeout, wrong-prefix recovery, Authentic/text-entry/off-title rejection and persisted-state initialization;
- store-level acceptance now proves PAL -> durable save -> fresh load -> profile switch -> NTSC -> durable save -> fresh load, establishing global/profile-independent persistence;
- `tools/analyze_regional_retail_static.py` independently verifies the exact retail identities, 38/45 RNC identity, all seven changed stream ordinals, course mapping, promoted resource/header deltas and candidate printable-string differences;
- `regional-retail-static-analysis.yml` retains that exact static inventory as JSON/Markdown evidence;
- `tools/compare_retail_frontend.py` plus `regional-retail-frontend-comparison.yml` now run the same semantic snesref UI routes against both retail ROMs and retain matched framebuffer/text differences plus route failures for interpretation; the route now includes title checkpoints at frames 300/360/420 plus first/settled main menu;
- `tools/compare_regional_audio_packages.py` plus `regional-retail-audio-packages.yml` compare the known 50-block ROM-side APU package pool independently of potentially relocated PAL selector tables;
- `tools/compare_regional_course_payloads.py` plus `regional-retail-course-payloads.yml` decode the seven changed RNC streams and localize byte changes into header, coarse table, fine-record region, resource list and post-list payload without over-classifying their semantics;
- the generated-product CMake patch now links the regional secret/runtime sources, so the feature is part of the shipping native product build rather than unit-test-only code.

Still intentionally unwired:

- platform event translation into the semantic matcher;
- thin production-host binding of the already-proven `0x84` title admission policy;
- save dispatch after `SaveRequired`;
- title/logo rendering selection;
- production consumption of the evidence experiments below.

Experiment A/E now have reusable execution machinery; the next step is to inspect retained outputs, classify visible deltas, and promote only confirmed presentation differences.

This keeps the active shared Modern host out of this PR until the current navigation/progression/controls branches are reconciled.

## Implementation phases

### Phase 0: evidence closure

Run Experiments A-E and update this document's presentation-difference inventory.

Do not implement speculative regional consumers before the relevant evidence is classified.

### Phase 1: pure regional state + secret recognizer

Add:

- typed `RegionalPresentation`;
- pure keyboard rolling matcher;
- pure controller sequence matcher;
- title-surface/reset/timeout policy;
- unit tests for success, timeout, wrong-order, partial-overlap, repeated selection and surface exit.

No rendering change is required in this phase.

### Phase 2: exact title branding switch

Bind the regional state to the proven title/logo presentation seam.

Requirements:

- NorthAmerica remains pixel/reference-compatible with current title behavior before HD substitution;
- Europe uses exact extracted Unirally source art or its provenance-bound approved HD derivative;
- no race simulation state changes;
- switch can occur from the title without process restart if the title presentation seam supports clean invalidation/rebuild;
- if a clean live swap is unsafe, restart only the frontend/title presentation state, never the authoritative cartridge runtime.

### Phase 3: remaining proven frontend deltas

Implement only the differences established by Experiment A/E.

Each consumer must be explicitly named and independently testable.

### Phase 4: optional course-local visual deltas

Only if Experiment C proves specific differences are presentation-only.

Do not bundle this with the initial title-logo feature.

## Validation

Minimum shipping acceptance:

- keyboard `PAL` switches Uniracers presentation to Unirally;
- keyboard `NTSC` switches back;
- Left Left Left L A and Right Right Right R A perform the same semantic transitions;
- no accidental switch on representative ordinary frontend traces;
- NorthAmerica presentation remains the default;
- all guest race-state and persistence checks remain identical across regional presentation choice;
- completed-run records/PBs remain comparable and do not acquire a false PAL gameplay identity;
- Authentic mode remains inert;
- title branding is provenance-bound to the verified retail assets;
- every additional regional consumer is backed by a retained experiment artifact.

## Planning rule

This workstream is secondary to correctness blockers for the Windows x64 product but is a legitimate primary-platform polish feature. It should be scheduled as a bounded independent lane when it does not contend with active Modern-host hotspots.

Do not expand it into full PAL-runtime support unless a future product decision explicitly changes the goal.
