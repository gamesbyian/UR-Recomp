# Work Queue

Respect real dependencies, but maximize parallel work across independent leaves. The trustworthy stock baseline is already established for the current Windows x64 product path; do not serialize unrelated product work behind closed research gates.

**How to choose work:** treat the sections below as evidence/status, not equal-priority buckets. The former reverse-engineering critical path through stock fidelity, course/rendering semantics and first shipping Widescreen is substantially closed. The active shipping path is now the **Windows x64 consumer product**: finish the Modern profile/progression experience, fast practice/navigation, run/records/timing presentation, controller/accessibility polish, broad Remastered coverage, and packaging/release acceptance while preserving the closed Authentic regression path. Prefer tasks that remove a player-visible blocker or unlock several of those product slices at once. Historical/acquisition/tooling work is supporting unless it directly blocks that path.

## Agent-ready Windows x64 lanes

The active roadmap should expose several runnable leaves at once. Unless an active branch already owns the same write surface, these are valid **parallel** lanes rather than a serial checklist:

1. **Profile/progression continuation:** **[shipped Continue slice + Restart policy ready]** profile-local unfinished-tour capture/apply survives the stock rider-select wipe, and Windows x64 exposes a fresh-process Continue Tour route that uses ordinary stock menu inputs and stops at the restored tour's TRACK_SELECT surface. The next stacked policy/model now defines explicit Resume Tour / confirmed Restart Tour over that same stock route: Resume alone permits restore; Restart suppresses restore and may retire host continuation only after settled TRACK_SELECT proves the stock row was wiped. Remaining baseline work is thin host/root UX integration plus settled challenge-tier presentation; do not build another persistence, picker or progression model.
2. **Controls/accessibility:** [~] the pinned framework's real rebind/save authority has been confirmed and a pure product rebind state machine now exists for the 12 P1 SNES controls, including capture/cancel, clear, reset and duplicate-key-friendly semantics. Next, after the active shared Modern-host navigation work clears, wire that model into the existing Controls panel using `keybinds_set_button` / `keybinds_reset_player` / `keybinds_save`, add native persistence acceptance, then proceed to hot-plug UX and first non-simulation accessibility options. Do not create another input map.
3. **Timing/statistics presentation:** [~] the Windows x64 slice now shows authoritative live/finish time, compatible PB, exact checkpoint/finish deltas, selected Local Run vs PB, and a first profile-wide Records → Runs/Replays overlay. The Records substrate enumerates valid profile runs once, groups them by authoritative course identity, reuses canonical per-course PB/Previous selectors, and supports course → run-history navigation. Continue with richer post-run detail, permanent top-level Records navigation, and the remaining Tracks / Racers-Profiles / Multiplayer-Tournament views without creating a second records model.
4. **Fast repeat/navigation:** add one-action rematch/repeat-practice and recent/next-event affordances above the already-authoritative Quick Practice/menu-routing machinery.
5. **Racer HD coverage:** choose the next animation family only from measured player-visible Original↔HD fallback frequency, then use the existing equivalence, dossier, temporal and approval pipeline without new archaeology.
6. **Presentation polish:** close the remaining product-overlay/high-density composition policy and deterministic sampling/filter choices without changing guest geometry or simulation cadence.
7. **Release/packaging:** [~] the first Windows x64 consumer-package contract is now a portable extracted folder/ZIP: canonical executable + ROM + rom.cfg + staged mods + launcher/README + SHA-256 manifest. Windows CI assembles and verifies that package, launches it from an unrelated working directory, requires a stock main-menu boot, proves framework config/keybind state anchors beside the package, and retains the assembled package as evidence. Next: complete mutable-data relocation/migration before claiming a Program Files installer, then add explicit startup/error-reporting and upgrade acceptance.
8. **Shared tooling:** centralize repeated validators/persistence helpers/context packets only when a concrete repeated cost has appeared in two or more active lanes.

Keep at least three of these in agent-ready form when possible. If a lane must touch a current shared hotspot owned by another branch, move its pure model/tests/catalog work forward first and leave only the thin integration step blocked.

## Platform portability guardrail

Windows x64 is the primary consumer/reference build. macOS, Web, Switch homebrew and PS5 remain later peer/feasibility targets behind the same simulation/product interfaces. Reject new desktop-only assumptions when an equally small portable seam exists, but **do not assign agents to secondary-platform reconnaissance, compile feasibility or port implementation while unfinished Windows x64 baseline requirements remain**. Platform-specific plans remain reference material for future work, not active queue authorization.

SDL3 is the canonical desktop host backend; SDL2 is fallback-only (`PLATFORM-TARGETS.md`, "SDL backend policy"). Do not write new product/host glue against SDL2-only APIs.

Video settings are now a baseline modern-product requirement: output resolution, display mode, VSync, presentation refresh/FPS target and internal render scale must remain host-owned. Do not implement variable guest simulation rate; high-refresh support is presentation-only and must preserve deterministic authoritative timing.

## Active execution order — 2026-10-05

Canonical capability/readiness status: `docs/SEMANTIC-SUFFICIENCY.md`. Use that scoreboard to decide whether a semantic task is actually blocking a product decision.

The structural-island program has crossed from scarce capability into abundant capability. Do **not** choose another island merely because the frontier ranker can name one. Before opening a new semantic investigation, query the normalized knowledge surfaces in `analysis/data/` and the three retained inference-audit reports. New work should start from the cheapest remaining falsifier, not from scattered prose or a fresh corpus sweep.

The active ordering is now:

1. **[shipped] Widescreen (16:9, 342×224).** 1P, ordinary 2P and VS races widen through host-presented, per-viewport course-model margins. Frontend, pre-race and results scenes stay centred. Gates: stock-parity centre and WRAM confinement (`tools/check_widescreen_product_parity.py`, native smoke), and the 4:3 regression frame identity plus the sprite-rip margin check (`widescreen-4x3-regression.yml`). Per-domain widths live in `analysis/widescreen-policy.yml` `domain_widths`; the evidence chain is R-2026-10-04-UI-29/30/31 and R-2026-10-05-UI-32/33. Remaining Phase 8 work is the reconnaissance tooling below. Earlier +8 hook and materializer history: `docs/WIDESCREEN-RECONNAISSANCE.md` § Retired queue entries.
2. **Keep the finite stock-fidelity matrix closed.** Representative 1P movement/stunt/contact/finish, ordinary 2P isolated + simultaneous input, VS, the active-display OAM seam, and progression-changing save/load are now durable. Run `37055966541` proves gameplay-authored Crawler bronze `0→1`, model-valid tier state, checksum-valid SRAM, and byte-for-byte fresh-process reload. Reopen this lane only for a concrete new fidelity counterexample.
3. **Use the consolidated course/resource model, not ad hoc course archaeology.** `analysis/data/course-corpus.json` is the canonical 45-course identity/geometry surface; `course-resource-catalog.json` owns promoted resource semantics and conserved bundles. The corpus is six fixed-area geometry families, Dessyreqt track IDs equal stream index minus one, and header coordinate pairs are strongly constrained as paired racer spawns at ×16 scale. Use the six-shape representative matrix for generalization; reopen broad course decoding only on a product-facing contradiction.
4. **Racer HD semantics and first shipping families are product-sufficient; expand by measured player-visible value.** The composition-aware runtime identity, OAM placement/orientation, true-density host compositor, fail-closed Original fallback, dossier/review tooling, temporal-coherence gate and hash-bound shipping approval path are all established. The original retained `1205–1220` strip and the later bounded families at `1305–1306`, `1244–1252`, `1230–1239` and `1261–1267` are shipping-approved under their exact provenance manifests. Runtime registrations may remain distinct even when stock raster evidence proves one visual pose; exact-raster and palette-equivalent variants must reuse canonical authored geometry through the deduplication contract in `HD-ART-DIRECTION.md` / `HD-VISUAL-REFERENCE-PIPELINE.md`. Do not resume adjacency archaeology or create per-state art merely to increase registration count. Choose the next family by measured Original/HD fallback frequency or another concrete player-visible product requirement. Canonical semantic/query state lives in `analysis/data/presentation-assets.json`; shipping approval manifests and generated review evidence own the detailed frame/run history.
5. **[shipped] Modern pause/Restart command path.** Results-safe Retry preserves live SRAM across rollback, repeated Retry restores one immutable race-entry anchor, and keyboard/controller pause navigation is integrated through the host-owned session API without guest input synthesis. The production pause surface now includes Resume/Restart, Options, Controls, Run Data, Exit Frontend and confirmed Quit; remaining work belongs to the specific product surfaces below rather than to Restart plumbing.
6. **Apply inference-first task admission across the repo.** `analysis/data/state-schema.json`, `code-semantics.json`, `presentation-assets.json`, `fixture-corpus.json`, and `evidence-claims.json` are the default query surfaces. Use `analysis/generated/inference-audit*.{json,md}` to avoid rediscovering closed relationships. If a needed fact is missing, extend the consolidation builder or add an explicitly provenance-bearing dataset instead of creating another isolated ledger.
### New structural-island admission rule

A new island is P0 only when it does at least one of the following:

- closes a known fidelity uncertainty;
- unlocks a concrete Widescreen/rendering/course requirement;
- connects or disambiguates an already high-value causal chain;
- supplies a cheap reusable semantic anchor with clear downstream leverage.

Generic frontier score, bounded-byte growth, analyzer cleanliness, or geographical adjacency in ROM are not sufficient reasons by themselves.

For each proposed island, state: **decision changed**, **downstream gate**, **cheapest discriminator**, **success condition**, and **stop condition**. If those cannot be named, choose another task.

### Queue maintenance rule

`WORK-QUEUE.md` is an execution surface, not the permanent home for every completed investigation. New completed-island detail should preferentially live in the structural census/generated report and `RESEARCH-LEDGER.md`; keep only enough summary here to prevent repeated work and explain current dependencies. Existing historical detail can be compacted opportunistically in a dedicated cleanup, not mixed into active technical PRs.

## Priority 0 — Fidelity divergence + semantic decompilation

**This remains a supporting P0 workstream, but broad semantic expansion is no longer the default highest-leverage action.** The native game boots, reaches races, the core offline toolchain is proven, and repeated structural recovery is now routine. Prioritize semantic work only when it advances the active execution order above.

Current admission rules:

1. **Reopen fidelity only on a meaningful semantic counterexample.** Event-relative 1P/2P/VS fixtures already cover the principal movement, stunt, contact, finish, frontend-text and progression paths. Pre-race scratch-byte differences and absolute-frame phase shifts are not debt unless they change a player-visible or authoritative semantic outcome. The 2014 SMV mismatch is retained as a timing-alignment lead only if frame-exact historical replay becomes a product requirement.
2. **Indirect/analyzer target discovery is bounded.** The known `80:C3C8`, `00:8584` and `00:8599` sites have explicit finite target sets. Reopen target logging only for a concrete fidelity/AOT question.
3. **The original core anchors are resolved.** Reset, main loop, racer update, course materialization and racer OAM construction are known. Add semantics only when a current product, renderer, course-tooling or discrepancy question needs them.
4. **Comparative-ROM structure is a query surface, not a coverage contest.** The normalized census now spans 132 regions / 21,836 bounded USA bytes across high-value race/course/collision/camera/stunt/input/render/control corridors with regional homologues where established. Start from `analysis/generated/comparative-structural-census.{json,md}`, `cross-build-symbol-correspondence.*`, the WRAM motion atlas and `analysis/data/`; admit a new island only when its answer changes a decision or closes a concrete uncertainty.
5. **Multiplayer fidelity is closed as a default lane.** Deterministic VS/ordinary-2P fixtures, paired-racer semantics, simultaneous input, active-display OAM and save isolation are durable. Do not reopen the historical one-unit X-speed/absolute-frame symptom without a new race-relative semantic mismatch.
6. **Use the cheapest falsifier before new decompilation.** Query the consolidated evidence and inference reports first. If a required fact is absent, prefer one bounded perturbation/trace or a normalized dataset extension over another broad analyzer sweep.

Do not chase semantic completeness uniformly. Prioritize code that is executed, divergent, hardware-facing, or a dependency of physics/course/rendering behavior.

### Semantic propagation pass

A high-confidence semantic discovery is not finished when it is named or documented. Before closing the discovery, perform a **bounded propagation pass** when doing so can illuminate the shipping critical path:

1. enumerate direct readers, writers, callers, callees, pointers and referenced tables;
2. look for sibling structures and repeated access patterns, especially P1/P2, current-player/stable-player, adjacent fields, parallel tables and structurally similar routines;
3. propagate the label across comparative-ROM matches only where structural evidence supports it, preserving provenance and confidence;
4. test whether the new meaning resolves or constrains an existing decompilation gap, fidelity mismatch, course/rendering unknown, or recovered-source ambiguity;
5. turn useful consequences into the existing authoritative surfaces: `SYMBOLS.md`, research-ledger entries, comparative-atlas metadata, fixtures, parsers, tests, or the owning queue item;
6. record promising downstream hypotheses only when there is a cheap discriminator or concrete implementation decision they can affect.

Treat this as semantic **fan-out**, not an invitation to recursively reverse engineer everything nearby. Apply the value-of-information rule at each hop and stop when the next expansion would no longer change a current decision, unlock downstream work, or produce cheap reusable knowledge.

### Community / AI reverse-engineering accelerants

Use `docs/AI-ASSISTED-REVERSE-ENGINEERING.md` as method guidance while working the critical path. These are optional accelerants, not new blocking milestones:

- [~] Controller-poll/replay boundary is narrowed on PR #133: native and `snesref` apply frame N's mask immediately before guest frame N, and the dense VS race-entry microtrace matches under a common observation schedule. Merge/promote that branch's documentation when its active-movement parity gate completes; do not restart this investigation from scratch.
- [x] Trial execution-coverage/CDL deltas on one already-understood causal A/B pair. Run `36940956374` compares timing-identical jump-control vs 48-frame B-held fixtures and narrows ~33.8k executed code bytes to 94 variant-only bytes in seven compact ranges (plus 14 control-only bytes), including the exact pressed-B decoder arm at `02:AADF..AAE5`. Retain CDL as a bounded semantic-search accelerant when a controlled A/B fixture exists; intersect the small delta with symbols/xrefs/writers rather than treating coverage as causal completeness.
- [ ] When an important routine remains opaque after targeted tracing, use a bounded one-variable perturbation matrix from a shared checkpoint and cluster outcomes/first divergences before attempting broader decompilation.
- [ ] For future Ghidra-heavy passes, stabilize processor context/signatures/types before semantic naming/comments, then finish with a mechanical contradiction/falsification check. Do not add a new Ghidra dependency unless existing pinned/manual surfaces cannot support the needed experiment.
- [x] Run the trusted semantic-anchor set through `tools/compare_semantic_anchors.py` across all four ROMs and build the bounded WRAM motion atlas. Run `36807393022` confirms the recurring PAL/Europe displacement families and finds no contradictory repeated-field projections in the accepted corpus. Next comparative priority is the 486-byte USA/beta cross-analyzer classification corpus; keep weak Europe checkpoint/HUD and other weak-retention candidates unpromoted until another local discriminator agrees.


## Infrastructure maintenance — Island / offline toolchain

Canonical execution plan: `docs/ISLAND-TOOLCHAIN-PLAN.md`.

The core no-network proof is complete: run `36791326251` successfully built the vendored Snes9x reference core, staged repository-owned SNESRecomp, generated the canonical project, and built `UniracersSNESRecomp` inside a network namespace. Islandization no longer preempts game research; remaining cleanup is maintenance unless a concrete toolchain defect blocks work.

- [x] Add the `third_party/` provenance/licensing/manifest infrastructure, repository-hygiene validation, local-source bootstrap preference, and fail-closed offline mode. A true network-disabled build smoke follows the first islanded core component.
- [x] Vendor the small/high-value tool tranche and package-registry closures. `mesen-for-ai`, `snes2asm` plus PyYAML 6.0.3, SuperFamiconv plus its Cargo closure, `ghidra-snes`, pruned Flips CLI, and Beetle/bsnes libretro are repository-owned and proven through fail-closed offline bootstrap. Beetle's libretro SRAM export and teardown defects were subsequently corrected by the narrow project-owned patch merged in #55, with exact 8 KiB SRAM roundtrip and clean teardown now permanent regressions. P0-B is closed.
- [x] Migrate SNESRecomp and the core reference/build dependencies needed by the canonical lane. C1-C4, the reduced Snes9x/`snesref` closure, repository-owned framework staging, and the SDL2 host boundary are implemented. Network-disabled run `36791326251` proves canonical generation and native build with GitHub/PyPI/crates.io physically unreachable.
- [ ] Preserve large/manual workbenches as exact archives or optional external tools where direct vendoring has poor value.
- [x] Prove a network-disabled core workflow before removing old fetch paths. Run `36791326251` is the green proof. Remove obsolete fallbacks only when doing so is low-risk and does not distract from current fidelity/decomp work.
- [ ] Use repository ownership to customize/optimize tools for UR-Recomp where measured value justifies divergence from upstream.

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
- [x] Finish a stock race deterministically. The project-owned Dragster route reaches stock results in both native and pinned Snes9x. Run `36801728342` extends the earlier green finish proof with exact paired checkpoint/gate/lap parity: P1/P2 progress from checkpoint/gate/laps `0/0/2` to `1/1/1`, later `3/0/1`, and results at `1/1/0`; every sampled racer-state checkpoint also matches. This closes the 1P finish mechanism without extra capture volume. The old 2014 pre-race absolute-frame mismatch remains reclassified as frontend/timing reuse.
- [x] No product feature on the accepted Windows path requires changing authoritative guest simulation. Modern/Widescreen/HD features remain host/presentation policy, with Authentic regression coverage retained.

**Exit:** complete a stock race in 4:3.

## Phase 4 — Emulator-compatibility seams

Convert known historical Uniracers emulator fixes into local understanding and permanent regression coverage. Keep the seams separate rather than treating every problem as the OAM quirk.

### Active-display OAM / sprite ripping

- [x] The canonical Uniracers active-display OAM seam is product-sufficient in the current runtime. Deterministic split-screen/VS coverage captures the scanline-0/112 `$2104` HDMA behavior and the accepted Authentic/Modern paths retain the stock sprite-ripping result. A broader emulator-theory classification of every possible 1P/2P occurrence is not required unless a concrete rendering counterexample appears.
- [x] Trace writes to `$2104` and verify expected scanline/value behavior. The durable VS regression reproduces HDMA `$2104 <- $A5` at scanline 0 and `$2104 <- $5A` at scanline 112 at every sampled stable race checkpoint; the source table is `7E:206C = 70 A5 70 5A 00`.
- [x] Verify the effective high-OAM target and sprites 96-99. Stable race snapshots end with `OAM[0x218] = 0x5A`; independent Snes9x/MAME/jgenesis/SNESdev evidence identifies `0x218` as the active-display destination. High-table byte index `0x18` controls sprites 96-99, and the project decoder verifies the `$A5/$5A` two-bit pair swap.
- [x] Disassemble the recovered Canoe patch hooks at `0x01534C` and `0x015714` plus injected handler at `0x1FFF00`. Run 36670381748 plus the permanent semantic decoder/test reconstruct all seven IPS records, both injected entry points, both synthetic HDMA tables and their dynamic cross-links; see `docs/CANOE-COMPATIBILITY-PATCH.md`.
- [x] Compare unpatched behavior, Canoe workaround, Snes9x special case, MAME/jgenesis models and bsnes/ares reference behavior. The source-model comparison is now explicit in `docs/CANOE-COMPATIBILITY-PATCH.md`: pinned Snes9x applies a Uniracers-specific HDMA hack forcing `OAMAddr=0x10C`; MAME generically redirects active-display OAM writes to physical `0x218` as an acknowledged approximation; ares and jgenesis instead derive the destination from live sprite evaluation/fetch state. All converge on the observed VS destination while differing on generality.
- [x] `tools/compare_active_oam_models.py` already captures the smallest useful model discriminator. A synthetic live-index runtime fixture would answer a general SNES-emulation question, not a current Uniracers product question, so it is deferred unless a real game fixture exposes an OAM mismatch. If that happens, prefer a correct general SNES behavior fix to a title-specific hack.

### Other historically exposed seams

- [x] LoROM SRAM mapping: run 36661148644 extracts the historical 2008 movie's known-valid 8 KiB SRAM image (SHA-256 `15650bb496292c6fc9c1ea35f8b26070d8c1617169fbe75be3c0482d98649fd1`) and proves exact preload→dump byte identity under both pinned Snes9x and the repository-owned Beetle core. Beetle now exposes `RETRO_MEMORY_SAVE_RAM` as 8192 bytes and exits cleanly after the fixture. Toolchain run 36661148675 independently proves the narrow compatibility patch in the ordinary fail-closed offline matrix.
- [x] XOR/window-area logic: run 36658348552 isolates the ordinary one-player `race-entered` checkpoint at frame 1035 as the only sampled XOR-active scene; BG1-4, OBJ and color all have both windows enabled with XOR logic, while the sampled frontend and stable VS checkpoints are negative controls. The permanent workflow now requires the XOR-active checkpoint set to remain exactly `{race-entered}`.
- [x] Color math / empty-subscreen behavior: canonical scene survey plus historical fallback A/B are complete. Frontend states use `CGWSEL=02`, `CGADSUB=7F`, `TS=10`, while active race changes to `CGADSUB=04` and fixed red=15. The historical backdrop-for-empty-subscreen perturbation changes ~97-99% of several frontend frames, 0 pixels on Rider Select, and only 392 pixels in a narrow race band; reject any title-wide compatibility fallback and preserve per-pixel SNES color-math semantics. Evidence: `analysis/generated/color-math-scene-survey.json` and `analysis/generated/color-math-fallback-ab.json`.
- [x] Race-start/post-start graphics: locally reduced from the historical Xe failure to the race presentation bring-up boundary. NOW PLAYING-relative captures stay cross-core pixel-identical and black through +140; Snes9x then enters the established race XOR/color-math regime before visible pixels appear. An `inRace=1`-aligned capture stays cross-core pixel-identical through +12, with Snes9x color-math switching by +8 and visible output beginning around +16; after onset the two healthy cores are not pixel-phase synchronized, so settled semantic fixtures remain the cross-core oracle. See `analysis/generated/race-visible-onset-*.json` and the emulator compatibility note.
- [~] Compatibility-seam documentation is sufficient for product work: the OAM, SRAM, XOR/window, color-math and race-visible-onset evidence already has permanent docs/generated artifacts/tests. Add research-ledger cross-links opportunistically when touching those surfaces; do not assign an agent solely to re-record the same conclusions.

**Exit:** the known historical Uniracers emulator compatibility problems are either reproduced and covered by deterministic tests or explicitly shown not to apply to the canonical runtime.

## Recovered autonomous-player accelerator

- [x] Locate public source for Dessyreqt's 2014 full-game real-time Uniracers bot (Pastebin `A0XpKw9v`).
- [x] Preserve the source and submitted #4250 SMV in the repository with hashes/provenance.
- [x] Preserve the recovered **USJO lineage**: exact v8 plus Dessyreqt's v14/v14a/backup/test descendants. V13 is now passive historical gap-filling only; newer surviving code is already local.
- [x] The recovered v8 bot has been inventoried to the level needed as a product/research accelerator. Static extraction is reproducible in `analysis/generated/usjo8-static-inventory.{json,md}`; further dynamic promotion is on-demand only when a specific stunt/boost/product question needs one of those labels.
- [x] The bot's key RAM labels are sufficiently reconciled for current use through the validation matrix, writer scans, deterministic runtime evidence and Nitrodon correspondence. Twist/Z-flip/roll/flip micro-semantics and exact boost-unit interpretation are not open shipping questions; recover them only if a concrete gameplay/statistics feature needs them.

- [~] Mine and operationalize the recovered **Nitrodon reverse-engineering workspace**. First reconciliation is complete in `reference/notes/nitrodon-reverse-engineering-mining.md` and `analysis/generated/nitrodon-reconciliation.json`: tabletop is corrected to duration/progress; roll/flip/Z-flip/tabletop widths and shared current-player velocity/boost slots are reconciled; stunt finalization at `02:9A42`, vertical acceleration at `02:A968`, and controller decode at `02:AA6E` are now canonical symbol seeds; and the exact base-5 four-stunt combination index feeding the 625-byte table at `02:9DAA` is documented. Completed propagation has now closed stable boost copy boundaries `11CF/11D1 ↔ 11CD`, confirmed `1199/119D/0EF1` through deterministic Dragster finish, and reconciled historical course addresses with exact RNC boundaries. Completed propagation has also identified runtime course-object code `0x14` as checkpoint/finish behavior and reclassified `bounce tracelog.txt` as a bounded collision-shape + 2×2 velocity-transform fixture. Next: trace the ROM-side message-queue consumer to close delayed boost units, decode `FE/FF` table sentinels, trace stunt score `12AF`, run the new 45-course resource-list/fingerprint analyzer, then generalize Dragster's confirmed checkpoint resource (`0x24` on USA Dragster) by structural incidence/descriptor/output/behavior fingerprints rather than assuming numeric IDs or absolute addresses remain stable, and replay the recovered bounce case only when collision fidelity work needs it.

- [~] Mine and operationalize the recovered **Dessyreqt historical workspace**. First corpus/lineage pass is complete in `reference/notes/dessyreqt-workspace-mining.md` and `analysis/generated/dessyreqt-workspace-index.json`: 80 files; movement→stunt→full-game bot lineage; USJO v14/v14a; queue-aware boost accounting; complete 45-map visual corpus; paired-racer leads; and nine glitch SMVs. V14a's 16-bit boost/queued-message model has now been connected to the ROM's real 32-entry stunt-message ring, and P2 position/speed leads have been structurally promoted through the common racer-update workspace. Next high-value uses: (1) trace the ROM-side queue consumer into boost mutation; (2) add one recovered Jumpover SMV as a collision-boundary regression after ordinary race fidelity is trustworthy; (3) use `magicnumber.lua` start/finish coordinates as cheap course-selector/finish probes. Do not spend time porting old policy where exact movies suffice.

- [x] Run one **controlled save-format/progression discriminator** before any broad SRAM reverse engineering. Run `37055966541` closes this with a real gameplay-authored Crawler bronze `0→1`; `analysis/generated/progression-sram-acceptance.json` confirms the model update, unchanged-but-correct tier 0 state, valid stock checksum, and exact 8 KiB persistence after fresh-process reload. The earlier bounded failures remain retained negative evidence rather than discarded attempts.
- [x] Port the clean menu-driving route into the shared native/snesref deterministic input harness through race entry.
- [x] Exact historical input plus current deterministic fixtures are sufficient regression workloads. The old frame-440 symptom has been reclassified by later event-relative fidelity work and does not justify porting the state-responsive bot policy. Revisit autonomous policy only if soak/fuzz coverage becomes a concrete release need.

## Phase 5 — Differential validation

Use `snesref` or another trustworthy reference route.

- [x] Deterministic input sequence to first race, shared verbatim by native and snesref.
- [x] Full-WRAM/state checkpoint comparison across native and Snes9x/snesref. The first-race fixture compares all 128 KiB at seven checkpoints and reduces the settled-race difference to seven bytes.
- [x] First-divergence workflow for the settled first-race checkpoint. Run 36511207129 resolves `$01D1–$01D4` as stale stack residue (`SP=$01FF`, `E=false`, no ordinary WRAM writers) and `$00C6/$00C8/$00C9` as free-running timing/phase counters. There is no remaining unexplained persistent gameplay-state divergence in this checkpoint.
- [x] Establish a backward-compatible neutral P1/P2 controller stream (`start:duration:p1-mask[:p2-mask]`) plus native-Lua and Mesen writers; preserve all historical three-field P1 corpora unchanged. Keep the pinned `snesref` P2 delta as a project patch until equivalent support is upstream.
- [x] P2 transport, ordinary 2P/VS simultaneous-input semantics and the representative race fidelity matrix are sufficient for the current product path. Existing deterministic fixtures and exact historical movies are preferred over porting the old adaptive bot. Add a new soak/bot fixture only when it detects a release risk that the retained finite matrix cannot cover.

**Exit:** fidelity is objectively testable.

## Phase 6 — Reverse-engineering map

Prioritize: main loop, input, race state, player physics, camera, course loader, RNC decompression, course representation, sprite/OAM construction, culling, HUD and audio hooks.

Maintain `SYMBOLS.md` and `RESEARCH-LEDGER.md`. `tools/export_symbols.py` generates `analysis/generated/symbols.json`; repository hygiene fails if the machine-readable export is stale.

- [x] The multi-ROM/analyzer atlas is established as reusable infrastructure rather than an unfinished coverage program. The comparative census, cross-build correspondence, inference/query surfaces and current analyzer contracts are sufficient to answer product-driven questions. Triage disagreements, propagate semantics and measure additional coverage only for a named downstream decision; do not assign agents to improve atlas completeness as a metric.

- [~] CPU audio package archaeology: `02:812A` is confirmed to resolve a contiguous length-prefixed record pool beyond the package-table-only `0x00..0x31` prefix; direct setup calls reach records through at least `0x42`. Records `0x3B` and `0x3D` uniquely byte-match the two preserved unused-song SPCs and are the only missing setup selectors in `0x38..0x42`. TCRF independently reports title-screen PAR substitutions selecting `$3B` and `$3D` for its two unused tracks, corroborating those selector identities; retain the reported surrounding package/setup patch semantics as secondary-source leads until locally reproduced. Full `0x00..0x31` package/SPC correlation run 36777071311 now closes the package ranking: excluding only 22-byte block `0x00`, which is below the correlator's 32-byte minimum, known reachable mappings are reproduced exactly and Unused Song 1 has the same 18-block signature as Demo package `03:FB15`, while Unused Song 2 has the same 23-block signature as race package `03:FB55`. The `0x3B/0x3C` near-duplicate keeps `03:FC15` as a sequence-sibling control for `0x3B`; orphan `03:FB95` remains a dormant-table control rather than a preferred song package. See `analysis/generated/audio-unused-path-analysis.md` and `analysis/generated/audio-record-pool-reconciliation.md`. `tools/patch_unused_audio_counterfactual.py` now provides fail-closed one-byte ROM substitutions for the primary causal tests (`0x38→0x3B` while retaining `FB15`, and first-race `0x3E→0x3D` while retaining `FB55`), with surrounding upload/package call bytes verified and unit-tested.

## Phase 7 — Course format

- [~] All 45 Method-1 course payloads are located, fingerprinted and independently decompressed. The unresolved selector/pointer/index encoding is **editor-only deferred debt**, not a Windows shipping blocker: the current product already has canonical 45-course identity, runtime course selection and presentation/resource lookup. Recover the encoding when Phase 10 needs arbitrary custom-course serialization or a concrete contradiction appears.
- [x] Verify RNC Method 1 corpus and independently decompress all 45 streams with CRC validation.
- [~] Reconstruct dimensions and primitives. Header bytes 13/14 form a confirmed 45/45 fixed-area invariant; on representative Dragster, runtime code resolves `00 04` to a 1024×16 grid of 64-unit coarse sectors, a 65536×1024 world domain, a 16,384-entry u16 sector→record table at `7F:000F`, and 32×32-byte 4×4 fine-cell records at `7F:800F`. LE16@11 is the mutable tail/resource cursor. Packed control bits beyond the proven materialized-resource selection path remain editor-only debt unless a product question needs them.
- [~] Produce structural documentation. `docs/COURSE-FORMAT.md` and the generated Dragster presentation contract now cover the representative Widescreen-facing spatial/resource model; full editor-format documentation remains deferred.
- [~] Build parser/tooling around the canonical ROM. `tools/build_course_presentation_contract.py` deterministically maps Dragster world rectangles to coarse sectors, fine records, packed surface words, C000 slots, A000 blocks and owning resources. Generalize by invariant check, not by automatic 45-course expansion.

## Phase 8 — Widescreen

Widescreen is shipped for the supported 1P/ordinary-2P/VS race scenes. The remaining entries in this section are retained diagnostic/reference capabilities, not prerequisites for further Windows product work. Reopen reconnaissance only for a concrete scene/aspect-ratio counterexample. Canonical historical contract: `docs/WIDESCREEN-RECONNAISSANCE.md`.

- [x] Pin and summarize concrete widescreen/recomp prior art without turning it into implementation authority.
- [x] Seed machine-readable widescreen domain/scene/probe vocabulary in `analysis/widescreen-policy.yml`.
- [~] A deterministic bsnes-hd diagnostic/preset matrix remains optional specialist tooling; current Widescreen acceptance does not depend on it.
- [x] `tools/widescreen_probe.py` exists and already supplies retained margin/geometry diagnostics such as `derive-margin`; do not create a second probe harness.
- [x] Classify representative title/frontend, pre-race, one-player, results, two-player and Vs. scenes by explicit presentation policy. 1P, ordinary 2P and VS races widen with host-presented per-viewport course-model margins and stock-parity gates (R-2026-10-04-UI-29/30); title/frontend, pre-race and results stay centred.
- [x] Separate simulation/activation, preparation/streaming, render/culling, camera/composition and UI-composition widths. `analysis/widescreen-policy.yml` `domain_widths` records the shipped race: only render/culling is 342 px. Simulation, guest streaming, camera and UI stay at the stock 256, and margin tiles come from the course model. Each width cites its evidence; `tests/unit/test_widescreen_domain_widths.py` enforces it.
- [~] Validate the accepted viewport/PAR/overscan architecture in `docs/DISPLAY-PRESENTATION-POLICY.md`: separate Display Geometry and View axes remain mandatory. Official-manual screenshot geometry now supports 7:6 horizontal PAR for Authentic presentation and rejects raw 8:7 as the historical display shape within the retained uncertainty envelope. The title-specific logical transform is pinned at full 224 lines and 7:6 PAR. `tools/widescreen_probe.py derive-margin` fixes the accepted 16:9 geometry at exact +42⅔ source pixels per side, exposed as +43 / 342×224 over +48 provider backing. Scene-aware `prepare_frame` / `compute_viewport` binding, dynamic native-wide PPU activation, and the accepted +48 ordinary-race materializer are now part of the ordinary generated product path. The persisted Modern Options `VIEW` setting now exposes Original and 16:9, with Original defaulting fail-closed and Authentic mode inert. The product path is integrated end to end for supported 1P/ordinary-2P/VS race scenes. There is no generic remaining capacity task; do not reopen PAR/overscan or provider-depth work without a concrete counterexample.
- [x] Widen render/culling paths deliberately while keeping stock simulation timing unchanged. BG1 margins are host-presented per viewport band and BG2 wraps statically (UI-29/30). Sprites keep stock culling by decision; the split-screen rip stays clear of the margin (UI-32), and no margin-only object reaches the picture (UI-33). With Widescreen off the program is frame-identical, and with it on guest WRAM stays confined at every parity checkpoint (UI-31).
- [x] Measure object/opponent/event information exposure between matched 4:3 and 16:9 runs. No opponent or object ever appears wholly in a margin in the final picture; racers only extend past the stock edge (1P left, 135/916 frames; two-player right, 2/3,001). The 43 px margin shows the course about 3 frames earlier at race speed. A parked slot-0 sprite draws in the left margin but stays behind the opaque BG2. See R-2026-10-05-UI-33, `tools/measure_widescreen_exposure.py` and `analysis/widescreen-exposure-evidence.json`.
- [x] Exercise player-1/player-2 split-screen and Vs. behavior independently, including the authentic sprite-ripping path. Each viewport is its own calibrated margin band, and VS/two-player checkpoints are centre-identical to Original (R-2026-10-04-UI-30). With Widescreen off, the split routes are frame-identical to the baseline (UI-31). Across 11,158 split frames, the rip's hidden sprite copies never reach the 43 px margin and keep ≥69 px clearance (UI-32, gated by `tools/check_split_sprite_rip_margin.py`).
- [x] Preserve bit-identical 4:3 regression mode. With Widescreen off, the product is bit-identical, frame by frame, to the same seeded program without the presentation layer on the 1P, VS and ordinary-2P routes. `widescreen-4x3-regression.yml` gates this (R-2026-10-04-UI-31). The AOT seed itself shifts tier timing against an unseeded, interpreter-heavy build; that is recorded there as a framework property, not a Widescreen effect.

## Phase 9 — Modern presentation

Optional authentic scaling, arbitrary windows, 16:9/ultrawide, high-resolution UI and replacement presentation layers.

### Frontend modernization / subtraction

Do this from the verified original UI state map, not from memory or generic modern-UI assumptions.

- [x] Classify original frontend states/features as presentation artifact, gameplay mechanic, or administrative/hardware-era system. `analysis/frontend-modernization-policy.json` covers every conceptual state with 30 features. Presentation/mechanics remain preserve-or-augment, and all currently identified administrative Modern redesigns now have explicit decided policy. `tools/validate_frontend_modernization_policy.py` enforces this; edit the policy file when a product decision changes rather than re-deriving it.
- [ ] Preserve every original audiovisual indicator by default; add clearer labels, values, deltas or expanded views alongside it rather than deleting it.
- [x] The reusable stock menu visual-language contract is sufficient for Modern UI work. Typography, palette, layout, cursor motion/easing, MAIN_MENU↔OPTIONS transition, rider/tour/track setup strip, both relevant fonts, menu SFX timing, records/results composition and UI-event sound identities are already measured in `analysis/generated/menu-visual-language.json`, `analysis/generated/menu-sfx-ids.json` and `UI-STATE-MAP.md`. Do not schedule another frontend capture survey unless a specific Modern surface lacks an answer.
- [x] Design a modern racer/profile model that separates save/profile storage from racer identity and supports create/name/customize. Shipping Windows Modern now has an independent profile catalog, exact classic rider presets, create/select/rename, controller preset creation/selection, isolated SRAM/run/ghost namespaces, stock rider-select projection, and the original forbidden-name table retained only as the accepted **"COOL NAME!"** Easter egg.
- [x] Preserve every classic named/color racer as an exact preset. `analysis/generated/legacy-cast-presets.json` already closes the factual corpus for all 16 racers: identity, select slot, medal column and exact race palette, with byte-exact icon/palette checks. Do not invent new canonical personalities for the 16 classic racers. Bronsen, Silvia, Goldwyn and ANTI-UNI retain the canonical opponent roles; recorded ghosts reflect the profile/racer that produced them. Optional later CPU/tournament reuse is content reuse, not new canon.
- [x] Bronsen, Silvia and Goldwyn are established stock named opponents, with ANTI-UNI as the Hunter exception; rider indices, palette assets and medal-tier selection are sufficiently proven for preservation. No broader opponent survey is required before Modern progression/tournament design.
- [ ] Implement the decided Modern Local Tournament flow while keeping stock League reproducible in Authentic mode: choose participants, event/track pool and format; default to round-robin/points play; persist an active tournament automatically; reuse original League standings as a presentation view.
- [~] Implement the decided Modern medal/challenge policy: the pure tier/opponent/completion contract is now defined and tested (Bronze/Silver/Gold; BRONSEN/SILVIA/GOLDWYN; Hunter→ANTI-UNI; higher-tier completion satisfies lower tiers; Authentic remains one-generation-at-a-time). Player-facing non-current-tier selection is blocked only on a narrow title-owned challenge-generation adapter: prove the minimum stock initialization seam that can present the selected generation without pre-granting persistent medal/checksum state, then fresh-process-accept the resulting canonical opponent/race and checksum-valid completion.
- [~] Implement decided Modern tour resume. Persist the current tour, completed-event state and selected racer/profile through the host-owned profile substrate, expose Resume Tour and Restart Tour, and survive process exit/rider re-entry without changing stock guest semantics. Authentic mode retains stock unfinished-tour loss.
- [ ] Replace destructive controller-chord administration with explicit confirmed actions in modern mode while preserving the original behavior for reference.
- [ ] Build the decided unified Records browser from the already-decoded stock rider stats, VS tally, top-3 track records and completed-run/PB data. Organize it around Tracks, Racers/Profiles, Runs/Replays and Multiplayer/Tournament; retain the original tables as Classic Tables/embedded views. Additional stock-memory discovery is not a prerequisite.
- [x] Make basic controls/status self-explanatory in-game without exposing secrets or advanced discoveries that are intentionally hidden. First-run Help plus F1 reopen now explains movement, jump, landing and stunt-to-speed behavior from live control bindings while deliberately preserving cheats, gold-tour vignettes, Hunter rewards and other advanced discoveries.
- [ ] Record each intentional modern behavior change as product policy and keep it distinct from fidelity fixes/regressions.

### Baseline modern product requirements

Treat these as must-do unless later technical evidence demonstrates a specific blocker.

- [ ] Full controller hot-plug/rebinding support and practical keyboard support.
- [~] Robust autosave, independent profiles/settings and resumable progression. Global settings remain durably persisted through host-state schema v6. Independent Modern profile storage now has its own versioned file contract, atomic replace-on-success writes, per-profile autosave generation, and an optional exact 8 KiB stock-SRAM mirror exposed only through Modern-only capture/restore calls. Fresh-process reload, legacy migration, malformed-state rejection and Authentic inertness are acceptance-gated. The next slice is lifecycle integration: capture/apply the profile mirror at controlled Modern boundaries and add host-owned tour/event continuation that survives the stock rider-select wipe.
- [x] Instant restart/retry from race, pause and results flows where appropriate. The accepted player-input path is now promoted into the ordinary generated native product host; Authentic mode remains available through host policy.
- [~] Modern pause menu: Resume/Restart, keyboard/controller parity and the production host overlay are implemented. Root navigation exposes Options/Controls/Run Data/Exit Frontend/Quit; Options contains persisted Focus Pause, desktop Display Mode, VSync, Presentation FPS, Output Resolution, Widescreen view and 1x–4x Internal Render Scale rows driven by one shared keyboard/controller cursor model. Output Resolution consumes the real active-monitor catalog and applies only in exclusive Fullscreen; Internal Render Scale independently controls Racer HD compositor density without changing guest geometry. Active Widescreen world expansion and logical-coordinate product overlays deliberately resolve to 1x until those compositors own widened/density-aware surfaces. Frozen-frame/blend staging is sized through 4x. Logical-coordinate onboarding/practice/pause/results overlays now explicitly force 1x until they own density-aware drawing, and native smoke persists 2x, requires a real 512×448 registered Racer HD draw, validates it through the shared `tools/check_ppm.py`, and retains the frame/log/state artifacts. Richer run statistics/splits and additional proven settings remain.
- [~] Personal-best and previous-run ghosts using local storage only. Previous/PB selection, per-profile target policy, checksum-bound `.urghost` traces, live-camera projection and the first visible Modern 1P presentation-only renderer are implemented. Remaining work is product polish/local ghost management, not another trajectory or simulation model.
- [x] Local replay/run-record persistence sufficient to re-drive or review completed runs. Versioned/checksummed `.urrun` artifacts persist per profile; the Local Runs browser shows valid and invalid records, marks Previous/PB state, and launches compatible records through the canonical deterministic input path without creating duplicate captures.
- [~] Exact timing, lap/split data, PB deltas and medal/target deltas shown alongside preserved original indicators. Completed-run artifacts and the Local Runs browser now expose exact 60 Hz finish timing, and the run-data substrate already computes compatible split/finish deltas. The remaining product work is richer in-race/results split and target presentation while retaining stock indicators. Stock top-3 per-track records remain mapped in `analysis/generated/track-records-sram.json`.
- [~] Practice/free-play: Quick Practice now has a canonical 45-course catalog, progression-aware availability, renderer-neutral picker/input models and authoritative arbitrary-course stock-menu routing. The Windows product can select and launch permitted courses without direct race-state writes while isolating/restoring SRAM and suppressing normal profile/run persistence. Faster repeat-attempt/rematch ergonomics remain.
- [x] Concise onboarding/help for fundamental controls, landing and stunt-to-speed behavior, with live keyboard/controller binding labels, first-run dismissal plus F1 reopen, and deliberate preservation of secrets/advanced discovery.
- [ ] Accessibility/input presentation options that do not alter authoritative simulation, including remapping, vibration control, readable text support and reduced flashing where applicable.
- [ ] Implement fast local multiplayer with simultaneous independent join/racer selection, duplicate classic presets allowed when desired, and clear player/viewport identity. Add rematch and track rotation without stock League bureaucracy; Authentic keeps the sequential selector.
- [ ] Authentic/raw-pixel plus modern/HD presentation presets, with optional CRT/NTSC-style display choices where useful.
- [~] Fast navigation affordances: direct Quick Practice/course selection exist. Implement the decided post-result action set: Next Event, Retry, Track Select, Tour Select and Records, contextually emphasizing Next Event in Tour play and Retry in Practice; recent-track remains.
- [ ] Localization-ready text/UI architecture.
- [~] Preserve the original attract/demo cycle as the default in Modern and Authentic. Stock behavior is measured in `analysis/generated/attract-cycle.json`. A future Local Showcase sourced from strong local runs may be offered only as an explicit optional attract mode, never as a silent replacement.
- [ ] Keep content/data boundaries friendly to future custom courses, local challenge packs and visual packs without making those all launch requirements.

### Decide when subsystem maturity allows

- [~] Expanded racer cosmetics are post-baseline optional content. Do not make them a Windows launch dependency; exact classic presets plus profile/racer identity are sufficient.
- [~] Full replay-viewer editing controls are deferred until actual replay usage justifies them. Replay launch and ghosts are sufficient for baseline; pause/seek/frame-step/HUD toggles may follow.
- [~] Photo/capture tooling is deferred indefinitely unless player demand or an art-review workflow makes it product-relevant.
- [ ] Evaluate richer local statistics/telemetry views.
- [~] Achievements/challenges are post-baseline optional content. If added, keep them local and mastery/discovery-oriented; never make them progression authority.
- [~] Section/checkpoint-based practice starts are a preferred post-baseline mastery feature once a safe authoritative start-state contract exists; prioritize them ahead of achievements/photo tooling when capacity permits.
- [x] Local Tournament policy is decided: round-robin/points league is the default Modern format; bracket variants are optional later extensions.
- [x] Modern medal/progression policy is decided: selectable canonical challenge tier, with higher-tier completion satisfying lower tiers; Authentic retains stock sequential clears.
- [~] Local Showcase is an optional future attract mode; preserve the stock attract cycle as default.
- [~] User-facing mod/content-pack affordances remain post-baseline. Keep interfaces/content boundaries friendly to them, but do not build a mod ecosystem before the Windows product is complete.

### Network/hosted-service non-goals

- [ ] Keep ghost/replay/timing/leaderboard/challenge data models transport-agnostic enough for future extension, but implement only useful local behavior.
- [ ] Do **not** implement or provision online multiplayer, matchmaking, hosted/global/friend leaderboards, downloadable ghosts, accounts, daily/weekly services, backend deployment, service credentials or online CI/testing unless project infrastructure changes.

- [x] Pin RetroArch, Libretro Slang shaders and bsnes-hd as visual-reference dependencies without adding them to default CI.
- [x] Define the canonical multi-interpretation upscale/reference strategy in `docs/HD-VISUAL-REFERENCE-PIPELINE.md`.
- [x] Establish the initial coherent-art decision authority in `docs/HD-ART-DIRECTION.md`.
- [~] Shader/scaler matrices, headless RetroArch benchmarking, offline scaler equivalence and bsnes-hd isolation are optional diagnostic capabilities. The shipping Remastered pipeline already has deterministic raw/native evidence, semantic extraction, authored true-density assets and review/approval gates. Add one of these tools only when a concrete art ambiguity or renderer defect survives the existing evidence path.
- [x] Racer HD shipping pipeline and initial high-value ordinary-race coverage are established. The retained `1205–1220` strip plus bounded families `1305–1306`, `1244–1252`, `1230–1239` and `1261–1267` are hash-bound shipping-approved with temporal-coherence and exact runtime-guard acceptance. Exact-state registrations collapse to fewer production assets whenever byte-identical or proven palette-equivalent stock evidence permits; reuse the shared equivalence/approval tooling for every later family. Detailed frame metrics, run IDs and approval hashes belong in the owning manifests/generated review evidence rather than this queue. Future expansion is admitted only by measured player-visible fallback reduction or another concrete product requirement.
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
- [~] Original-development source/tool hunting is passive archival work. The existing ROMs, prototype, recovered historical workspaces, press material and local tooling are sufficient for the Windows product; only pursue Mike Dailly/framework/SNasm/editor/converter artifacts when a concrete new provenance lead appears.
- [~] Former “historical prediction” tests are no longer a bundled task. Course geometry/width and product-facing animation indexing are already sufficiently constrained by the canonical course corpus and presentation assets. Copier-protection and audio-driver identity remain preservation-only questions unless they affect a live compatibility or audio decision.


## Third-party code audit and adaptation

- [x] Establish an explicit imported-code review/adaptation policy.
- [x] Audit the recovered 2014 Lua bot for silent language/runtime hazards; duplicate table keys and the signed `0x8000` edge bug are recorded.
- [x] Centralize promoted player-state addresses and signed conversion in `tools/uniracers_state.py`.
- [x] Add unit coverage for promoted state semantics, duplicate-Lua-key detection and RNC packed-payload bounds.
- [x] Classify the Snes9x 1.43 Uniracers branch as historical workaround evidence rather than an implementation template.
- [x] Audit imported emulator/source snapshots far enough to identify assumptions worth testing. Remaining work is now Phase 4 runtime discrimination, not open-ended source auditing; active-display OAM is the first concrete seam.
- [x] Defer autonomous race-driving-policy porting. Exact historical SMVs plus the retained deterministic fixture matrix already cover current regression needs; revive state-responsive driving only when a concrete soak/fuzz requirement cannot be met by fixed input.
- [~] Review any newly imported executable/script before promoting it into a project-owned dependency. This is an ongoing admission rule, not a backlog item.
- [x] Classify and byte-pin the full `reference/imported/` corpus; fail CI on unclassified additions, altered mirrors or executable-bit drift.
- [x] Harden `tools/toolchain.json` / `bootstrap_toolchain.py`: argv-only builds, exact pins/origins, clean disposable checkouts, per-tool Python environments, typed artifact verification and hash-pinned project patches.
- [x] Make every automatic toolchain entry smoke-buildable in CI; keep heavyweight GUI/debugger workbenches explicitly manual until a real workflow needs them.
- [x] Establish `tools/tool_interop.json` and `docs/TOOL-INTEROPERABILITY.md` as the producer/consumer and multi-tool-chain authority.
- [~] Canonical symbol fan-out is sufficient for current automatic tooling through the generated snes2asm/da65 surfaces. Add Mesen/Ghidra import only when an active product-driven investigation actually uses those workbenches; do not schedule parity for unused tools.
- [x] Add an independent Snes9x vs Beetle/bsnes-derived first-race state route; first successful run establishes a checkpoint-by-checkpoint emulator-variance baseline.
- [~] Mesen/mesen-for-ai and Mesen-CDL integration are conditional cross-emulator tools, not current fidelity gates. Existing native + pinned-reference fixtures are sufficient for the Windows product. Promote the Mesen runtime/CDL adapter only when a specific discrepancy needs an independent emulator oracle or coverage source.
- [x] Prove the first exact semantic graphics/presentation round trip on a representative racer family: deterministic `$0FE9/$0FEB` frame identity → `20:8000` pointer → exact packed stream, plus exact race-init OBJ graphics and palette identity/payload, with byte-identical reconstruction and a compact manifest. Extend on demand rather than bulk-decoding every racer frame.\n- [~] The snes2asm → SuperFamiconv → WLA-DX round trip remains demand-triggered. Prove it only when a concrete native SNES planar graphics family requires that path; current Racer HD work does not.
- [x] Audit headless execution/build posture: keep GUI workbenches off default CI, preserve Mesen's upstream Xvfb-backed testrunner route, and restrict automatic builds to CLI/libretro surfaces.
- [x] Trim automatic build scope: cc65 now builds only da65; WLA-DX now builds only wla-65816 + wlalink; Python venv setup no longer upgrades pip unconditionally; fresh Git bootstrap fetches only the pinned commit.
- [~] Add tool-bootstrap cache/reuse only after measured agent sessions show it is a recurring wall-time cost. Until then this is a trigger condition, not queued implementation.

- [x] Pin visual-reference workbenches (RetroArch, Slang shaders, bsnes-hd) as manual/wrapped dependencies so future graphics work does not depend on rediscovering or floating upstream versions.
- [~] Add RetroArch/bsnes-hd interop only when a real diagnostic capture is needed by another project tool. The current Remastered pipeline does not require this contract.

Audit policy: `docs/THIRD-PARTY-CODE-AUDIT.md`. Remaining closeout scope and explicit defer/transfer rules: `docs/TOOLING-AUDIT-CLOSEOUT.md`.


## Completed-run / ghost current state (2026-10-05)

The durable run foundation and first player-facing consumption paths are shipped. Typed/versioned/checksummed `.urrun` artifacts persist per profile, export through the canonical deterministic input grammar, reload in a fresh process, and drive the Local Runs browser/replay path. Checksum-bound `.urghost` sidecars can render Previous or Personal Best in Modern 1P through the live camera and existing Racer-HD semantic selector without guest-memory, controller, collision or second-simulation authority. Corrupt/incompatible data fails closed. Remaining work is richer split/target presentation and local-management polish, not another records or ghost data model. See `COMPLETED-RUN-RECORDS.md`, `COMPLETED-RUN-BROWSER.md` and `GHOST-PRESENTATION-TRACE.md`.

