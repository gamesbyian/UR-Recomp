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
- [x] Input reaches menus. The native scripted harness proves the full clean frontend chain `0xD7 → 0x3C → 0x6D → 0xF6 → 0x16` under real controller input and then enters race state `7E:0313 = 1`.
- [x] A one-player mode/track can be selected and started deterministically.

**Exit:** title/menu operation is reproducible.

## Phase 3 — First playable race

- [x] Reach one-player race.
- [x] Track/player/background render plausibly. Native and Snes9x race-entry framebuffers show the same coherent stock race scene; exact pixel/color fidelity remains a separate compatibility question.
- [~] Audio pipeline runs through the native race fixture: 32 kHz stereo device opens and callbacks begin under SDL dummy audio with no runtime error. Audible/content fidelity still needs capture or listening evidence.
- [x] Start race deterministically and accelerate under controlled Right input with matching native/reference X position/speed semantics.
- [x] Jump under sustained B input from the validated moving state. Run 36514981164 causally validates player-1 Y position, signed Y speed and air state against a matched Right-only control in both native and Snes9x.
- [x] Rotate intentionally with L/R while airborne. Run 36516524308 confirms persistent player-1 `7E:04C7` as a modulo-64 pitch angle: eight L frames move 7→55 (−16 mod 64), eight R frames move 7→23 (+16), identically native/reference.
- [x] Land with event-relative state validation. Run 36517502791 matches native/reference throughout: track-height contact clears `air` by `landing-034`, and vertical velocity is fully reset by `landing-036`. Script labels include the runner's mandatory idle frames and are treated as event-relative.
- [x] Validate one reproducible collision/contact case. Run 36518208740 is green and native/Snes9x agree at every tracked semantic checkpoint. Against the timing-identical clean-jump control, the 16-frame airborne over-rotation intervention produces a distinct failed-landing/contact trajectory: at the key checkpoint player 1 remains airborne with `ySpeed=-187` and reduced `xSpeed=389`, while control is already grounded with `ySpeed=0` and `xSpeed=448`; the displacement/speed difference persists through settle.
- [~] Finish a stock race deterministically. Collision/contact is closed. The active discriminator is now exact replay of the recovered reset-anchored 2008 WIP using its frozen controller stream plus embedded starting SRAM in both pinned Snes9x and the native Lua bridge; the simpler rhythmic Dragster probe remains a secondary diagnostic.
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
- [~] Verify the bot's key RAM labels against the canonical ROM/runtime. Frontend/race-entry state is verified; the active race-acceleration fixture is now testing the effective Lua player-1 X position/speed fields (`7E:0411`, `7E:04B7`) and related recovered state. Duplicate player-1 Lua keys have been resolved by actual Lua overwrite semantics. The historical 2008 Microstorage WIP SMV remains a second deterministic input corpus.
- [x] Port the clean menu-driving route into the shared native/snesref deterministic input harness through race entry.
- [~] Evaluate its race-driving policy as an autonomous regression workload. A first bounded whole-race script is active, and the preserved 2014 SMV now has a deterministic extractor plus coarse pinned-Snes9x replay workflow so exact historical first-race input can be recovered before porting more policy logic.

## Phase 5 — Differential validation

Use `snesref` or another trustworthy reference route.

- [x] Deterministic input sequence to first race, shared verbatim by native and snesref.
- [x] Full-WRAM/state checkpoint comparison across native and Snes9x/snesref. The first-race fixture compares all 128 KiB at seven checkpoints and reduces the settled-race difference to seven bytes.
- [x] First-divergence workflow for the settled first-race checkpoint. Run 36511207129 resolves `$01D1–$01D4` as stale stack residue (`SP=$01FF`, `E=false`, no ordinary WRAM writers) and `$00C6/$00C8/$00C9` as free-running timing/phase counters. There is no remaining unexplained persistent gameplay-state divergence in this checkpoint.
- [~] Regression cases for race start, acceleration, jump, rotation, landing, stunt, collision, finish and two-player. Race start, acceleration, jump, rotation, landing and one failed-landing/contact case are covered. Deterministic Dragster finish is the active next fixture; stunt and two-player remain open.

**Exit:** fidelity is objectively testable.

## Phase 6 — Reverse-engineering map

Prioritize: main loop, input, race state, player physics, camera, course loader, RNC decompression, course representation, sprite/OAM construction, culling, HUD and audio hooks.

Maintain `SYMBOLS.md` and `RESEARCH-LEDGER.md`. `tools/export_symbols.py` generates `analysis/generated/symbols.json`; repository hygiene fails if the machine-readable export is stale.

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


## Third-party code audit and adaptation

- [x] Establish an explicit imported-code review/adaptation policy.
- [x] Audit the recovered 2014 Lua bot for silent language/runtime hazards; duplicate table keys and the signed `0x8000` edge bug are recorded.
- [x] Centralize promoted player-state addresses and signed conversion in `tools/uniracers_state.py`.
- [x] Add unit coverage for promoted state semantics, duplicate-Lua-key detection and RNC packed-payload bounds.
- [x] Classify the Snes9x 1.43 Uniracers branch as historical workaround evidence rather than an implementation template.
- [~] Audit imported emulator/source snapshots for assumptions worth converting into deterministic compatibility tests. Active-display OAM is the first concrete seam.
- [~] Port useful autonomous-player behavior into neutral state/policy/input layers. Exact historical SMV replay is preferred where prerecorded input suffices.
- [ ] Review any newly imported executable/script before promoting it into a project-owned dependency.

Canonical audit: `docs/THIRD-PARTY-CODE-AUDIT.md`.
