# Work Queue

Work in dependency order. Later visual work is intentionally gated on a trustworthy stock baseline.

## Phase 0 — Evidence floor

- [x] Create private GitHub repository.
- [x] Select a pinned SNESRecomp revision.
- [x] Add SNESRecomp gitlink/submodule at the pinned revision.
- [x] Place canonical project ROM in the private repository for repository-hosted tooling.
- [x] Fingerprint exact ROM revision: SHA-256, CRC32, size, header/mapping, region and vectors.
- [x] Record ROM identity in project-readable form.
- [x] Make verification tooling accept only the canonical fingerprint.
- [ ] Record baseline behavior in trusted emulators where useful.

**Exit:** the canonical input is fingerprinted and machine-verifiable.

## Phase 1 — Analyzer reconnaissance

- [x] Run the pinned SNESRecomp cartridge probe against the canonical ROM.
- [x] Run analyzer/code-discovery reconnaissance.
- [ ] Record cartridge mapping, banks, AOT/static coverage, unresolved indirect dispatch, interpreter fallback, warnings, crashes and likely framework gaps.
- [ ] Classify blockers as configuration, analyzer limitation, runtime/hardware, or unknown.
- [ ] Keep human-authored summaries and configs; avoid committing giant generated code dumps without a reason.

**Exit:** we know what blocks or permits execution.

## Phase 2 — First boot

- [x] Fix native-smoke executable discovery: exact generated game target is required; arbitrary CMake helper fallback removed.
- [x] Launch the actual generated Uniracers native target under the smoke workflow.
- [x] Native window opens under Xvfb (960×720 reported by host).
- [x] Native main loop enters and first frame simulates; treat this as execution bring-up cleared, while exact reset-vector tracing remains available if needed.
- [x] First simulated frame and audio callback complete without a reported DMA/HDMA initialization failure.
- [x] Title/logo sequence appears and frame 300 has been visually verified from the actual native target.
- [~] Input reaches menus. The native scripted harness now proves `mainMenu = 0xD7` → `onePlayerSelect = 0x3C` → `onePlayerTours1 = 0x6D` → `onePlayerTracks = 0xF6` under real controller input. The route is advancing one observed menu state at a time toward race entry.
- [ ] A mode can be selected.

**Exit:** title/menu operation is reproducible.

## Phase 3 — First playable race

- [ ] Reach one-player race.
- [ ] Track/player/background render plausibly.
- [ ] Audio runs.
- [ ] Start, accelerate, jump, rotate, land and finish.
- [ ] No simulation modifications.

**Exit:** complete a stock race in 4:3.

## Phase 4 — Emulator-compatibility seams

Convert known historical Uniracers emulator fixes into local understanding and permanent regression coverage. Keep the seams separate rather than treating every problem as the OAM quirk.

### Active-display OAM / sprite ripping

- [ ] Test whether current runtime already handles the behavior correctly.
- [ ] Reproduce the failure if not.
- [ ] Determine affected one-player, two-player and Vs. modes.
- [ ] Trace writes to `$2104` and verify expected scanline/value behavior, including the jgenesis 0/112 and `0xA5`/`0x5A` observations.
- [ ] Verify the effective high-OAM target and sprites 96-99.
- [ ] Disassemble the recovered Canoe patch hooks at `0x01534C` and `0x015714` plus injected handler at `0x1FFF00`.
- [ ] Compare unpatched behavior, Canoe workaround, Snes9x special case, MAME/jgenesis models and bsnes/ares reference behavior.
- [ ] Reduce any mismatch to the smallest deterministic case.
- [ ] Prefer a correct general SNES behavior fix to a game-specific hack.

### Other historically exposed seams

- [ ] LoROM SRAM mapping: build deterministic save/load byte-roundtrip coverage.
- [ ] XOR/window-area logic: identify an affected screen and add PPU/window-state plus frame regression coverage.
- [ ] Color math / empty-subscreen behavior: identify an affected screen and add PPU/color-math plus frame regression coverage.
- [ ] Record each seam's final explanation in the research ledger / knowledge base and link its permanent test.

**Exit:** the known historical Uniracers emulator compatibility problems are either reproduced and covered by deterministic tests or explicitly shown not to apply to the canonical runtime.

## Recovered autonomous-player accelerator

- [x] Locate public source for Dessyreqt's 2014 full-game real-time Uniracers bot (Pastebin `A0XpKw9v`).
- [x] Preserve the source and submitted #4250 SMV in the repository with hashes/provenance.
- [ ] Verify the bot's key RAM labels against the canonical ROM/runtime. The historical 2008 Microstorage WIP SMV has also been recovered and should be used as a second deterministic input corpus.
- [~] Port or translate its menu-driving policy into the native/snesref deterministic input harness. Main-menu, rider-select, first-tour and track-select states are verified under real scripted controller input; current work is confirming the default track and discovering the following now-playing state.
- [ ] Evaluate its race-driving policy as an autonomous regression workload.

## Phase 5 — Differential validation

Use `snesref` or another trustworthy reference route.

- [ ] Deterministic input sequences.
- [ ] WRAM/state comparison.
- [ ] First-divergence workflow.
- [ ] Regression cases for race start, acceleration, jump, rotation, landing, stunt, collision, finish and two-player.

**Exit:** fidelity is objectively testable.

## Phase 6 — Reverse-engineering map

Prioritize: main loop, input, race state, player physics, camera, course loader, RNC decompression, course representation, sprite/OAM construction, culling, HUD and audio hooks.

Maintain `SYMBOLS.md` and `RESEARCH-LEDGER.md`.

## Phase 7 — Course format

- [ ] Locate compressed blocks and pointer/index tables.
- [x] Verify RNC Method 1 corpus and independently decompress all 45 streams with CRC validation.
- [ ] Reconstruct dimensions and primitives.
- [ ] Produce structural documentation.
- [ ] Build parser/tooling around the canonical ROM.

## Phase 8 — Widescreen

Only after deterministic stock behavior is established.

- [ ] Separate viewport width from gameplay/collision semantics.
- [ ] Widen render/culling paths deliberately.
- [ ] Test object activation and opponent behavior.
- [ ] Preserve 4:3 regression mode.

## Phase 9 — Modern presentation

Optional authentic scaling, arbitrary windows, 16:9/ultrawide, high-resolution UI and replacement presentation layers.

## Phase 10 — Editor/custom courses

Design only after the real course representation is understood. Prefer a documented custom-course format loaded without altering core physics.


## Original-development archaeology workstream

Canonical combined plan: `docs/RESOURCE-COLLECTION-AND-DEV-RESEARCH-PLAN.md`

See docs/original-development/.

- [x] Establish confidence-labelled developer technical history.
- [x] Create source index and acquisition ledger.
- [x] Acquire and place the 1994-11-29 PAL prototype in `reference/roms/prototypes/`.
- [x] Fingerprint the PAL prototype and record header/mapping metadata; extend vector reporting if useful.
- [x] Generate first structural PAL-prototype vs USA-retail diff report.
- [x] Acquire, organize and fingerprint PAL retail and the historical GoodSNES-listed beta image.
- [x] Generate four-build differential comparison, including USA retail vs legacy beta and PAL retail vs 1994-11-29 prototype.
- [x] Inspect DMA press-material archive; retain/upload the Uniracers PDF judged relevant.
- [ ] Continue hunt for Mike Dailly's historical SNES framework source.
- [ ] Search for binaries/source/screenshots of SNasm, Unicycle Compression, level editor, A0 plotter, graphics/MIDI converters and Amiga/SNES link.
- [ ] Convert remaining historical predictions into local ROM tests: 256-wide course interpretation, copier protection, animation indexing and audio-driver identity. RNC Method 1 and OAM/raster behavior now have strong local/external evidence.
