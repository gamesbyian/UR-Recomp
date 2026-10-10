# UR-Recomp: active work queue

**Current as of 2026-10-09:** Baldosa integration and adversarial QA share one playable Windows x64 candidate. This queue owns live work; the [release ledger](RELEASE-QUALITY-LEDGER.json) alone owns gate status. Refresh `main` and PRs before assigning lanes.

## Baldosa native Modern checkpoint (2026-10-09)

**Components merged, not yet a unified Modern app:**

- **#1090/#1095/#1099/#1100/#1101:** acknowledged native pause, input release, snapshot and CRC parity.
- **#1105:** real SDL Restart rewinds the guest's frame 1952 to race anchor 1783, preserves SRAM and proves changed post-resume WRAM on an append-only host timeline. Guest-indexed frame filenames can be overwritten by a rewind.
- **#1108:** Baldosa uses the existing portable Modern user-data root for config, bindings and SRAM; invalid explicit roots reject.
- **#1113:** opt-in typed Modern state/profile/catalog selection before native `RtlReadSram`; invalid named profiles reject without creating a profile.
- **#1115:** check current PR/CI before crediting its real-guest named-profile 8-KiB SRAM boot and invalid-profile tests.

**Next:** Connect the existing five-way visible Modern frontend and controller seats to Baldosa, preserving exactly one host-owned input, Restart, storage/records/ghost/tournament authority. Keep the older patched executable as rollback. Current profile boot proofs do **not** establish that frontend, a full persisted result or original-emulator event parity (**official 0/45**). Share the same native build and QA routes with graphics/gameplay agents.

## Baldosa native Modern checkpoint (2026-10-09)

**Components merged, not yet a unified Modern app:**

- **#1090/#1095/#1099/#1100/#1101:** acknowledged native pause, input release, snapshot and CRC parity.
- **#1105:** real SDL Restart rewinds the guest's frame 1952 to race anchor 1783, preserves SRAM and proves changed post-resume WRAM on an append-only host timeline. Guest-indexed frame filenames can be overwritten by a rewind.
- **#1108:** Baldosa uses the existing portable Modern user-data root for config, bindings and SRAM; invalid explicit roots reject.
- **#1113:** opt-in typed Modern state/profile/catalog selection before native `RtlReadSram`; invalid named profiles reject without creating a profile.
- **#1115:** check current PR/CI before crediting its real-guest named-profile 8-KiB SRAM boot and invalid-profile tests.

**Next:** Connect the existing five-way visible Modern frontend and controller seats to Baldosa, preserving exactly one host-owned input, Restart, storage/records/ghost/tournament authority. Keep the older patched executable as rollback. Current profile boot proofs do **not** establish that frontend, a full persisted result or original-emulator event parity (**official 0/45**). Share the same native build and QA routes with graphics/gameplay agents.

## First read (fresh coding agent, five-minute route)

1. [PROJECT-PLAN.md](PROJECT-PLAN.md) for what is being built, and [BALDOSA-UR-RECOMP-REUSE-AUDIT-20261009.md](BALDOSA-UR-RECOMP-REUSE-AUDIT-20261009.md) for completed code/assets and exact integration seams.
2. The one specialist authority for your *owned* lane, plus its current sources and exact CI/head. Do **not** re-read every dated Baldosa experiment or all 45 course histories.
3. [QA-BOUNDED-RELEASE-CAMPAIGN.md](QA-BOUNDED-RELEASE-CAMPAIGN.md) for common evidence and acceptance boundaries; [QA-PLAYER-JOURNEYS.md](QA-PLAYER-JOURNEYS.md) for named journeys.

Preserved old queue, phase progress and individual investigation notes: [archive/WORK-QUEUE-THROUGH-20261009.md](archive/WORK-QUEUE-THROUGH-20261009.md). **Historical record only**, not competing priority authority.

## Current delivery board and ownership

| Order / exclusive owner | Starting point already in the repo | Next acceptance-producing change | Shared QA reuse / stop |
|---|---|---|---|
| **P0 Integrated Windows Modern/Baldosa lifecycle** | Merged #1068/#1072/#1074/#1076/#1078/#1080/#1081/#1083/#1085 provide native guest observer, moving 4× art, input, genuine pause, world margins, stable fallback and Win32 execution/PE tests. `native/product/baldosa_execution_backend.hpp`, existing `tools/baldosa_*` injectors and `modern_session_c_api.h` | Join these into **one** actual controller-only Modern launch → real 1P/2P guest → acknowledged pause/resume/restart/exit → settled result under existing product host. Keep old core rollback. Merged green **#1086** verifies live-race-native pause/resume inside a genuine 2P guest (24 frozen SDL polls, next exact frame, unchanged 2,473 WRAM CRCs) on Linux and Win32; Modern menu/physical audio remains independent QA. | QA-05/06/09/10 controller, audio, output and human focus. Native build alone is insufficient; stop if current Modern host must be reauthored rather than narrowly adapted. |
| **P0 Gameplay fidelity / QA-01/07** | Merged **#1079** runs the exact archived original Zoo scene input in both Snes9x and Baldosa: both reach a stable result but the sampled guest `p1_stored_contact` is **0 vs 10240**, with a two-frame guest-entry offset. Independent full-result parity remains unproven | Reproduce at least one authentic-to-settled original/Baldosa Circuit, scored Stunt and non-Dragster Race, with course/score/laps/time/result and independently linked reference. Find the cheapest first event witness rather than more engine archaeology. | Only then fan out through 45 USA events. **Official 0/45** accepted pairs remains; no credit for script exit, matched WRAM CRC or timed out Zoo. |
| **P0 Source-visible Racer HD + true Widescreen / QA-08** | First-party procedural 4× racer pixels in `native/presentation/racer_hd_presenter.hpp`; `native/title/uniracers_ws_margins.c`; stable 1024×896 4× Original fallback. Merged **#1082** demonstrates 342×224 native world pixels in all four split margins across six moving 2P frames, with 2,473/2,473 identical guest CRCs; merged **#1045** adds per-rider Original-OBJ footprint suppression, source-visibility evidence and negative tests; native acceptance passed on the preceding byte-identical runtime head and unit/ledger gates passed on the final merge head. Full 1P/2P/VS and widened pixel release proof remains open | Merge verified narrow contributions into **one** host compositor. Prove P1/P2 source-derived sprites, actual margin world pixels, zero phantom riders, correct Original fallback, proper HUD/7:6 PAR and actual 4K-capable host presentation without changed guest behavior. | Shared pinned 2P route plus moving visual/L4 checks. +24 margin or 1024×896 raster alone does **not** prove finished 16:9/4K. Don't redo art, shadows or density infrastructure. |
| **P0 Modern frontend feature + QA-05/09** | Merged green **#1056** implements the visible five-destination Modern root and default Return→Start guest-release barrier, including native SDL and Windows candidate checks **on our existing product host**, not a unified Baldosa application | Bind those already validated root/input models to Baldosa's C ABI, no second router; preserve exact P1/P2 human release, native pause and 5/5 audible default Restart, then verify the combined Windows package. Controller-only profile→event→result→Records→quit and 5/5 audible default Restart repetitions. | Distinguish missing feature from missing QA proof. Do not modify overlapping `uniracers_modern_host.cpp` in another lane without coordination. |
| **P0 Persistent progress and local 2P QA-02/03/11** | Profiles/SRAM, `.urrun/.urghost/.urmatch`, tournament leases/receipts and multi-process acceptance already implemented. Merged green **#1058** preserves the exact in-process fixture attempt/lease after receipt I/O failure and retries from SAVE PENDING without inventing awards | Keep existing host schemas and authority under Baldosa. Prove a genuinely raced 2P leg/result/Records journey, repeat the receipt-outage test on the package, and separately design **crash-before-receipt post-restart provenance**; the current retry is in-process only. | Never fabricate standings, silently overwrite player data or count unit-only evidence as packaged recovery. Do not reimplement #1058's now-merged in-process lease/receipt recovery; preserve transaction invariants and focus only on unproved fresh-process real-guest scenarios. |
| **P1 Integration/independent QA integrator** | Existing [QA-PLAYER-JOURNEYS.md](QA-PLAYER-JOURNEYS.md), pinned USA ROM and CI routes; Windows portable ZIP builder and user-data root | Assemble one nominated **exact Windows ZIP/hash** from merged code; reuse it for controller, audio, 4:3/16:9, data-restart, ghost/result and 1P/2P acceptance with independent source oracle. | Record each L4/L5 witness against exact build; preserve physical hardware gap and current QA ledger. QA campaign's first **300 productive-agent-hour** tranche is reviewed at 100/200/300, not an accepted cost forecast. |

**Integration rule:** Each feature owner supplies executable output and component proof; QA reuses that exact candidate and adds independent event, lifecycle, persistence and player-visible assertions. Prefer one guest build serving many witness checks, not N duplicate recompilation builds. No new generic harness or extra automatic Actions trigger without a new durable invariant.

## Sequencing and merge boundaries

1. **Refresh live state before editing.** **All six outstanding implementation PRs (#1045, #1056, #1058, #1079, #1082, #1086) have merged.** Recheck GitHub and next candidate after this checkpoint; do not reopen their already-proven bounded components. The last QA-08 code passed real native acceptance before a ledger-only correction and the revised ledger passed unit validation. Resolve branch ownership from GitHub, not this dated snapshot. Do not overwrite stale-branch content into `main`.
2. **Integrate Baldosa's already proven primitives**, using established disposable stages and narrow host C ABI: frame/PPU state → Modern runtime; human input and pause ownership → actual menus; guest result/clock/controller stream → existing stores. Preserve the old shipping core as rollback, not an equal greenfield investigation.
3. **Reuse the same short real route for acceptance where possible:** (a) live 2P input/pause/HD/world + CRC; (b) original/native completed single events; (c) fresh-process Windows player journey with persisted results and resumed input/audio. Do not equate any of these with the others.
4. **Produce the first player-facing vertical slice** before broad parallel course/asset/secondary-platform expansion: launch → profile/racer → authentic race → legitimate result → Records/replay/ghost → retry or quit, in real 16:9 with coherent stable density and optional Original.
5. **Promote only accepted evidence.** The release ledger stays unchanged until specific candidate-bound independent proof meets its gate. Log honest negative outcomes and rerun invalidated assertions after merges.

## Three ready independent lanes for fresh agents

**All three begin from latest `main` and current CI.** These are scoped agent handoffs, not a second queue or permission to create three recompilation frameworks. Reuse one pinned native candidate and the existing exact-guest, emulator, input and raster tests. A lane finishes by merging a functional change or producing a decisive failure trace with a named owner.

**Lane A, Baldosa → Modern Windows gameplay/product (P0):** Own `native/product/baldosa_execution_backend.hpp`, existing `tools/baldosa_*product*` guest/input/pause stages, and the narrow `modern_session_c_api.h` boundary. **Reuse** the merged #1056 five-destination root, existing profiles/SRAM/Records/ghosts/tournament stores, and #1086 live-race pause without rewriting their state machines. Deliver a genuine controller-only cold start → profile/racer → live 1P/2P → acknowledged pause/restart/quit → actual result → Records/Repeat route, including physical held-Start release and audible native resume. Validate one exact Windows packaged candidate. Avoid owner changes in `native/presentation/` or the original-event oracle.

**Lane B, complete original/Baldosa event fidelity QA-01/07 (P0):** Own `tools/baldosa_2014_zoo_*`, current Snes9x/Baldosa result comparator, `docs/ORIGINAL-COURSE-EVENT-CENSUS.md` and corresponding test/fixtures. #1079 found both guests enter a **stable** Zoo result but disagree at `p1_stored_contact` (0 vs 10240), with a two-frame scene-entry difference. First discriminate latch phase/scene initialization from real guest behavior, then check authentic PPU result time/text, final laps/score and correct original course identity. Close one real Race/Circuit/Stunt independent pair **before** expanding 45-course coverage. No new universal harness.

**Lane C, HD/widening compositor and QA-08/10 (P0):** Own existing `native/presentation/` source-OBJ/pose renderer, `native/title/uniracers_ws_margins.*` and `tools/baldosa_ws24_*`/4× host presentation probes. Begin with merged #1082 **342×224 actual-world 1× evidence** and merged #1045 per-instance Original-OBJ footprint guard; further full moving 2P/VS/original-overlap admission is still missing. Join true extra world visibility with stable 4× authored HD / Original fallback, ensure P1/P2 source-visible sprites, clean split line/HUD/7:6 PAR and correctly mapped actual 3840×2160 host output. Preserve guest 2P CRC. No new renderer, source extraction pipeline or simulation writes.

**Following joint candidate:** QA-02/03/11 can use actual Lane A raced run/match/ghost artifacts and Lane B authentic results to validate package/fresh-process C16/storage crash boundaries, multi-leg results and tournament records. This follow-up does **not** reopen the already-merged in-process lease/receipt fix. An independent release-QA integrator owns the final exact Windows ZIP/hash and gate-specific hardware checks, not duplicated per-agent CI matrix jobs.

## Stop / defer

- **No second Modern router, save store, ghost system, renderer, PPU materializer, Baldosa script/asset intake or permanent guest.** Those materials already exist.
- Do not commission new broad 45-course automation before the first full original/native event path is demonstrated.
- Defer optional Racer Studio four-material masks, editor/custom courses, browser/netplay, Switch/PS5/macOS ports, global sound restoration and generic RE unless a specific live Windows defect depends on them.
- Do not chase obscure per-frame differences unless they affect authoritative gameplay, sound, player data or a required fidelity oracle.
- Fix confirmed P0 bugs even if a spike budget expires. A bounded test timeout is a research stop, never permission to ship data loss or a known gameplay defect.

## Routing by authority

Product and renderer ownership: [PROJECT-PLAN.md](PROJECT-PLAN.md), [MODERN-FRONTEND-SHIPPING-STATUS.md](MODERN-FRONTEND-SHIPPING-STATUS.md), [MODERN-PRODUCT-LAYER.md](MODERN-PRODUCT-LAYER.md), [DISPLAY-PRESENTATION-POLICY.md](DISPLAY-PRESENTATION-POLICY.md), [WIDESCREEN.md](WIDESCREEN.md), [HD-ART-DIRECTION.md](HD-ART-DIRECTION.md).
Baldosa code/evidence: [BALDOSA-UR-RECOMP-REUSE-AUDIT-20261009.md](BALDOSA-UR-RECOMP-REUSE-AUDIT-20261009.md), [BALDOSA-NATIVE-EXECUTION-EXPERIMENT-20261009.md](BALDOSA-NATIVE-EXECUTION-EXPERIMENT-20261009.md).
QA and source oracle: [QA-BOUNDED-RELEASE-CAMPAIGN.md](QA-BOUNDED-RELEASE-CAMPAIGN.md), [ORIGINAL-COURSE-EVENT-CENSUS.md](ORIGINAL-COURSE-EVENT-CENSUS.md), [RELEASE-QUALITY-LEDGER.json](RELEASE-QUALITY-LEDGER.json), [VALIDATION.md](VALIDATION.md).
Windows integration: [WINDOWS-X64-PACKAGING.md](WINDOWS-X64-PACKAGING.md) and [WINDOWS-CLEAN-MACHINE-ACCEPTANCE.md](WINDOWS-CLEAN-MACHINE-ACCEPTANCE.md).

No historical section of this file or an old `CLAUDE` branch is an active assignment. For more specific work, use `python3 tools/build_agent_context.py <lane>`, then check that the lane still matches this live board.
