# Work Queue

Work in dependency order. Later visual work is intentionally gated on a trustworthy stock baseline.

## Priority 0 — Island / offline toolchain

**This workstream preempts new infrastructure expansion, but must not interrupt or overwrite active research already in flight.**

Canonical execution plan: `docs/ISLAND-TOOLCHAIN-PLAN.md`.

Goal: make the core automated research/build toolchain runnable from a clean checkout without GitHub, PyPI or crates.io after ordinary host/compiler prerequisites are present.

- [x] Add the `third_party/` provenance/licensing/manifest infrastructure, repository-hygiene validation, local-source bootstrap preference, and fail-closed offline mode. A true network-disabled build smoke follows the first islanded core component.
- [ ] Vendor the small/high-value tool tranche and package-registry closures. `mesen-for-ai`, `snes2asm` plus its PyYAML 6.0.3 closure, SuperFamiconv plus its 78-package Cargo vendor closure, `ghidra-snes` source/language data, and pruned Flips CLI are complete. Beetle/bsnes libretro is landed, and independent-reference run 36627766874 successfully drives the same seven-checkpoint first-race fixture through Snes9x and repository-owned Beetle (race entry at frames 1035 and 1038 respectively). The current promotion branch moves Beetle into the ordinary fail-closed offline bootstrap/build matrix; once that branch matrix is green, P0-B is complete and work moves fully to P0-C. Beetle's post-fixture teardown abort and cross-core WRAM differences remain explicit follow-up evidence, not blockers to the independent execution gate.
- [ ] Migrate SNESRecomp and core reconstruction/build dependencies incrementally. WLA-DX is complete as the first P0-C core-build tranche: the repository owns the exact pinned 65816/linker source closure plus the narrow build patch; ordinary `bootstrap_toolchain.py --offline` proof is green.
- [ ] Preserve large/manual workbenches as exact archives or optional external tools where direct vendoring has poor value.
- [ ] Prove a network-disabled core workflow before removing the old fetch paths.
- [ ] Use repository ownership to customize/optimize tools for UR-Recomp where measured value justifies divergence from upstream.

**Concurrent-work rule:** PRs #9, #11 and #14 were active when this P0 item was created and currently overlap plan/tooling files. Islandization must be implemented in isolated tranches, kept draft when necessary, and rebased/reconciled with current `main` plus all still-active overlapping PRs before merge. Do not merge a mechanically conflict-free result if it would discard or stale their work.

**Merge gate:** inspect open PRs/unsubmitted branches, reconcile by intent, regenerate derived artifacts, run repository hygiene + toolchain contract/build smoke, and verify no active evidence/fixture path is weakened. See the canonical plan for the full procedure.


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
- [x] Record cartridge mapping, banks, AOT/static coverage, unresolved indirect dispatch, interpreter fallback, warnings, crashes and likely framework gaps. Run 36575810121 records a standard 2 MiB LoROM / 8 KiB SRAM cartridge, 9 analysis roots expanding to 54 exact variants, 52 AOT-eligible variants, 2 bounded LLE-only variants, and three unique unresolved indirect guest sites explicitly routed as `lle_dynamic`; see `analysis/generated/analyzer-reconnaissance.md`.
- [x] Classify blockers as configuration, analyzer limitation, runtime/hardware, or unknown. No Phase-1 configuration or runtime blocker remains; the two LLE-only variants and three unresolved indirect sites are bounded analyzer-proof gaps covered by the interpreter tier, and later deterministic native bring-up reaches menus and a stock race through the same pinned framework.
- [x] Keep human-authored summaries and configs; avoid committing giant generated code dumps without a reason. The project preserves a compact manifest-derived report plus its deterministic summarizer and does not retain generated C.

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
- [~] Finish a stock race deterministically. Collision/contact is closed. The 2014 Dessyreqt historical movie supplies the durable pinned-Snes9x reference oracle, reaching first race at frame 794 and first results at frame 2874 (run 36538122590); native replay of an exact historical stream remains open. The 2008 WIP is now explicitly a legacy-timing compatibility corpus: its full modern pinned-Snes9x reference replay never reaches race/results, matching the unresolved WIP1-timing concern rather than providing a usable finish oracle. The simpler rhythmic Dragster probe remains a secondary diagnostic.
- [ ] No simulation modifications.

**Exit:** complete a stock race in 4:3.

## Phase 4 — Emulator-compatibility seams

Convert known historical Uniracers emulator fixes into local understanding and permanent regression coverage. Keep the seams separate rather than treating every problem as the OAM quirk.

### Active-display OAM / sprite ripping

- [ ] Test whether current runtime already handles the behavior correctly.
- [ ] Reproduce the failure if not.
- [~] Mode coverage: VS mode is now deterministically reproduced through active split-screen gameplay with the scanline-0/112 $2104 HDMA seam captured. Ordinary 2P and any 1P occurrence still need explicit classification.
- [x] Trace writes to `$2104` and verify expected scanline/value behavior. The durable VS regression reproduces HDMA `$2104 <- $A5` at scanline 0 and `$2104 <- $5A` at scanline 112 at every sampled stable race checkpoint; the source table is `7E:206C = 70 A5 70 5A 00`.
- [x] Verify the effective high-OAM target and sprites 96-99. Stable race snapshots end with `OAM[0x218] = 0x5A`; independent Snes9x/MAME/jgenesis/SNESdev evidence identifies `0x218` as the active-display destination. High-table byte index `0x18` controls sprites 96-99, and the project decoder verifies the `$A5/$5A` two-bit pair swap.
- [ ] Disassemble the recovered Canoe patch hooks at `0x01534C` and `0x015714` plus injected handler at `0x1FFF00`.
- [ ] Compare unpatched behavior, Canoe workaround, Snes9x special case, MAME/jgenesis models and bsnes/ares reference behavior.
- [ ] Reduce any mismatch to the smallest deterministic case.
- [ ] Prefer a correct general SNES behavior fix to a game-specific hack.

### Other historically exposed seams

- [x] LoROM SRAM mapping: run 36661148644 extracts the historical 2008 movie's known-valid 8 KiB SRAM image (SHA-256 `15650bb496292c6fc9c1ea35f8b26070d8c1617169fbe75be3c0482d98649fd1`) and proves exact preload→dump byte identity under both pinned Snes9x and the repository-owned Beetle core. Beetle now exposes `RETRO_MEMORY_SAVE_RAM` as 8192 bytes and exits cleanly after the fixture. Toolchain run 36661148675 independently proves the narrow compatibility patch in the ordinary fail-closed offline matrix.
- [x] XOR/window-area logic: run 36658348552 isolates the ordinary one-player `race-entered` checkpoint at frame 1035 as the only sampled XOR-active scene; BG1-4, OBJ and color all have both windows enabled with XOR logic, while the sampled frontend and stable VS checkpoints are negative controls. The permanent workflow now requires the XOR-active checkpoint set to remain exactly `{race-entered}`.
- [x] Color math / empty-subscreen behavior: canonical scene survey plus historical fallback A/B are complete. Frontend states use `CGWSEL=02`, `CGADSUB=7F`, `TS=10`, while active race changes to `CGADSUB=04` and fixed red=15. The historical backdrop-for-empty-subscreen perturbation changes ~97-99% of several frontend frames, 0 pixels on Rider Select, and only 392 pixels in a narrow race band; reject any title-wide compatibility fallback and preserve per-pixel SNES color-math semantics. Evidence: `analysis/generated/color-math-scene-survey.json` and `analysis/generated/color-math-fallback-ab.json`.
- [ ] Record each seam's final explanation in the research ledger / knowledge base and link its permanent test.

**Exit:** the known historical Uniracers emulator compatibility problems are either reproduced and covered by deterministic tests or explicitly shown not to apply to the canonical runtime.

## Recovered autonomous-player accelerator

- [x] Locate public source for Dessyreqt's 2014 full-game real-time Uniracers bot (Pastebin `A0XpKw9v`).
- [x] Preserve the source and submitted #4250 SMV in the repository with hashes/provenance.
- [~] Verify the bot's key RAM labels against the canonical ROM/runtime. Frontend/race-entry state is verified; the active race-acceleration fixture is now testing the effective Lua player-1 X position/speed fields (`7E:0411`, `7E:04B7`) and related recovered state. Duplicate player-1 Lua keys have been resolved by actual Lua overwrite semantics. The historical 2008 Microstorage WIP SMV remains a second deterministic input corpus.
- [x] Port the clean menu-driving route into the shared native/snesref deterministic input harness through race entry.
- [~] Evaluate its race-driving policy as an autonomous regression workload. The preserved 2014 SMV now has a deterministic extractor and a confirmed pinned-Snes9x first-race/results replay with durable frame/state evidence. Prefer replaying this exact historical input through native before porting more state-responsive policy logic.

## Phase 5 — Differential validation

Use `snesref` or another trustworthy reference route.

- [x] Deterministic input sequence to first race, shared verbatim by native and snesref.
- [x] Full-WRAM/state checkpoint comparison across native and Snes9x/snesref. The first-race fixture compares all 128 KiB at seven checkpoints and reduces the settled-race difference to seven bytes.
- [x] First-divergence workflow for the settled first-race checkpoint. Run 36511207129 resolves `$01D1–$01D4` as stale stack residue (`SP=$01FF`, `E=false`, no ordinary WRAM writers) and `$00C6/$00C8/$00C9` as free-running timing/phase counters. There is no remaining unexplained persistent gameplay-state divergence in this checkpoint.
- [x] Establish a backward-compatible neutral P1/P2 controller stream (`start:duration:p1-mask[:p2-mask]`) plus native-Lua and Mesen writers; preserve all historical three-field P1 corpora unchanged. Keep the pinned `snesref` P2 delta as a project patch until equivalent support is upstream.
- [~] P2 transport now has canonical-ROM causal evidence and a deterministic VS route into active split-screen gameplay. Remaining promotion work is ordinary 2P coverage, simultaneous-input gameplay semantics, paired racer-state checkpoints across native/patched `snesref`/Mesen, and persistent cross-runtime parity.
- [ ] Adapt the recovered 2014 policy so either controller can be driven independently; use that to create bot-vs-bot and human-vs-bot soak workloads after the deterministic 2P route is trusted.
- [~] Regression cases for race start, acceleration, jump, rotation, landing, stunt, collision, finish and two-player. Race start, acceleration, jump, rotation, landing and one failed-landing/contact case are covered. Deterministic Dragster finish is the active next 1P fixture; 2P transport infrastructure now exists, while gameplay promotion, stunt and full two-player regression remain open.

**Exit:** fidelity is objectively testable.

## Phase 6 — Reverse-engineering map

Prioritize: main loop, input, race state, player physics, camera, course loader, RNC decompression, course representation, sprite/OAM construction, culling, HUD and audio hooks.

Maintain `SYMBOLS.md` and `RESEARCH-LEDGER.md`. `tools/export_symbols.py` generates `analysis/generated/symbols.json`; repository hygiene fails if the machine-readable export is stale.

## Phase 7 — Course format

- [~] Locate compressed blocks and pointer/index tables. All 45 Method-1 course payload blocks are located and verified; the selector/pointer/index structure remains open, with direct/split/relative/fixed-record encodings under mechanical search.
- [x] Verify RNC Method 1 corpus and independently decompress all 45 streams with CRC validation.
- [~] Reconstruct dimensions and primitives. Header bytes 13/14 form a confirmed 45/45 fixed-area structural invariant: zero-as-256 yields complementary pairs whose product is 1024. LE16@11 is now runtime-confirmed on Dragster and stream 11 as a mutable pre-trailer cursor that advances exactly through the variable trailing region to EOF−1; trailer grammar, dimension unit/consumer and geometry primitives remain open.
- [ ] Produce structural documentation.
- [ ] Build parser/tooling around the canonical ROM.

## Phase 8 — Widescreen

Only after deterministic stock behavior is established. Canonical reconnaissance contract: `docs/WIDESCREEN-RECONNAISSANCE.md`.

- [x] Pin and summarize concrete widescreen/recomp prior art without turning it into implementation authority.
- [x] Seed machine-readable widescreen domain/scene/probe vocabulary in `analysis/widescreen-policy.yml`.
- [ ] Prove a deterministic bsnes-hd diagnostic invocation and commit a small project-owned preset matrix for BG/sprite/window/PAR exposure experiments.
- [ ] Implement `tools/widescreen_probe.py` on the shared fixture grammar once the capture route is proven; sweep staged margins and emit first-failure reports.
- [ ] Classify representative title/frontend, one-player, results, two-player and Vs. scenes by explicit presentation policy.
- [ ] Separate simulation/activation, preparation/streaming, render/culling, camera/composition and UI-composition widths.
- [ ] Define viewport/PAR/overscan policy without hard-coding 16:9 source widths into game logic.
- [ ] Widen render/culling paths deliberately while keeping stock simulation timing unchanged.
- [ ] Measure object/opponent/event information exposure between matched 4:3 and 16:9 runs.
- [ ] Exercise player-1/player-2 split-screen and Vs. behavior independently, including the authentic sprite-ripping path.
- [ ] Preserve bit-identical 4:3 regression mode.

## Phase 9 — Modern presentation

Optional authentic scaling, arbitrary windows, 16:9/ultrawide, high-resolution UI and replacement presentation layers.

### Frontend modernization / subtraction

Do this from the verified original UI state map, not from memory or generic modern-UI assumptions.

- [ ] Classify original frontend states/features as presentation artifact, gameplay mechanic, or administrative/hardware-era system.
- [ ] Preserve every original audiovisual indicator by default; add clearer labels, values, deltas or expanded views alongside it rather than deleting it.
- [ ] Define the reusable menu visual-language contract from captured evidence: composition, typography, palette, animation/motion, cursor behavior, sounds and transitions.
- [ ] Design a modern racer/profile model that separates save/profile storage from racer identity and supports create/name/customize. Preserve the original forbidden-name detection list only as an Easter egg: show **"COOL NAME!"** and then accept the entered name normally.
- [ ] Preserve every classic named/color racer as an exact preset; decide which also become AI opponents, ghosts or tournament cast.
- [ ] Preserve Bronsen, Silverton and Goldwyn as named opponents independently of any Bronze/Silver/Gold progression redesign.
- [ ] Prototype a simplified modern League/tournament path while keeping the original League flow reproducible in authentic/reference mode.
- [ ] Evaluate performance-based medal awarding or selectable challenge tiers as alternatives to mandatory Bronze → Silver → Gold replay.
- [ ] Add modern per-event/tour persistence unless evidence shows the original session constraint is mechanically meaningful.
- [ ] Replace destructive controller-chord administration with explicit confirmed actions in modern mode while preserving the original behavior for reference.
- [ ] Design a unified records/statistics surface that can embed or reproduce the original score/result presentations rather than erasing them.
- [ ] Make basic controls/status self-explanatory in-game without exposing secrets or advanced discoveries that are intentionally hidden.
- [ ] Record each intentional modern behavior change as product policy and keep it distinct from fidelity fixes/regressions.

### Baseline modern product requirements

Treat these as must-do unless later technical evidence demonstrates a specific blocker.

- [ ] Full controller hot-plug/rebinding support and practical keyboard support.
- [ ] Robust autosave, independent profiles/settings and resumable progression.
- [ ] Instant restart/retry from race, pause and results flows where appropriate.
- [ ] Modern pause menu with resume, restart, options, controls/run data and exit choices.
- [ ] Personal-best and previous-run ghosts using local storage only.
- [ ] Local replay/run-record persistence sufficient to re-drive or review completed runs.
- [ ] Exact timing, lap/split data, PB deltas and medal/target deltas shown alongside preserved original indicators.
- [ ] Practice/free-play route with rapid track selection and repeat attempts.
- [ ] Concise onboarding/tutorial for fundamental controls, landing and stunt-to-speed behavior while preserving secrets/advanced discovery.
- [ ] Accessibility/input presentation options that do not alter authoritative simulation, including remapping, vibration control, readable text support and reduced flashing where applicable.
- [ ] Fast local multiplayer join/setup, rematch and track rotation without legacy League bureaucracy.
- [ ] Authentic/raw-pixel plus modern/HD presentation presets, with optional CRT/NTSC-style display choices where useful.
- [ ] Fast navigation affordances such as recent track, rematch, next event and direct practice access.
- [ ] Localization-ready text/UI architecture.
- [ ] Preserve original attract/demo behavior and leave a clean hook for a local recorded-run showcase.
- [ ] Keep content/data boundaries friendly to future custom courses, local challenge packs and visual packs without making those all launch requirements.

### Decide when subsystem maturity allows

- [ ] Evaluate expanded racer cosmetics beyond name/color and exact classic presets.
- [ ] Evaluate a full replay viewer with scrub/frame-step/camera/HUD controls.
- [ ] Evaluate photo/capture tooling.
- [ ] Evaluate richer local statistics/telemetry views.
- [ ] Evaluate achievements/challenges centered on mastery and discovery rather than grind.
- [ ] Evaluate section/checkpoint-based practice starts after the course/state model is safe enough.
- [ ] Evaluate a simplified local tournament/bracket mode.
- [ ] Decide final modern medal/progression policy after original thresholds/state are mapped.
- [ ] Evaluate a modern attract/demo reel sourced from strong local runs.
- [ ] Evaluate user-facing mod/content-pack affordances beyond planned custom-course tooling.

### Network/hosted-service non-goals

- [ ] Keep ghost/replay/timing/leaderboard/challenge data models transport-agnostic enough for future extension, but implement only useful local behavior.
- [ ] Do **not** implement or provision online multiplayer, matchmaking, hosted/global/friend leaderboards, downloadable ghosts, accounts, daily/weekly services, backend deployment, service credentials or online CI/testing unless project infrastructure changes.

- [x] Pin RetroArch, Libretro Slang shaders and bsnes-hd as visual-reference dependencies without adding them to default CI.
- [x] Define the canonical multi-interpretation upscale/reference strategy in `docs/HD-VISUAL-REFERENCE-PIPELINE.md`.
- [x] Establish the initial coherent-art decision authority in `docs/HD-ART-DIRECTION.md`.
- [ ] Curate the minimal project-owned shader/scaler preset matrix: raw/nearest, ScaleNx, HQx, xBR/xBRZ, SABR, ScaleFX, Super-xBR, selected NTSC and selected CRT references.
- [ ] Prove one deterministic matched-frame RetroArch capture under Linux/headless automation; record exact runtime/backend requirements and cost.
- [ ] Identify offline equivalents for bulk extracted-asset scaling so emulator/frontend startup is avoided where unnecessary.
- [ ] Test bsnes-hd layer/sprite isolation on a concrete Uniracers scene; keep it specialist-only unless the evidence gain is real.
- [ ] When Phase E extraction is ready, generate semantic-asset reference dossiers containing raw data/palette, animation neighbors, geometry anchors/contact points and selected processed interpretations.
- [ ] Add temporal-coherence checks for animated replacement sequences: contour/scale/pivot/contact drift, flicker and inconsistent invented detail.
- [ ] Define deterministic sampling/render policy per presentation class rather than one global host texture filter.
- [ ] Keep all processed images provenance-labelled and subordinate to native ROM/framebuffer evidence.

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
- [x] Audit imported emulator/source snapshots far enough to identify assumptions worth testing. Remaining work is now Phase 4 runtime discrimination, not open-ended source auditing; active-display OAM is the first concrete seam.
- [~] Make an explicit port/defer decision for autonomous race-driving policy. Exact historical SMV replay is preferred wherever prerecorded input suffices; port policy only if state-responsive whole-race coverage adds a capability movies cannot.
- [ ] Review any newly imported executable/script before promoting it into a project-owned dependency.
- [x] Classify and byte-pin the full `references/imported/` corpus; fail CI on unclassified additions, altered mirrors or executable-bit drift.
- [x] Harden `tools/toolchain.json` / `bootstrap_toolchain.py`: argv-only builds, exact pins/origins, clean disposable checkouts, per-tool Python environments, typed artifact verification and hash-pinned project patches.
- [x] Make every automatic toolchain entry smoke-buildable in CI; keep heavyweight GUI/debugger workbenches explicitly manual until a real workflow needs them.
- [x] Establish `tools/tool_interop.json` and `docs/TOOL-INTEROPERABILITY.md` as the producer/consumer and multi-tool-chain authority.
- [~] Fan canonical symbols into every analysis/debugger surface instead of maintaining tool-specific label lists. snes2asm YAML and da65 info seeds are generated; Mesen and Ghidra import remain.
- [x] Add an independent Snes9x vs Beetle/bsnes-derived first-race state route; first successful run establishes a checkpoint-by-checkpoint emulator-variance baseline.
- [~] Prove the shared fixture grammar end-to-end through Mesen/mesen-for-ai. The adapter and ROM-free semantics tests exist; promote the pinned MesenCE Linux runtime, execute the canonical first-race fixture, emit the same named full-WRAM checkpoints, and compare them with the existing tool.
- [ ] Validate a Mesen-CDL compatibility adapter against a small known execution corpus before feeding Mesen coverage into DiztinGUIsh or da65; preserve any non-equivalent flags explicitly.
- [ ] Prove an exact Uniracers graphics round trip through snes2asm → SuperFamiconv → generated reconstruction worktree → WLA-DX before treating SuperFamiconv output as authoritative replacement bytes. This is owned by the main asset-extraction/modern-presentation plan rather than the general audit.
- [x] Audit headless execution/build posture: keep GUI workbenches off default CI, preserve Mesen's upstream Xvfb-backed testrunner route, and restrict automatic builds to CLI/libretro surfaces.
- [x] Trim automatic build scope: cc65 now builds only da65; WLA-DX now builds only wla-65816 + wlalink; Python venv setup no longer upgrades pip unconditionally; fresh Git bootstrap fetches only the pinned commit.
- [ ] Add a fingerprinted safe-reuse/cache mode for repeated same-checkout tool bootstraps only if agent sessions show rebuild time is materially recurring; keep strict clean rebuilds as the CI/default evidence path.

- [x] Pin visual-reference workbenches (RetroArch, Slang shaders, bsnes-hd) as manual/wrapped dependencies so future graphics work does not depend on rediscovering or floating upstream versions.
- [ ] Promote a RetroArch or bsnes-hd command/output contract into `tools/tool_interop.json` only after a real deterministic capture experiment establishes what another project tool can consume.

Audit policy: `docs/THIRD-PARTY-CODE-AUDIT.md`. Remaining closeout scope and explicit defer/transfer rules: `docs/TOOLING-AUDIT-CLOSEOUT.md`.
