# Uniracers Modern Port Plan

Last updated: 2026-10-03

This is the canonical product-development plan for turning the original SNES Uniracers / Unirally into a faithful modern native port.

For current reverse-engineering priorities, evidence collection and archival work, see `RESOURCE-COLLECTION-AND-DEV-RESEARCH-PLAN.md`. For day-to-day milestone status, see `WORK-QUEUE.md`. Remaining global tooling-audit work is bounded by `TOOLING-AUDIT-CLOSEOUT.md`; experiments transferred from that audit are owned by the relevant phases below. This document owns the longer path from stock native execution to the intended modern port.

## Terminology

The project as a whole is the **UR-Recomp project**, **Uniracers modern port**, or simply **the project**. Do not use `widescreen` or `HD` as shorthand names for the project, its overall architecture, or its end state.

**Widescreen** means the specific feature that expands the logical horizontal view beyond the original 4:3 presentation.

**HD Presentation** means the specific feature that substitutes or renders higher-resolution visual assets/presentation while preserving authoritative game state.

Use those terms only when discussing those features or their implementation. Other work should be named for what it actually is: native execution, fidelity validation, reverse engineering, course decoding, asset extraction, tooling, audio modernization, custom courses, and so on.

## Platform target policy

The modern product is one authoritative recompiled game with multiple host implementations. **Windows x64 is the primary consumer/reference packaging target.** Planned peer/feasibility targets are modern macOS, a best-effort macOS 10.13 High Sierra legacy lane, WebAssembly/browser execution, Nintendo Switch homebrew, and a PlayStation 5 personal-use host port when lawful tooling is available.

These are host targets, not separate gameplay rewrites. Platform-specific lifecycle, filesystem, graphics, audio, controller and packaging code must stay outside authoritative simulation, progression/SRAM semantics, Widescreen materialization, HD semantic replacement selection and modern product-state schemas. Linux may remain an engineering/CI host without becoming the product-definition target.

Console builds are private personal-use feasibility targets, not commercial/storefront deliverables. Do not commit proprietary SDK material, confidential platform documentation, keys or device-unique secrets. The canonical matrix and portability rules live in `PLATFORM-TARGETS.md`; Switch-specific planning lives in `SWITCH-HOMEBREW-PORT.md`.

## Product definition

The target is **Uniracers itself**, not a mechanically similar recreation.

The original game simulation remains authoritative for:

- physics;
- collision and track contact;
- player and opponent race state;
- stunt recognition;
- acceleration, boost and braking;
- RNG;
- in-race rules and timing;
- AI;
- course semantics.

The project must also preserve the original frontend, progression, save behavior, indicators and administrative flows well enough to reproduce them in an authentic/reference mode. That requirement does **not** make every cartridge-era frontend or persistence convention mandatory in the modern product layer.

The modern port may deliberately replace or extend presentation, input plumbing, display aspect, windowing, asset resolution, UI composition, player/profile management, campaign/progression UX and optional audio presentation, provided that:

- stock behavior remains reproducible in the authentic/reference path;
- modernized frontend/progression policy does not silently alter authoritative race simulation;
- an original audiovisual indicator is not removed merely because a clearer modern indicator exists;
- recognizable original menu presentation and interaction character are preserved even when choices are reorganized, removed or added;
- any deliberate behavioral change is documented as product policy rather than mistaken for a fidelity fix.

### Modernization and subtraction policy

Modernization begins with subtraction, not feature accumulation. Before adding a new system, classify the original feature being touched as one of:

1. **Presentation artifact:** preserve it by default. Original indicators, animations, icons, result rituals, menu visual grammar, sounds and other player-visible communication remain part of the fidelity target. Additional labels, numbers, deltas, tooltips, overlays or expanded views may elaborate on them; they should not casually replace them.
2. **Gameplay mechanic:** preserve it unless there is a specific, evidence-backed product decision to change it. Mechanics that appear strange should be tested against expert/high-level play before being called obsolete.
3. **Administrative or hardware-era system:** eligible for redesign or removal in the modern product layer when its main purpose came from shared-cartridge saves, limited storage, 1994 menu conventions, content-padding repetition or other platform constraints. Preserve an authentic/reference implementation where needed for fidelity.

Apply this rule especially to the frontend:

- retain the overall Uniracers menu look, motion, typography, color language, sounds and recognizable screen character;
- allow menu choices, grouping and navigation depth to change when doing so removes obsolete administration or exposes modern features;
- keep original result/score indicators even when clearer modern data is shown alongside them;
- treat manual-dependent opacity in basic controls or status as friction to explain, while preserving genuine secrets, advanced discoveries and game-world mystery.

### Racer identity and legacy cast

The original named/color-coded unicycles must be preserved as recognizable legacy content, but the modern product should not require a racer choice to double as a save slot.

Plan for a modern racer/profile model in which:

- player-created names are accepted even when they match the original forbidden-name list; instead of rejection, trigger a special **"COOL NAME!"** acknowledgement and then continue normally with the chosen name;
- players can create and name their own racer independently of save/profile storage;
- body color and any later-supported cosmetic dimensions are chosen independently;
- every original named/color combination is available as a faithful preset;
- original racers may also appear as AI opponents, ghosts, tournament entrants or other appropriate legacy cast roles;
- Bronsen, Silverton and Goldwyn remain preserved as named opponents even if Bronze/Silver/Gold progression is redesigned.

The exact customization surface should wait for Phase E asset/animation understanding so cosmetic freedom does not accidentally invalidate sprite-state fidelity.

### Progression and frontend candidates for deliberate simplification

The modern product layer should evaluate, rather than automatically inherit:

- unicycles as save/profile slots;
- persistent multi-league/player-management bureaucracy;
- mandatory repeat clears of the same tour for Bronze, Silver and Gold tiers;
- loss of unfinished tour/session progress where no gameplay purpose depends on it;
- destructive/administrative controller chords;
- the original forbidden-name rejection behavior, while preserving its detection list as an Easter-egg trigger for the modern **"COOL NAME!"** acknowledgement;
- redundant score/record menu silos;
- menu states that exist only to compensate for storage or controller-era constraints.

Where these systems have recognizable presentation, preserve that presentation language or expose an authentic mode rather than deleting the historical evidence wholesale. The target is a cleaner route into Uniracers, not a generic replacement frontend.

### Modern baseline features

The following are **must-do modern product requirements** unless later technical evidence shows that a specific item is impractical or conflicts with fidelity. They should be treated as baseline product competence rather than speculative feature creep:

- full modern controller support, hot-plugging and rebinding;
- keyboard input where practical;
- independent modern profiles, racer identity and settings;
- robust autosave plus resumable progression;
- instant restart/retry from gameplay, pause and results where appropriate;
- a modern pause menu with resume, restart, options, controls/run data and exit choices;
- personal-best and previous-run ghosts;
- local ghost management and replayable run records without any network dependency;
- exact timing, lap/split data, personal-best deltas and target/medal deltas shown in addition to original indicators;
- a coherent records/statistics browser that preserves classic score/result presentations as views;
- a practice/free-play route with rapid track selection and repeated attempts;
- a concise in-game onboarding/tutorial path for fundamental controls and the stunt-to-speed relationship;
- accessibility-oriented presentation/input options where they can be implemented without changing authoritative simulation, including remapping, vibration control, readable text support, reduced flashing and similar host-layer accommodations;
- fast local multiplayer setup, rematch and track rotation without requiring legacy League administration;
- native widescreen, modern resolutions including 4K, arbitrary-window support and authentic 4:3 fallback;
- display geometry/pixel aspect and logical view width must remain separate product axes as defined in `DISPLAY-PRESENTATION-POLICY.md`: Authentic 4:3 uses the validated historical display transform, Raw Pixels preserves literal square source pixels, and modern Remastered/Reimagined presentation uses square host-pixel geometry while view width is selected independently;
- user-configurable video output settings including automatic/native-display resolution, common explicit resolutions, windowed/borderless/fullscreen modes, VSync, presentation refresh/FPS targets, and internal render scale where the active graphics mode benefits from it;
- presentation refresh/FPS settings must never alter authoritative guest simulation cadence, physics, timers, AI, RNG, animation-state selection, input semantics or records; higher-refresh presentation must use host-side frame pacing, repeated presentation frames and/or presentation-only interpolation as appropriate;
- three first-class graphics modes backed by swappable presentation assets: **Original** (literal/authentic SNES artwork), **Remastered** (faithful high-resolution reconstruction that preserves the original art decisions while removing low-resolution pixel-grid limitations), and **Reimagined** (new modern artwork closely derived from the original design language); optional CRT/NTSC-style presentation may sit on top of Original where useful;
- fast navigation conveniences such as recent track, rematch, next event and direct practice access;
- localization-ready text/UI architecture even if only one language is initially shipped;
- preservation of attract/demo behavior, with room for a modern showcase/demo presentation using recorded local runs;
- architecture that does not unnecessarily prevent custom courses, local challenge packs, visual packs or other data-driven extensions later.

These requirements should be implemented at the layer that owns them. Do not move timing, ghost, replay, menu or accessibility concerns into the original simulation when host/runtime policy can provide them cleanly.

The first project-owned modern product seam is defined in `MODERN-PRODUCT-LAYER.md`: host profile selection and typed host settings live in an isolated, versioned host-state envelope with an explicit Authentic/Modern policy switch. Authentic mode grants no host-profile, host-setting or modern-command authority. The envelope deliberately contains no WRAM/SRAM, racer-slot, medal, course or simulation state; future pause/restart, autosave, records, ghosts and racer identity should attach through narrow host/runtime interfaces rather than expanding cartridge-era save semantics. Pause is bound to the existing host frame gate. Restart Race has the deterministic native substrate and the first real modern-product command integration: `ModernSessionRuntime` carries the typed request through the runtime adapter into the lifecycle-owned rollback anchor, owns the rewind-audio timing lock while Retry is valid, reconciles live audio presentation after restore, and exposes a narrow C ABI for generated-host and later UI wiring. One important persistence boundary is explicit: SNESRecomp rollback snapshots include cartridge SRAM, so the Uniracers binding preserves the current 8 KiB SRAM across Retry instead of reverting progression or records to the race-entry image. Title policy exposes Retry only in active race and established results surfaces. The ordinary native product host now exposes root Resume, conditional Restart, Options, Controls, read-only Run Data and confirmed Quit Desktop. Options owns persisted Focus Pause, desktop Display Mode and VSync through one keyboard/controller-parity subview. Native run `37148646286` proves Focus Pause, Windowed → Borderless Fullscreen and VSync On → Adaptive through the generated host, schema-v3 save/reload, fresh-process application and Authentic-mode inertness. Display mode and VSync remain host presentation policy only; neither changes authoritative guest cadence, timers, physics, AI, RNG, animation-state selection, progression, records or SRAM. Presentation refresh/FPS targets remain a separate pacing follow-on. Controls, Run Data and Quit keep their prior root positions and acceptance. Restart run `37148647371` remains green through repeated replay and results-screen SRAM preservation. Authentic mode remains a stock-policy escape hatch and does not apply modern administrative state. Profiles, autosave/resume, richer run statistics/splits, additional proven settings and a true Exit-to-Frontend implementation remain separate follow-ons.

### Decide when the relevant subsystem is mature

The following are desirable but should be evaluated when the underlying state model, renderer, frontend or course model is sufficiently understood. Do not force them early:

- expanded racer cosmetics beyond name/color and exact legacy presets;
- full replay viewer with scrubbing, frame stepping, camera controls or HUD hiding;
- photo/capture tools;
- richer statistics such as stunt histories, heatmaps, streaks or aggregate telemetry;
- achievements/challenges designed around mastery, secrets and unusual clean runs rather than grind;
- section/checkpoint-based practice starts, if the course/state model can support them without corrupting normal simulation semantics;
- a simplified local tournament/bracket mode replacing most legacy League administration;
- modern medal/progression policy such as awarding the highest achieved tier immediately or making challenge tier selectable;
- a modernized attract/demo reel sourced from especially strong local runs;
- user-facing mod/content-pack affordances beyond the already planned custom-course tooling.

A later decision may promote any of these to must-do once implementation cost and fidelity impact are understood.

### Network and hosted-service policy

The project has no planned infrastructure for hosted services and no practical environment for testing production online features. Therefore:

- **do not spend implementation time on online multiplayer, matchmaking, global/friend leaderboards, downloadable ghosts, cloud challenge services, daily/weekly events, accounts or any hosted backend;**
- **do not add CI, credentials, service deployment or test infrastructure for them;**
- keep local data models and APIs clean enough that a future contributor could add network transport or hosted services without redesigning core simulation, ghost, replay, timing, leaderboard or challenge data;
- where a feature has both local and online forms, implement the useful local form only unless the infrastructure situation changes.

This is a deliberate "leave the door open" posture, not a deferred delivery commitment.

The end-state should support:

- native desktop execution;
- authentic 4:3 presentation as a permanent regression/reference mode;
- the **Widescreen** feature, providing true additional horizontal view rather than stretched 4:3;
- modern window sizes including 4K output;
- a three-tier graphics system: original SNES art, faithful high-resolution remaster art, and closely derived modern reinterpretation art, all preserving authoritative animation/state timing and selectable without changing simulation;
- original courses and simulation behavior;
- deterministic validation against the original ROM;
- eventual documented course tooling and custom courses;
- a public-release path that does not require distributing proprietary ROM bytes.

## Architecture decision

The default architecture is:

```
original ROM
    |
    v
SNESRecomp analyzer + generated native 65816 code
    |
    v
authoritative original simulation / SNES state
    |
    +------------------------------+
    |                              |
    v                              v
authentic PPU path          enhancement policy
4:3 oracle                  game-state / symbols
    |                              |
    |                        +-----+------+
    |                        |            |
    v                        v            v
stock framebuffer      true-wide PPU   overlay extraction
                       rendering       / HD Presentation
                            |            |
                            +-----+------+
                                  |
                                  v
                           modern host compositor
                                  |
                                  v
                         4:3 / 16:9 / 4K output
```

A separate gameplay rewrite in Godot, Unity or another engine is **not** the primary plan. It would create a second simulation that must independently reproduce every quirk already present in the executable original. A separate renderer or editor may eventually use decoded project data, but the shipping simulation should remain the recompiled game unless evidence shows that approach cannot meet the presentation goals.

Generated C is disposable implementation output. Durable game-specific knowledge belongs in:

- analysis configuration;
- runtime/host integration;
- enhancement hooks;
- symbols;
- parsers;
- asset manifests;
- deterministic tests;
- compact evidence reports.

### Consolidated knowledge/query layer

The project now has a normalized cross-domain query surface under `analysis/data/`. Treat it as the default starting point for planning and reverse-engineering decisions, while retaining the underlying generated/runtime/historical artifacts as provenance-bearing evidence.

Canonical query surfaces are:

- `course-corpus.json` for the reconciled 45-course identity, geometry, header, landmark and resource-list view;
- `course-resource-catalog.json` for promoted resource semantics, conserved resource bundles and regional resource-selection deltas;
- `state-schema.json` for promoted RAM/SRAM semantics, paired-racer relations, regional motion clusters and historical/reconciled state leads;
- `code-semantics.json` for named functions joined to structural/cross-build correspondence;
- `presentation-assets.json` for exact semantic presentation families and derived record constraints;
- `progression-model.json` for medal/tier/checksum semantics and predictive acceptance rules;
- `fixture-corpus.json` for deterministic fixture ownership and semantic/event-relative anchoring;
- `evidence-claims.json` for selective atomic cross-source claims.

Planning rule: query these surfaces and `analysis/generated/inference-audit*.{json,md}` before commissioning a new trace, structural island, course sweep or historical-source reconciliation. If a required relationship is scattered but repeatedly useful, extend the consolidation builder instead of adding another parallel ledger.

## What the project already has

The plan begins from a much stronger baseline than a normal blind SNES port.

### Native execution

The canonical USA ROM already builds through the pinned SNESRecomp stack and reaches a visually verified stock Uniracers title screen in the actual generated executable.

The current smoke proves:

- the intended native executable is built, not a CMake helper;
- the canonical ROM loads;
- SNES initialization succeeds;
- SDL/X11 video initializes;
- audio initializes;
- the main loop runs;
- frames are simulated;
- a real presented frame can be captured;
- frame 300 has been visually identified as the coherent stock title screen.

Deterministic menu navigation and playable-race bring-up are complete. Broad first-divergence archaeology is no longer the active target: event-relative race fidelity is strong across the representative 1P/2P/VS matrix, and pre-race absolute-frame seams are treated as cadence/alignment leads unless semantically anchored state disagrees. The +8 presentation-phase seam is now causally closed for the current Widescreen decision. Meaningful P2 race state remains equal, but the stable host/frontend cadence shift changes the sampled class of six-state presentation/frontend counter `$7710B1` at `object-tail-141`. `83:EB3F..EB51` therefore initializes P2 presentation sequence 3 instead of 1; `82:8952/8956` writes frame `0x0A8D` instead of `0x0A45` through indexed P2 `$0DEB`, the ordinary marshal carries that through `$0F4F -> $0F97 -> $0FEB`, and `83:F0BB/F296/F2BB` stages the different presentation before VRAM first diverges at `object-tail-142`. OAM remains equal through the early gap, and the later two-pixel authentic-center regression at `168` is downstream. The first controlled +8 Widescreen strip-scheduling experiment is now accepted. Run `37066327707` uses the stock preparation machinery twice in a bounded diagnostic path to stage an adjacent future horizontal column into the secondary `$03xx` lane before NMI: 309 future-stock columns match exact later-stock payloads, adjacent VRAM geometry and post-NMI bytes, with a 14-frame consecutive acceptance run. Camera/gameplay state remains equal, and the separate liveness guardrail finds zero protected differences across 61 samples with the first progression event unchanged at frame 1225. That preparation mechanism is now implemented as the smallest live native hook. Final acceptance run `37081391730` reaches it through `83:CBCC -> 83:CD55 -> 81:A52B/A52F`, leaves margin 0 inert, and reuses stock `A59E/AB88`. All 617 same-camera primary→prepared transitions advance exactly one low-five-bit position on the 32-column VRAM ring. Their full 16-bit step shapes (`+1`, `-31`, or `+33` in the retained fixture) are also observed in stock, so the upper edge bits are compound resource/segment state rather than ring geometry. The run retains 317 exact later-stock payload matches with a 25-column consecutive exact-match run and preserves protected gameplay/camera/progression state. The stock guest preparation surface still stops at `secondary-lane-capacity`: one spare horizontal lane is enough for +8 but not the additional columns required by +16/+24. That no longer blocks the architecture. Run `37086273196` closes the next capacity seam by leaving the accepted +8 guest path unchanged for column +1 and carrying column +2 entirely in host/native presentation storage: 617/617 shadow columns are present, all 617 exactly match the nearest later-stock compound edge word plus 32-byte payload at the required next ring coordinate, cleanup is deterministic, and the liveness fixture shows no earlier gameplay activation. The proof provider was deliberately an independent later-stock oracle. Native workflow run `37094022986` now closes the production content seam: column +2 is generated directly from the live `7F:000F` coarse-sector table and `7F:800F` packed-surface fine records, with no future-stock input and no synthetic guest descriptor lane. All 617 host-shadow rows are produced with zero provider misses; 599/599 rows with a same effective fine-Y viewport match the independent stock control exactly, while the remaining 18 are explicitly classified vertical-view transitions. Cleanup and protected state remain equal, and the liveness fixture still reaches the identical `liveness-004` progression event one guest frame later, never earlier. Run `37146519813` closes the host materializer through +72: eight host-owned columns at the deepest margin, 4,936 retained host rows, 4,773/4,773 exact same-view matches, zero provider misses/unmatched rows, deterministic cleanup, zero protected-state differences, and identical named semantic progression events across +16/+24/+64/+72. The repeated -2 host-frame phase at already-accepted +16 proves the former ±1 cutoff was capture-phase sensitive; the gate now retains exact semantic/protected-state requirements with an explicit ±2 phase tolerance. Canonical validated capacity is +72. The +32 sweep also surfaced and fixed the stock inactive-vertical fallback (`camY >> 4`). The next Widescreen architecture step is no longer deeper strip materialization or review-tool construction. PR #302 / run `37142393303` generates explicit display-geometry candidates from canonical 256×224 menu/pre-race/race captures. The policy now records full-height 7:6 as the preferred provisional Authentic candidate because it maps the canonical raster exactly to 4:3 without cropping authored rows. Its exact 16:9 extension is +42⅔ source pixels per side; the provisional host-native viewport exposes the nearest symmetric integer +43 per side (342×224), while the strip-granular live-course provider prepares +48 per side and is independently validated through +72. Visible viewport extent and provider backing capacity are therefore separate contracts rather than one magic width. The remaining decision is to validate or reject that title-specific PAR/overscan candidate from retained/reference evidence and close the final output transform/composition while authoritative simulation, stock 4:3, and the accepted +8 guest path remain unchanged. Stock progression-changing save/load acceptance is now closed: run `37055966541` captured a gameplay-authored Crawler bronze (`0→1`), validated the model-predicted tier state and checksum, and reloaded the entire 8 KiB SRAM byte-for-byte in a fresh current reference process.

### Four-ROM differential corpus

The repository contains:

- USA retail;
- Europe retail;
- historical GoodSNES-listed `Uniracers (Beta)`;
- 1994-11-29 PAL prototype.

Important current observations:

- USA retail and the legacy beta differ in only 486 isolated byte positions;
- their 45 RNC streams are byte-identical;
- USA retail and the November PAL prototype also share the complete 45-stream RNC corpus;
- Europe retail changes seven decoded streams while preserving 38 byte-for-byte.

These builds are differential oracles for late fixes, regional behavior and executable/data boundaries.

Treat the four-build corpus as a **comparative code-analysis surface**, not merely a byte-diff archive. The project should build a normalized cross-build code atlas that can align routines and tables even when absolute addresses move. For every useful executable region, compare independent analyzer views rather than treating generated recompilation C as the sole reverse-engineering authority.

The comparative lane should:

- run the canonical USA build and the other three preserved builds through every analysis route that can produce useful structure: SNESRecomp manifest/generated code, snes2asm, bounded da65, and Ghidra/ghidra-snes where persistent cross-reference analysis earns its cost;
- add other genuinely independent 65816 control-flow analyzers only when they provide a distinct interpretation rather than duplicating an existing decoder;
- normalize results by SNES address, instruction fingerprint, control-flow shape, callers/callees, referenced ROM tables and WRAM/PPU accesses;
- align structurally corresponding routines across builds even when code has moved;
- flag analyzer disagreements in function boundaries, code-vs-data classification, M/X state, indirect targets, jump tables and cross-references as high-value investigation targets;
- use cross-build stability to distinguish source-level routines/tables from build-specific layout noise;
- propagate locally verified semantic labels from Nitrodon, Dessyreqt, TAS/RetroAchievements and dynamic traces across structurally matched builds, while retaining provenance and confidence;
- retain SNESRecomp's generated C as execution-oriented evidence, not as a claim that semantic decompilation is complete.

The goal is a machine-readable **Uniracers comparative code atlas**: one record per candidate routine/data object, correspondence across all preserved builds, analyzer interpretations, runtime execution evidence, known symbols/RAM effects and unresolved disagreements. The first implementation now exists in `tools/build_comparative_code_atlas.py`, with explicit gaps in `analysis/decompilation-gaps.json` and semantic coverage in `analysis/generated/decomp-gap-inventory.json`. Expand these artifacts before inventing parallel tracking systems.

### Course corpus

There are exactly 45 validated RNC Method 1 streams in each preserved build.

The repository owns an independent Method 1 decoder. All 180 stream decodes pass their packed and unpacked CRC16 checks.

Evidence now strongly supports one decoded payload per shipped track. The RNC storage order is explicitly reconciled as Crawler, Jumper, Shuffler, Bounder, Walker, Runner, Hopper, Sprinter, Hunter, which matches the SRAM progression-row order rather than the player-facing/manual tour ordering. Dessyreqt historical track IDs map exactly as `track_id = stream_index - 1`. Decoded byte 2 equals decimal 45 on exactly the nine third-position tracks in the nine five-track stream groups, matching the game's 45-second stunt events.

The shipped Rob Northen Method 1 unpacker has also been identified in ROM code:

- USA / legacy beta: `01:B8F1`;
- Europe retail: `01:B8E2`;
- PAL prototype: `01:B8D1`.

### Autonomous player source recovered

Dessyreqt's public 2014 **Uniracers Tabletop bot** source has been located at Pastebin ID `A0XpKw9v`, via TASVideos submission #4250. The submission states that the bot completes the game without savestate search and can be adjusted for a human to race against it. The script contains frontend navigation, course-specific driving regions and a large labeled RAM map. It should be treated as a major input/fidelity/reverse-engineering resource and adapted into the project's deterministic harness after its addresses are locally verified.

### Frontend/UI state model

The frontend should be treated as a state machine rather than a loose screenshot collection. The seed model lives in `analysis/ui-state-map.yml` with human guidance in `docs/UI-STATE-MAP.md`.

Use public screenshots and the original manual to bootstrap recognition and candidate controls, then promote important edges to local evidence with controller-only fixtures. Existing `dump <tag>` checkpoints already emit framebuffer BMPs plus machine state, so the same deterministic routes can serve UI archaeology, regression testing, future frontend/HD Presentation work, and symbol discovery without inventing a parallel capture system.

Prefer cheap visual/menu inference before code archaeology when the UI is self-explanatory; escalate to tracing/disassembly when timing, hidden conditions, visually identical states, or progression-sensitive behavior make observation ambiguous.

Treat atlas completion as tiered rather than absolute:

1. **Critical fidelity:** ordinary 1P flow, progression-relevant screens, pause, race setup/results, materially used Options/Records states, 2P/VS setup and split-screen behavior, and any frontend state that participates in a known emulator/compatibility seam or modern implementation decision. These must be understood well enough to implement and validate.
2. **Cheap completeness:** states or transitions that fall out from the manual, public screenshots, recovered bot, existing dumps, or a trivial deterministic probe. Harvest these when the marginal cost is small.
3. **Archaeological tail:** obsolete administrative minutiae, secret/destructive chords, exact blacklist behavior, transient tally substates, punctuation-editor edge cases, exact attract timing, and similar quirks with no implementation or validation consequence. Record existing evidence, but do not spend serious reverse-engineering effort closing these solely to make the atlas numerically complete.

A red atlas/gap cell is therefore a research prompt, not automatically a project blocker. Promote it to critical only when it affects fidelity, implementation, testing, compatibility, or a deliberate product decision.

### Runtime state anchors

Historical TAS work and RetroAchievements provide strong runtime probes for:

- speed;
- X/Y position;
- screen X;
- boost meter;
- flips, rolls, twists, Z-flips and tabletops;
- medal/progression state;
- dense stunt-state and per-tour result blocks.

These should become symbol and validation anchors rather than remaining reference notes.

### Split-screen/OAM behavior

**Local reproduction status (2026-09-29):** the deterministic VS route now reaches active split-screen gameplay and captures HDMA writes `$2104 <- $A5` at scanline 0 and `$2104 <- $5A` at scanline 112 across repeated stable race checkpoints. Patched Snes9x supplies the detailed PPU/OAM journal; the frozen neutral controller stream is also exercised against an independent Beetle/bsnes reference path. Treat these events as the concrete authentic-mode regression target while continuing to reconstruct their effective OAM-address/high-table consequences.

The project has unusually rich independent evidence for Uniracers' raster sprite trick:

- developer testimony describes C64-style sprite ripping and scanline-state changes;
- Snes9x carries a title-specific OAM workaround;
- MAME independently models the same effective active-display OAM location;
- jgenesis documents writes on scanlines 0 and 112 with values `0xA5` and `0x5A`, affecting sprites 96-99;
- the recovered Canoe patch hooks two original ROM locations and installs replacement logic.

This is both a correctness seam and a future presentation opportunity. Authentic mode must model the original behavior; the HD Presentation compositor may eventually render the same logical sprites without needing to reproduce the visual trick at the final-host layer.

### Original graphics pipeline evidence

Developer history says the unicycle was a detailed 3D model rendered down into tiny SNES frames. The animation corpus spans stunt rotations, tilt/stretch, saddle movement, and many pedal/wheel phases. Mike Dailly also lists dedicated **Unicycle Compression** and **A0 plotter** tools.

Therefore the unicycle graphics should be treated as a multidimensional animation system, not merely a sprite sheet.

A major HD Presentation goal is to recover the dimensions and indexing of that corpus so high-resolution assets can be selected from the same original game state that selects the SNES frame. The first racer family now has a mechanically decoded 30-cell, five-by-six occupancy lattice, exact set-cell → packed-record ordering, concrete packed-word → renderer-staging transforms, and retained runtime proof that the 5×6 cells occupy a stable rectangle at tile offset `(1,0)` inside the 64×64 racer OBJ. `major_slot` is stored tile row, `minor_slot` is stored tile column, and OAM H/V flipping is applied later. Packed-word low-byte bits 1..0 are part of the renderer contract: together with the high byte they select the DMA source-address page, while bits 7..2 select the source-bank offset. The four-record `83:F0BB..F295` composer is now also recovered: primary and companion streams are selector-clipped, `$0D1B/$0D1D` gate each player's companion half, enabled companion cells win overlaps while still consuming the hidden primary word, and synchronized MesenCE evidence reproduces all 25 occupied source/destination pairs exactly. `tools/export_racer_composed_snapshots.py` turns this state into deterministic transparent 64×64 stored/display PNGs. Treat this as the reusable semantic boundary for replacement work; expand to other animation families only when a product-facing decision needs them.

### Toolkit capabilities already available

The pinned SNESRecomp framework supplies several pieces directly relevant to the remaster:

- hybrid native execution with interpreter fallback;
- `snesref` for deterministic independent-emulator comparison;
- raw frame, memory and audio capture;
- reusable support patterns for the Widescreen feature developed across existing ports;
- PPU layer policies and margin rendering;
- host-overlay extraction for BG and OBJ content;
- host-side substitution of higher-resolution art;
- data-only `.snesmod` packages for optional assets/features;
- frontend aspect controls;
- optional MSU-1 support if remastered audio is ever desired.

The project toolchain additionally pins:

- Snes9x libretro;
- bsnes libretro;
- SuperFamiconv;
- snes2asm + WLA-DX;
- da65/cc65;
- ghidra-snes;
- Floating IPS;
- ares;
- RetroArch plus the pinned Libretro Slang shader corpus for controlled visual-reference/upscaling experiments;
- bsnes-hd as an on-demand high-resolution/layer-isolation specialist;
- ffmpeg, ImageMagick, jq, ripgrep and standard build tools.

Use these before inventing parallel infrastructure.

---

# Program phases

The phases below are gates, not calendar estimates. Research tracks may run in parallel when they do not weaken the dependency order.

## Phase A - trustworthy stock native game

### Goal

Reach and complete a normal one-player race in the native executable with no presentation enhancement enabled.

### Work

1. Make the title-screen smoke deterministic and non-flaky.
2. Add deterministic controller input, using the recovered 2014 Dessyreqt full-game bot's menu-state policy as a primary accelerator rather than rediscovering frontend navigation from scratch. The project-owned neutral stream must support independent P1/P2 masks without invalidating historical P1-only files.
3. Prove controller-2 causality early: P1 idle/P2 moving, then one simultaneous-input case, before treating any apparent second-racer motion as trustworthy 2P evidence.
4. Navigate:
   - boot;
   - title;
   - player/name/front-end flow as required;
   - mode/course selection;
   - race start.
5. Exercise:
   - acceleration;
   - braking;
   - jumping;
   - rotation;
   - landing;
   - stunt recognition;
   - boost;
   - finish.
6. Capture bounded evidence from both recomp and `snesref`.
7. Record analyzer/AOT/interpreter coverage and unresolved dynamic dispatch encountered by the route.
8. Turn any actual failure into the smallest reproducible test.

### Visual-reference work is decision-triggered, not a Phase-A gate

The project owns a rich visual-reference toolset, but broad scaler/CRT/upscaler matrices are **not** required before stock fidelity is established.

Use raw/native captures as the factual control. Pull in Scale2x/HQx/xBR/SABR/ScaleFX/Super-xBR, NTSC/CRT processing, RetroArch/Slang, bsnes-hd or other reference views only when a concrete graphics/asset question would benefit from competing interpretations. Prefer isolated extracted assets once the underlying graphics/palette/state selection is known.

For each such experiment, define the ambiguity it is meant to resolve and stop once the result is sufficient for an implementation/design decision. Do not generate exhaustive presentation variants merely because the pipeline can.

Canonical implementation details remain in `HD-VISUAL-REFERENCE-PIPELINE.md`, but that pipeline is supporting infrastructure until Phase E/G questions actually need it.

### Gate

A scripted stock route reaches and completes a race, with no known simulation divergence on the compared state surfaces.

## Phase B - deterministic fidelity harness

### Goal

Make simulation fidelity continuously falsifiable before widening or replacing presentation.

### Core oracle

Use `snesref` with the pinned Snes9x core by default. Cross-check PPU/OAM-sensitive findings with bsnes/ares and, where necessary, documented hardware behavior. Once the pinned MesenCE route is proven against the shared fixture grammar, use it as a third deterministic execution engine rather than inventing a separate replay language.

For rendering investigations, keep the fidelity oracle raw. RetroArch/Slang, NTSC/CRT filters and other presentation processing may be used as diagnostic/reference views only after an unprocessed capture is preserved. This separation can help determine whether a discrepancy belongs to SNES/core rendering, frontend presentation, or the recomp runtime without contaminating the actual regression evidence.

### Build canonical scripts

Create short deterministic input scripts for:

- boot/title;
- menu navigation;
- flat straight race;
- jump and clean landing;
- failed landing;
- each major stunt class;
- boost gain and depletion;
- collision;
- race finish;
- a representative AI race;
- one stunt course;
- two-player split-screen;
- Vs.-mode OAM raster behavior.

### Compare

Prefer machine-readable comparison over screenshots alone:

- WRAM writes;
- selected WRAM values;
- CPU state around first divergence;
- frame hashes/raw frame buffers;
- PPU state;
- OAM/high-OAM;
- audio hashes/captures;
- RNG or other discovered state;
- race timer and result state.

### Special golden test

The original developers reportedly reduced feel/fairness testing to a flat straight race. Recreate that idea as a canonical deterministic test using the published speed/position/boost WRAM anchors.

### Emulator-compatibility seam program

Treat historical Uniracers-specific emulator fixes as a source of concrete fidelity requirements, not as folklore or patches to copy blindly.

Build a compatibility matrix with at least these independent seams:

| Seam | Existing evidence | Required project test |
| --- | --- | --- |
| Active-display OAM / sprite ripping | Snes9x title-specific workaround, MAME active-display OAM handling, jgenesis hardware model, Mike Dailly testimony, recovered Canoe patch | Trace writes to `$2104`, scanlines, values, effective high-OAM byte and sprites 96-99; compare native/reference behavior in affected one-player, two-player and Vs. paths |
| LoROM SRAM mapping | historical Snes9x fixes explicitly mentioning Uniracers | Deterministic clean/save/load round trip with byte-level SRAM comparison |
| XOR/window-area logic | historical Snes9x fixes explicitly mentioning Uniracers | Capture affected scenes with PPU/window state and deterministic frame comparison |
| Color math / empty-subscreen behavior | historical Snes9x experiments and regressions involving Uniracers | Capture affected scenes with color-math/subscreen state and deterministic frame comparison |

For the active-display OAM seam specifically:

1. disassemble the recovered Canoe patch hooks at ROM offsets `0x01534C` and `0x015714` and its injected handler at `0x1FFF00`;
2. identify the original routines those hooks replace or bypass;
3. reproduce the canonical ROM's `$2104` behavior under a trusted reference runtime;
4. test the jgenesis observations of scanlines 0/112 and values `0xA5`/`0x5A`;
5. compare Snes9x, bsnes/ares, jgenesis's documented model, the Canoe workaround and SNESRecomp;
6. prefer a correct general SNES PPU/OAM implementation when practical, with game-specific compatibility only as a narrowly justified fallback.

The emulator-history findings are complete only when converted into project-owned regression tests or explicitly rejected as irrelevant to the canonical ROM.

### Gate

4:3 native mode has a repeatable regression suite capable of identifying the first meaningful divergence.

## Phase C - executable and state map

### Goal

Recover enough semantic structure to make enhancement hooks deliberate rather than pattern guesses.

### Priority symbols

Map readers/writers and update routines around:

- `7E:04B7` speed;
- `7E:11CD` boost;
- `7E:0411` / `7E:0415` position;
- `7E:1509` screen X;
- stunt counters;
- camera state;
- current game/mode state;
- current tour/course index;
- current player/opponent state;
- race timer;
- RNG;
- sprite/OAM builder;
- background/tilemap streamer;
- object activation/culling;
- course loader;
- RNC source/destination selector.

### Tools

Use:

- SNESRecomp analyzer and runtime trace surfaces first;
- `snesref` WRAM traces;
- snes2asm/da65 for bounded static regions;
- Ghidra only where cross-reference work earns its setup cost, with canonical project symbols imported from the same generated symbol authority used by snes2asm/da65/Mesen;
- four-ROM diffs to align unchanged functions and expose late changes;
- historical SNasm syntax only as lineage evidence, not as an assumed source language.

### Gate

The symbol map includes the major gameplay, camera, course-loading, sprite-construction and rendering boundaries needed by later presentation features.

## Phase D - exact course model

### Goal

Turn the 45 decoded payloads into a semantic course representation that can be rendered, inspected and eventually edited without changing game physics.

### Immediate work

1. Trace the single known caller path into `RNC1_Unpack`.
2. Identify how the game selects one of the 45 streams.
3. Confirm stream ordinal against a known selected course at runtime.
4. Follow the decompressed destination into its consumers.
5. Test the historical `7E:2080` breadcrumb.
6. Determine the role of the first decoded header words.
7. Test, rather than assume, the historical:
   - 256-wide claim;
   - 64x64-block observation;
   - 8x8 tile relationship.
8. Separate:
   - visual track layout;
   - collision/physics;
   - hazards;
   - boosts;
   - start/finish/checkpoints;
   - metadata/theme;
   - auxiliary dictionaries/tables.

### Independent validation

Render extracted structures and align them against:

- gameplay captures;
- Halamantariel's VGMaps atlas;
- known very long course dimensions;
- the seven PAL-retail changed tracks.

The seven PAL deltas are particularly useful because changed geometry or metadata fields should reveal their meaning when aligned with otherwise identical format structure.

### Deliverables

- documented binary schema;
- parser;
- ROM-to-neutral-course exporter;
- structural visualizer;
- lossless round-trip tests where practical;
- stable course IDs/names once runtime mapping confirms them.

### Gate

At least one course is reproduced structurally from ROM data and matches independent gameplay/map evidence. Then extend to all 45.

## Phase E - original graphics and animation model

### Goal

Understand what the SNES renderer is drawing well enough to replace presentation without changing animation decisions.

**Current family-level status (2026-10-03):** the ordinary two-player race racer family has crossed this semantic-replacement gate. Authoritative presentation identity is read from guest state, duplicate primary IDs are disambiguated by full synchronized composition, stock geometry/pivot/contact anchors are reproducible from the canonical ROM, live placement/orientation comes independently from OAM, and the host-only replacement path now has exact fail-closed selection plus a continuous fully registered 16-frame window (`1205`–`1220`) in the deterministic two-player route. This does **not** close Phase E globally: track/background tiles, UI/fonts/effects, broader racer animation families, and approved final replacement art remain open.

### Asset extraction

Build deterministic extraction for:

- unicycle graphics;
- track/background tiles;
- palettes;
- UI;
- fonts;
- logos;
- menu arrows and other sprites;
- HUD pieces;
- effects.

Use SuperFamiconv where possible. Write custom extraction only for genuinely game-specific packing/indexing.

Before SuperFamiconv output becomes an authoritative replacement path, prove an exact real-asset round trip through snes2asm native bytes → SuperFamiconv → the generated reconstruction worktree → WLA-DX. Fixtures must catch palette/tile order, flips, dimensions, deduplication, base offsets and padding/unused-byte changes.

Public sprite/background sheets are comparison references, not authority. Our extractor should reproduce their content from the canonical ROM.

### Unicycle animation archaeology

Treat this as an indexing problem.

Recover dimensions such as:

- wheel/pedal phase;
- body/saddle pose;
- tilt/stretch;
- rotation/orientation;
- stunt state;
- player color/palette;
- animation timing.

Correlate:

- game-state variables;
- tile/CHR uploads;
- OAM composition;
- ROM source ranges;
- rendered frame identity.

The desired output is a stable semantic asset key such as an original animation/state identifier, not a screenshot hash.

### Why this matters for HD Presentation

A high-resolution unicycle should be chosen by the same original state that chose the low-resolution sprite. That preserves exact animation cadence, stunt poses and gameplay timing while allowing the host to substitute a higher-resolution render.

The semantic asset identity established here must be shared by all three eventual graphics packs. Extraction should therefore produce canonical source assets and registration metadata once, then allow **Original**, **Remastered** and **Reimagined** representations to hang from that same identity instead of growing into disconnected inventories.

### Gate

For each presentation family, original rendered elements can be deterministically identified from authoritative game state and reproduced through an extraction/registration manifest.

The ordinary-race racer family has passed this gate for the currently registered semantic window. Its exact `1205`–`1220` runtime window now also produces a generated approval dossier containing 14 observed representations, ROM-derived stock evidence, verified anchors and trace-derived temporal context. Its next work is no longer generic identity/placement archaeology: make final visual-language decisions against that packet, or deliberately select broader animation-family coverage when that coverage unlocks a specific art/product decision. Phase E as a whole remains open until the other required presentation families reach equivalent sufficiency.

## Phase F - Widescreen feature with stock art

### Goal

Implement the Widescreen feature with stock art before introducing the HD Presentation feature.

This separates geometry/camera problems from asset-resolution problems. Canonical reconnaissance details live in `WIDESCREEN-RECONNAISSANCE.md`; pinned external prior art is summarized in `../reference/notes/widescreen-and-modern-presentation-prior-art.md`.

### First rule

Establish the 4:3 release gate before any Widescreen hook. With the Widescreen feature disabled, enhancement work must leave the authentic path bit-identical on defined deterministic captures.

### F0 - reconnaissance before permanent widening

Before changing game behavior, run a bounded widescreen reconnaissance pass on representative deterministic fixtures.

Required preparation:

1. study the pinned `wide-snes` reference by failure category rather than transplanting Super Mario World patches;
2. establish a small reproducible bsnes-hd diagnostic preset matrix for per-BG widening, sprite clip/safe/unsafe behavior, window handling, overscan and pixel-aspect policy;
3. build `tools/widescreen_probe.py` only after a deterministic capture route exists, reusing the shared fixture grammar rather than creating another replay format;
4. probe increasing horizontal exposure margins (current matrix: +0, +8, +16, +24, +32, +48, +64, +72 source pixels where the runtime can express them);
5. record the first margin/frame at which each rendering or game-state assumption fails.

The probe should classify at least:

- stale/unprepared background columns;
- unintended tilemap wrap or authored-world overrun;
- sprite disappearance, clipping or coordinate wrap;
- newly exposed hidden sprites/objects;
- object pop-in or late graphics preparation;
- window/color-math/scanline-effect boundaries;
- unfinished/offstage art;
- scripted transition or reveal leakage.

The purpose is to replace "widescreen looks wrong" with a machine-readable first-failure map.

### Keep horizontal domains separate

Do not let one `viewport_width` variable silently own unrelated semantics. Model these as distinct policy domains even when stock code happens to conflate them:

1. **simulation / activation bounds** — when gameplay objects exist or become behaviorally active;
2. **preparation / streaming bounds** — when tiles, graphics, stages or other presentation data must be ready;
3. **render / culling bounds** — what can be emitted/drawn;
4. **camera / composition bounds** — how the player and world are framed;
5. **UI composition bounds** — fixed-screen safe areas, edge anchors and host overlays.

Changing one domain does not authorize changing another. In particular, widening visibility must not silently advance AI, RNG, collision, progression or scripted events.

### Apply SNESRecomp's proven Widescreen patterns deliberately

For Uniracers, investigate each applicable pattern rather than copying another game's addresses:

1. **Use PPU scroll phase**, not only WRAM camera mirrors.
2. **Populate newly visible margin data before display** so the first wide frame does not expose stale/wrapped tilemap columns.
3. Classify each background layer as world-anchored, periodic, bounded or HUD.
4. Find a real gameplay-state gate and a separate liveness gate if needed.
5. Widen culling and the OAM emitter together.
6. Preserve signed/negative sprite-X behavior in the left margin.
7. Widen ordinary-object presentation horizons without advancing progression/controller records or simulation activation unless independently justified.
8. Give large objects enough graphics-preparation slack to prevent visible pop-in.
9. Bias graphics/stage streaming only where widened visibility requires it.
10. Give each widening subsystem an independent kill switch.
11. Preserve the original 4:3 path exactly.

### Aspect and pixel-aspect policy

Do not hard-code "widescreen = 352" or any other single source width into game logic.

Define widescreen in terms of:

- logical source viewport bounds;
- target display aspect;
- pixel-aspect policy;
- overscan/safe-area policy;
- optional compatibility presets.

Support 16:9 first, but make fixes viewport-bound-driven so later ultrawide work does not require rediscovering hidden 256-pixel assumptions. Record whether a test uses raw square source pixels or CRT-era pixel-aspect correction.

### Scene classification

Every important screen/sequence should eventually declare a presentation policy rather than inherit a global widening guess. Initial classes:

- `world-expand` — reveal additional authored world;
- `fixed-4:3` — preserve the original composition;
- `fixed-center` — center the original composition inside a wider host canvas;
- `edge-anchored-ui` — keep a bounded world but move selected UI anchors;
- `mixed` — layer-specific policies;
- `special-scripted` — transitions, reveals or sequences requiring explicit handling.

Start with title/frontend, representative one-player race, results, two-player and Vs. Add special cases only from reproduced evidence.

### Course/world boundaries

Uniracers courses can be extremely long and sometimes highly vertical. The Widescreen feature must distinguish:

- continuous track world;
- course boundary;
- repeating decorative backgrounds;
- fixed frontend/HUD surfaces;
- special vertical or looped structures.

Do not invent content by generic tilemap wrap when the authored world has ended.

### HUD/UI

Keep gameplay world widening separate from HUD layout.

Possible policies include:

- keep original HUD centered initially;
- anchor rigid HUD groups to widened edges;
- preserve a 16:9 HUD safe frame on wider outputs;
- use SNESRecomp elastic-band handling only for legitimately stretchable chrome/gauges;
- move to host-overlay composition once HD Presentation UI replacement begins.

### Information-exposure test

For representative hazards, opponents and scripted events, record:

- first simulated;
- first behaviorally active;
- first graphics-prepared;
- first emitted/drawn;
- first visible to the player.

Compare 4:3 and 16:9 on the same deterministic route.

Simulation/activation timestamps should remain identical unless a separately justified compatibility fix requires otherwise. Visibility is expected to move earlier. Record that visibility delta so camera/composition decisions can be reviewed with evidence rather than intuition.

### Two-player and Vs. mode

This is its own gate, not a postscript.

Authentic mode must reproduce the original scanline/OAM trick. Trace and validate:

- writes around scanlines 0 and 112;
- `0xA5` / `0x5A`;
- sprites 96-99;
- high-OAM byte `$18`;
- the Canoe hook regions.

Widescreen coverage must exercise one-player, two-player and Vs. paths, with player-1/player-2 viewport behavior considered independently.

For the Widescreen feature with stock presentation, first determine whether the PPU path can extend both viewports correctly while retaining original sprite-ripping semantics.

For the final HD Presentation path, host composition may be cleaner: preserve the original logical sprite state and split-screen timing, but render the two viewport sprite sets directly instead of depending on the physical OAM side effect for final pixels. This is acceptable only if simulation state remains unchanged and authentic mode still proves the original path.

### Gate

A representative one-player course and the two-player/Vs. path display true additional world width with stock assets; the first-failure reconnaissance map has no unexplained showstopper inside the supported viewport; camera/UI policy is explicit; and deterministic simulation remains equivalent to 4:3.

## Phase G - HD Presentation feature

### Goal

Provide three interchangeable graphics modes without replacing gameplay logic:

1. **Original** — the canonical SNES-derived artwork, retained permanently as the authentic visual-reference mode. It may be presented as raw/nearest pixels or with optional display-only CRT/NTSC treatment, but the underlying art remains the original art.
2. **Remastered** — faithful high-resolution reconstruction of the original artwork. Preserve composition, silhouettes, proportions, palette relationships, shading intent, animation poses, pivots/contact points and other deliberate art decisions while removing the visible limitations of the original pixel grid. At 4K it should read as the same art, only cleanly resolved.
3. **Reimagined** — new modern artwork closely based on the original assets and Uniracers design language. It may add detail, richer materials, smoother illustration and contemporary production value, but should remain recognizably derived from the original rather than drifting into a generic modern visual style.

These are parallel shipping targets, not a ladder where the later mode supersedes the earlier one. A player must be able to choose among all three, and changing the graphics pack must not alter authoritative simulation, collision, RNG, race timing or animation-state selection.

The preferred production lineage is:

```
canonical ROM-derived semantic asset
        |
        +--> Original presentation
        |
        +--> faithful HD reconstruction --> Remastered presentation
                                      |
                                      +--> reference/conditioning input for Reimagined artwork
```

The Remastered asset is therefore both a final product asset and a clean geometric/style reference for Reimagined work. Generative or manual reinterpretation should begin from extracted canonical assets and, where useful, approved faithful reconstructions rather than from screenshots alone.

The evidence/capture contract lives in `HD-VISUAL-REFERENCE-PIPELINE.md`. The coherent-art decision authority lives in `HD-ART-DIRECTION.md`. The production restoration/toolchain contract lives in `ASSET-RESTORATION-PIPELINE.md`. A processed reference may help explain ambiguous source pixels, but no scaler or generated output becomes canonical art by default.

### Preferred mechanism

Use SNESRecomp host-overlay extraction and host-side composition.

The runner can expose already-rendered BG/OBJ content without modifying:

- WRAM;
- VRAM;
- OAM;
- registers;
- DMA;
- savestate state.

Game policy determines what element is being captured; the host can then:

- crop/reposition it;
- scale it;
- omit the stock pixels from final composition;
- substitute higher-resolution art;
- choose final draw order.

This is the natural boundary for the HD Presentation feature.

### HD Presentation asset manifest

Create a versioned manifest mapping semantic original assets/states to replacements.

Every semantic asset family should map cleanly across **Original**, **Remastered** and **Reimagined** representations. Keep enough provenance that future tools/models can reproduce or re-evaluate the derived artwork without rediscovering the source mapping.

Every replacement should have:

- stable semantic ID;
- source-state or extracted-original identity;
- original dimensions/pivot;
- high-resolution dimensions/pivot;
- gameplay-relevant contact/attachment points where applicable;
- animation group and frame;
- neighboring-frame/temporal-coherence evidence for animated assets;
- palette/color policy;
- sampling/render policy;
- intended blend/transparency mode;
- provenance, including model/workflow/settings, masks/reference inputs and meaningful candidate history when generation or AI assistance is used;
- checksum;
- fallback behavior;
- graphics-pack role: Original, Remastered or Reimagined.

Do not key important gameplay art solely on fuzzy image matching.

Animated replacements must be reviewed as sequences as well as stills. Reject contour breathing, scale/pivot/contact drift, inconsistent invented detail or material/highlight flicker even when individual frames look plausible. Generate comparison dossiers spanning raw source, conventional/pixel-art scalers, selected neural upscalers and constrained generative candidates where useful; retain exact model/workflow provenance for every candidate.

Tooling should make side-by-side and rapid-toggle review among all three graphics modes straightforward. Original remains the visual oracle; Remastered must preserve its authored design decisions; Reimagined may depart in surface detail but must retain semantic registration, frame relationships and gameplay-facing geometry unless an explicit presentation-only exception is documented.

### Unicycle strategy for HD Presentation

Two useful routes can coexist:

1. manually/artistically rebuilt high-resolution equivalents;
2. newly rendered 3D source assets designed to reproduce the original poses.

Because the original art itself was rendered from a detailed 3D model, a new 3D source model is historically congruent with the original pipeline. The hard requirement is not "pixel art at higher resolution"; it is that each original animation state selects the corresponding replacement pose with the same timing and pivot behavior.

### Track/world strategy for HD Presentation

Use a staged approach.

**G1: pristine stock geometry at higher output resolution**

Keep original tiles but render/composite cleanly at modern resolution. This establishes coordinates, layer boundaries and camera correctness.

**G2: high-resolution tile/background replacement**

Replace known backgrounds, track tiles and decorative elements through asset identities while keeping the original course/tile structure.

**G3: semantic track renderer, only after the course model is understood**

If the decoded course format reveals track primitives cleanly enough, a host renderer may draw curves/surfaces/effects directly at arbitrary resolution while the original SNES simulation continues to own collision and gameplay.

This is potentially the strongest final presentation path because it avoids magnifying tile limitations, but it is deliberately gated on a verified semantic course model. Do not infer collision geometry from rendered pixels.

### UI and frontend

Menus/HUD are good early HD Presentation candidates because their screen-space regions are easier to isolate and do not alter simulation.

The modern frontend must preserve the **overall original look and vibe** rather than replacing it with generic contemporary UI. Treat the existing frontend as a visual/interaction design language that can host a cleaner information architecture.

Use host overlays to replace or elaborate at higher resolution:

- logos;
- menu art;
- fonts/text panels where practical;
- HUD chrome;
- icons;
- static frontend elements;
- supplementary labels, values, deltas or explanations around original indicators.

When modernizing an existing indicator, keep the original indicator visible and meaningful unless a specific fidelity exception is documented. For example, an original graphical result indicator may remain while exact times/deltas are added beside it.

Frontend restructuring may:

- collapse obsolete administrative steps;
- add create/customize-racer flows;
- add modern profile/save management;
- reorganize records and statistics;
- add explicit confirmations for destructive actions;
- expose new options and accessibility/help surfaces.

But it should preserve recognizable screen composition, animation/motion language, color, typography, sound and other characteristic Uniracers cues wherever practical.

Keep original layout/behavior available as fallback and regression reference, and maintain the UI state map as the evidence source for what the original actually did.

### 4K

4K is a host output target, not a new simulation coordinate system.

The authoritative SNES world remains in original units. The presentation layer maps it into an arbitrary host framebuffer, potentially combining:

- true-wide logical view;
- subpixel/high-resolution asset positions;
- asset-class-specific deterministic sampling/filtering;
- high-resolution replacement textures;
- modern UI layout.

Do not multiply physics coordinates merely because the output is 3840x2160. Do not use one global texture filter for stock pixels, reconstructed sprites, fonts, UI, backgrounds and semantic track geometry; each presentation class needs an explicit policy.

### Gate

A stock gameplay route can be presented with high-resolution replacement art at modern desktop resolutions while producing the same authoritative simulation state as the unenhanced route.

## Phase H - optional audio modernization

Stock SPC audio remains the initial and permanent fallback. The production workflow and provenance rules live in `ASSET-RESTORATION-PIPELINE.md`.

Treat the SPC/APU state as structured source material rather than beginning from a mixed recording. Prefer this order:

1. exact SPC/DSP reference render;
2. per-voice isolation;
3. BRR sample extraction with loop metadata;
4. sequence/event recovery where practical;
5. deterministic reconstruction from recovered samples, envelopes, pitch/modulation, DSP/echo and timing;
6. only then modern sample substitution, re-recording, restoration, generative assistance or mix/master changes.

Bring in or wrap, when Phase H becomes active:

- a cycle-accurate SPC700/DSP reference renderer such as `snes_spc`;
- BRR extraction/decoding tooling such as BRRtools;
- ffmpeg/SoX-class deterministic resampling, normalization and filtering;
- waveform/spectrogram comparison tooling;
- sequence/MIDI extraction experiments where they materially reduce manual transcription;
- neural source separation only for material that cannot already be isolated exactly from APU/SPC state.

For music, preserve composition, timing, arrangement and game-trigger semantics while evaluating exact high-quality rerenders, clean renders of original BRR samples, reconstructed higher-resolution source samples, replacement instruments or hybrid approaches.

For SFX, catalogue each semantic effect's source sample(s), pitch/envelope behavior, DSP context and trigger state before deciding whether to preserve, rerender, reconstruct, subtly layer or replace it. Do not apply one blanket modernization treatment to every effect.

SNESRecomp's optional MSU-1 path is one possible integration boundary because it can stream modern PCM while leaving the original ROM path intact when disabled. Other host-side substitution boundaries are acceptable if they preserve the same fallback and simulation separation.

Require machine-readable provenance for restored/generated audio candidates, parallel to HD visual assets. Keep large models and workstation-specific state out of Git; commit manifests, workflow/project interchange files where practical, hashes, licenses and deterministic recipes.

This phase must never block the visual remaster.

## Phase I - custom courses and editor

This is downstream of understanding the real course format.

Preferred architecture:

- neutral documented course model;
- importer from original RNC course records;
- validator and normalization boundary between authoring data and runtime semantics;
- visual editor that targets the semantic model rather than the original packed binary layout;
- exporter/packaging format;
- runtime loader or data-only mod integration.

For editor/geometry iteration, prefer small deterministic headless fixtures that exercise one curve, transition, surface or camera rule before relying on full-course visual review. The related-project scan in `reference/notes/related-projects-technical-scan.md` records modern examples of both patterns; they are implementation references, not fidelity evidence.

Original courses remain canonical fixtures for parser and renderer tests.

A custom-course format may be cleaner than requiring recompression into the exact original packed layout, provided it feeds the same simulation semantics.

---

# Validation gates for the remaster

## Gate 1 - authentic 4:3

Enhancements disabled must preserve the reference route.

Tests should include:

- state hashes;
- WRAM landmarks;
- frame captures;
- audio where meaningful;
- OAM/PPU behavior for sensitive scenes.

## Gate 2 - Widescreen simulation equivalence

For the same initial state, inputs and frame count:

- player position/velocity must match;
- stunt state must match;
- timer must match;
- RNG must match;
- opponent/AI simulation must match unless a documented visibility policy intentionally changes activation;
- progression must match.

Any deliberate spawn/visibility exception must be isolated and justified.

## Gate 3 - visual completeness

For every widened scene test:

- no stale tilemap margins;
- no wraparound garbage;
- no cull pop;
- no sprite clipping at left/right edges;
- no early stage/progression trigger;
- no HUD gaps/stretch errors;
- no two-player split corruption.

## Gate 4 - HD Presentation substitution correctness

Replacement presentation must preserve:

- pose identity;
- animation cadence;
- pivot/attachment points;
- draw order;
- transparency;
- palette/color semantics;
- screen/world anchoring.

Disabling the HD Presentation pack must return to the stock renderer with no simulation change.

---

# Tool-to-task map

| Need | First tool/path |
|---|---|
| Recomp/native execution | pinned `snesrecomp` |
| Independent deterministic reference | `snesref` + Snes9x libretro |
| PPU/OAM-sensitive independent check | bsnes libretro / ares |
| First CPU divergence | SNESRecomp trace/co-sim facilities |
| ROM/build differences | project Python tools + four preserved ROMs |
| Course decompression | `tools/rnc_method1.py` |
| Course structure | project Python probes + runtime load trace |
| SNES tiles/palettes/maps | SuperFamiconv |
| Broad ROM disassembly | snes2asm + WLA-DX |
| Bounded 65816 disassembly | da65 with known M/X state |
| Long-lived cross-reference work | Ghidra + ghidra-snes |
| IPS experiments | Floating IPS |
| Frame/audio/image conversion | ffmpeg + ImageMagick + libvips |
| Asset provenance/capture | SNESRecomp assetdump/debug surfaces + restoration sidecars |
| HD reference/upscale candidates | pinned scaler matrix + waifu2x / Real-ESRGAN / Real-CUGAN |
| Constrained generative reconstruction | reproducible ComfyUI or scripted Diffusers workflows; structural/reference conditioning |
| HD Presentation layer extraction | SNESRecomp host-overlay extraction |
| SPC reference/voice isolation | cycle-accurate SPC700/DSP renderer such as `snes_spc` |
| BRR sample recovery | BRR extraction/decoding tooling |
| Audio comparison/processing | ffmpeg/SoX-class deterministic processing + waveform/spectrogram probes |
| Optional modern PCM delivery | SNESRecomp MSU-1 support or equivalent host-side substitution |
| Historical syntax/tool lineage | preserved SNasm builds |

---

# Research already in the repo that directly changes implementation strategy

Several collected facts should influence engineering decisions now.

## The unicycle replacement problem is state-identification, not image-upscaling

Developer history describes a high-detail 3D source model and a compressed multidimensional animation corpus. Therefore recover the frame-selection/index logic before committing to the HD Presentation asset pipeline.

## Track graphics and collision are separable

Historical destructive tests reportedly changed visual and physical course behavior independently. The modern port must not derive authoritative collision from an HD Presentation visual mesh. Visual reconstruction can be semantic and modern while collision remains original.

## The 45 RNC payloads are probably the central course asset unit

The exact 45-count, tour cadence and stunt timer byte make them a strong bridge between frontend course selection, course data, runtime load and eventual semantic rendering.

## The game's raster trick is both a compatibility test and a presentation seam

Two-player sprite ripping must be correct in authentic mode, but the final host compositor does not have to reproduce the hardware trick to draw HD Presentation sprites if it can recover the same logical per-viewport sprite state.

## Old emulator bug history gives us a regression inventory

Uniracers has historically exposed issues in:

- LoROM SRAM mapping;
- XOR/window-area inversion;
- color addition / empty-subscreen behavior;
- active-display OAM.

Validate these separately. Do not blame every graphical anomaly on the famous OAM behavior.

## The ROM is aggressively packed

Developer recollection says very little cartridge space remained. Treat apparent gaps cautiously and prefer differential/code-flow evidence before declaring bytes unused.

---

# Current critical path

The last two days materially changed the shape of the project. Broad structural recovery is now a proven capability rather than the main uncertainty. The comparative-island pipeline has mapped enough race, collision, camera, course-resource, OAM, timing, message and rendering-adjacent structure that the scarce resource is **semantic sufficiency for deliberate modification**, not the ability to discover another valid code island.

A fresh agent should therefore optimize for the shortest path to a safely altered presentation, not for island count, bounded-byte count, atlas percentage or archaeological completeness.

1. **Finish the renderer-facing causal chain already in motion.** Prioritize regions that connect camera/window state, world preparation/streaming, sprite/OAM construction, PPU output and race rendering. Current work around the `83:F0BB` race-render path is an example of the right kind of structural recovery because it directly constrains presentation work.
2. **Separate gameplay activation from presentation visibility.** Establish when world objects/opponents/events become behaviorally active versus when their graphics are prepared, culled and emitted. This is a Widescreen safety requirement: widening must not silently advance simulation or reveal state that was not already authoritative.
3. **Close a finite stock-fidelity matrix rather than continue generalized divergence hunting.** Required representative cases are: one-player acceleration/jump/rotation/landing/contact, stunt/reward behavior, finish/results, course transition, ordinary two-player isolated and simultaneous input, VS setup/play, save/load/progression, and the known active-display OAM/raster seam. Compare semantic/event-relative state where absolute host-frame phase is not itself gameplay state. Once this matrix is green, stock fidelity is sufficient for presentation work unless later evidence exposes a counterexample.
4. **Define the minimum course/rendering contract needed for presentation.** Recover course bounds, spatial organization, materialized resources, graphics/tile streaming, object/event placement and the fields needed to render a wider view deliberately. Do not block Widescreen on an editor-complete reconstruction of every course structure.
5. **Begin bounded Widescreen reconnaissance as a reverse-engineering instrument.** After the renderer-facing chain is coherent enough to interpret failures, test tiny horizontal exposure increments such as +8, +16 and +24 source pixels under deterministic fixtures. The purpose is to identify the first violated assumption. Do not preserve a widening change merely because it appears visually plausible.
6. **Recover only the semantic structure demanded by those failures or by fidelity gates.** Structural islands remain valuable, but a new island must now satisfy at least one of these conditions: close a known fidelity uncertainty; unlock a concrete Widescreen/rendering/course requirement; connect or disambiguate an already high-value subsystem; or provide a cheap reusable semantic anchor with clear downstream leverage. Frontier rank alone is not sufficient.
7. **Run deterministic original-asset extraction/reconstruction and animation-state mapping in parallel.** These can advance without waiting for full Widescreen and will later gate HD Presentation. Prioritize exact round trips, resource/animation identity and semantic state mapping, not aesthetic replacement work yet.
8. **Implement stock-art Widescreen once the activation/preparation/render domains are understood.** Expand logical view while holding authoritative simulation and authentic 4:3 behavior constant. Validate information exposure, culling, camera, HUD, multiplayer and raster behavior.
9. **Implement HD Presentation, then the modern product layer.** Higher-resolution presentation comes after semantic asset/state mapping. Contemporary controls, profiles, pause/retry, ghosts/timing/statistics, accessibility and streamlined frontend behavior should remain outside authoritative simulation wherever practical.
10. **Finish editor/custom-content and release packaging after the underlying semantic formats are stable.**

Supporting research is pulled forward when it shortens one of these steps. It does not become critical merely because evidence exists, an analyzer can expose it, or a previous workstream had momentum.

## Structural-recovery stop rule

The comparative structural census is an instrument, not a completion metric.

Before starting a new island, name the **decision it can change** and the **downstream gate it can unblock**. Continue only when at least one is concrete. Prefer an adjacent region that closes a causal chain over an isolated region with a slightly higher generic frontier score. Stop expanding a subsystem when the project can already observe the relevant state, explain the behavior needed by the product, modify it safely, and validate the result.

Completed-island narratives belong in generated census/evidence artifacts and the research ledger. The active queue should retain only the current blocker, why it matters, the cheapest discriminator, success condition and stop condition.

## Semantic-sufficiency model

Canonical evidence-backed status: `docs/SEMANTIC-SUFFICIENCY.md`.

Track major product-facing subsystems by capability rather than byte coverage. For each subsystem, ask whether the project can:

- **observe** the authoritative state deterministically;
- **explain** the causal behavior relevant to the product;
- **modify safely** without accidentally changing neighboring simulation;
- **validate** the modification against authentic/reference behavior.

Use `unknown / partial / sufficient` for each dimension. A subsystem becomes a semantic research priority when a missing dimension blocks the current critical path.

The first scoreboard should cover at minimum:

| Subsystem | Observe | Explain | Modify safely | Validate | Current planning consequence |
| --- | --- | --- | --- | --- | --- |
| Racer simulation / core physics | sufficient | sufficient | sufficient for preservation; modification normally prohibited | sufficient | Reopen only for a new event-relative discrepancy |
| Camera / screen-relative projection | sufficient | sufficient | partial | sufficient | Complete renderer-facing integration rather than map unrelated code |
| Sprite/OAM construction and split-screen seam | sufficient | sufficient | partial | sufficient | Hard authentic-mode and Widescreen constraint |
| Object/gameplay activation | sufficient for representative checkpoint/finish family | sufficient | partial | sufficient | Preserve activation independently of widened presentation; reopen on a discrepant object family |
| World preparation / VRAM streaming | sufficient for representative stock schedule | sufficient for representative stock schedule | accepted through +72 host-owned materialization | sufficient for stock schedule, +8 native scheduling, and accepted random-access host materialization through +72 | Run `37146519813` closes +72 with exact semantic/protected-state acceptance under bounded ±2 capture-phase tolerance. The preferred provisional Authentic 256×224 + 7:6 transform derives +48 for 16:9; validate that transform, then bind actual viewport/composition state to the provider. |
| Course spatial/resource model | sufficient | sufficient for representative presentation questions | partial | sufficient on representative contract + sampled family invariants | Presentation-sufficient; defer editor-complete tail |
| Frontend / progression | sufficient | sufficient for principal stock flow | partial | sufficient for stock save/load/progression | Stock persistence closed; reopen only for a concrete fidelity or product-policy need |
| Modern product / host administrative state | sufficient for host state, durable desktop settings, pause, Retry, host-owned Options/Controls/Run Data, confirmed Quit Desktop and production native-host integration | sufficient ownership boundary | sufficient for current pause/restart/Options/Controls/Run Data/desktop-quit slice plus live host Display/VSync application | sufficient deterministic/native acceptance; run `37148646286` proves schema-v3 Focus Pause/Display/VSync persistence and Authentic inertness through the ordinary product executable, and `37148647371` keeps Restart/SRAM preservation green | Continue profiles, autosave/resume, richer run statistics/splits, presentation-refresh pacing, additional proven settings and true Exit-to-Frontend without changing guest authority |
| Original graphics / animation state | sufficient for the first composition-aware racer replacement neighborhood | sufficient for the registered racer family | sufficient for presentation-only substitution and Original fallback | sufficient for current registered states | Continue adjacency-driven semantic coverage and approved art; do not reopen identity/placement architecture |

Update this table when evidence changes a capability class. Do not inflate a class merely because more bytes were bounded.

## Fidelity closure rule

Absolute host-frame identity is not itself a product requirement when runtimes cut the same guest transition on adjacent host boundaries and event-relative authoritative state agrees. Preserve frame-level diagnostics where they expose a real causal difference, but do not manufacture fidelity debt from harmless phase alignment.

Conversely, any event-relative difference in authoritative simulation, progression, object activation, collision, timing, RNG or multiplayer causality remains a real blocker until explained or explicitly adopted as product policy.

## First useful HD Presentation prototype

The first HD Presentation experiment should **not** try to replace the whole game's presentation.

A good vertical slice is:

- one deterministic one-player course;
- stock simulation;
- true 16:9 world view;
- original course geometry;
- one high-resolution unicycle replacement set for the states actually encountered;
- one background/theme treatment;
- original HUD initially, then one HD Presentation overlay pass;
- side-by-side 4:3 regression route proving unchanged simulation.

That slice exercises every architectural boundary without requiring complete asset replacement.

---

# Public-release boundary

The private research repository intentionally contains ROMs and preservation material that must not simply become a public release repository.

Before public distribution:

1. audit tracked proprietary artifacts and Git history;
2. separate the public source/tooling history if necessary;
3. require the user's own verified ROM;
4. generate derived native code locally or use the framework's setup-host model;
5. package optional HD Presentation assets through a clearly versioned data boundary such as `.snesmod`;
6. keep original-ROM validation and fallback behavior explicit.

This release constraint should shape packaging late, but it should not distort current private research.

---

# Definition of done

The project reaches its intended goal when a player can supply the supported original game, launch a native port, and play Uniracers with:

- demonstrably original simulation behavior;
- authentic 4:3 fallback;
- the Widescreen feature;
- modern-resolution output;
- high-resolution presentation assets;
- correct one-player and split-screen behavior;
- deterministic regression coverage against the original;
- documented course/asset structures sufficient to maintain and extend the port.

Everything else, including custom courses, remastered audio, ultrawide modes and additional presentation options, is an extension beyond that core victory.


## Evidence-to-executable conversion rule

The repository contains substantial historical/community evidence. Its value is realized only when it changes executable understanding or a product decision.

Current priorities and live work belong in `docs/WORK-QUEUE.md`. Research/acquisition triage belongs in `docs/RESOURCE-COLLECTION-AND-DEV-RESEARCH-PLAN.md`. Chronological attempts and old branch/PR recovery details belong in logs, ledgers and preserved evidence, not in this product plan.

Promote useful evidence into one or more durable forms:

- deterministic fixture or first-divergence discriminator;
- locally verified symbol/state meaning;
- parser/decoder or comparative-atlas correspondence;
- generated compact evidence report;
- regression test;
- architecture/implementation constraint;
- explicit negative result that prevents repeated work.

Do not preserve old task ordering merely because it once reflected active branches. The current critical path above outranks historical workstream momentum.
