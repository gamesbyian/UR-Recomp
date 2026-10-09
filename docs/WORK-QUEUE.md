# UR-Recomp: active work queue

**Current as of 2026-10-09 (integration checkpoint after #1085):** **Baldosa incorporation and the remaining adversarial QA are one coordinated shipping programme.** Work on a single faithful, genuinely modern, playable Windows x64 candidate. This document alone orders *live* work; do not infer today's assignment from historical PR numbers, tool inventories or the length of an old research plan. Refresh `main` and GitHub PR states on entry because merges are frequent. **Release gate status lives only in [RELEASE-QUALITY-LEDGER.json](RELEASE-QUALITY-LEDGER.json).**

## First read (fresh coding agent, five-minute route)

1. [PROJECT-PLAN.md](PROJECT-PLAN.md) for what is being built, and [BALDOSA-UR-RECOMP-REUSE-AUDIT-20261009.md](BALDOSA-UR-RECOMP-REUSE-AUDIT-20261009.md) for completed code/assets and exact integration seams.
2. The one specialist authority for your *owned* lane, plus its current sources and exact CI/head. Do **not** re-read every dated Baldosa experiment or all 45 course histories.
3. [QA-BOUNDED-RELEASE-CAMPAIGN.md](QA-BOUNDED-RELEASE-CAMPAIGN.md) for common evidence and acceptance boundaries; [QA-PLAYER-JOURNEYS.md](QA-PLAYER-JOURNEYS.md) for named journeys.

Preserved old queue, phase progress and individual investigation notes: [archive/WORK-QUEUE-THROUGH-20261009.md](archive/WORK-QUEUE-THROUGH-20261009.md). **Historical record only**, not competing priority authority.

## Current delivery board and ownership

| Order / exclusive owner | Starting point already in the repo | Next acceptance-producing change | Shared QA reuse / stop |
|---|---|---|---|
| **P0 Integrated Windows Modern/Baldosa lifecycle** | Merged #1068/#1072/#1074/#1076/#1078/#1080/#1081/#1083/#1085 provide native guest observer, moving 4× art, input, genuine pause, world margins, stable fallback and Win32 execution/PE tests. `native/product/baldosa_execution_backend.hpp`, existing `tools/baldosa_*` injectors and `modern_session_c_api.h` | Join these into **one** actual controller-only Modern launch → real 1P/2P guest → acknowledged pause/resume/restart/exit → settled result under existing product host. Keep old core rollback. Open #1086 owns pause in **live** race, not a new pause framework. | QA-05/06/09/10 controller, audio, output and human focus. Native build alone is insufficient; stop if current Modern host must be reauthored rather than narrowly adapted. |
| **P0 Gameplay fidelity / QA-01/07** | Historical original Zoom Zoo and Bowl completion movies, existing original/native input tools, Baldosa bounded smoke. Open **#1079** owns complete original Zoo movie transplant | Reproduce at least one authentic-to-settled original/Baldosa Circuit, scored Stunt and non-Dragster Race, with course/score/laps/time/result and independently linked reference. Find the cheapest first event witness rather than more engine archaeology. | Only then fan out through 45 USA events. **Official 0/45** accepted pairs remains; no credit for script exit, matched WRAM CRC or timed out Zoo. |
| **P0 Source-visible Racer HD + true Widescreen / QA-08** | First-party procedural 4× racer pixels in `native/presentation/racer_hd_presenter.hpp`; `native/title/uniracers_ws_margins.c`; stable 1024×896 4× Original fallback. Open **#1082** owns calibrated 342×224 (+48 backing) experiment; **#1045** owns exact per-rider Original source-OBJ footprint gating | Merge verified narrow contributions into **one** host compositor. Prove P1/P2 source-derived sprites, actual margin world pixels, zero phantom riders, correct Original fallback, proper HUD/7:6 PAR and actual 4K-capable host presentation without changed guest behavior. | Shared pinned 2P route plus moving visual/L4 checks. +24 margin or 1024×896 raster alone does **not** prove finished 16:9/4K. Don't redo art, shadows or density infrastructure. |
| **P0 Modern frontend feature + QA-05/09** | Existing typed five-destination root, huge implemented Modern host and profile/record models. Open **#1056** owns visible Play/Practice/Multiplayer/Records/Options and default Return→Start guest-input release fix | Land and validate its root/input changes on the existing host, then reuse the same models via Baldosa C ABI. Controller-only profile→event→result→Records→quit and 5/5 audible default Restart repetitions. | Distinguish missing feature from missing QA proof. Do not modify overlapping `uniracers_modern_host.cpp` in another lane without coordination. |
| **P0 Persistent progress and local 2P QA-02/03/11** | Profiles/SRAM, `.urrun/.urghost/.urmatch`, tournament lease/receipts and multi-process acceptance already implemented; **#1058** owns exact storage-outage receipt retry | Preserve all existing file schemas and ownership under the new guest. Prove a fresh-process real 2P leg/result/Records journey and explicitly inject the relevant storage faults. | Never fabricate standings, silently overwrite player data or count unit-only evidence as packaged recovery. Keep #1058's coordinator/host file ownership exclusive. |
| **P1 Integration/independent QA integrator** | Existing [QA-PLAYER-JOURNEYS.md](QA-PLAYER-JOURNEYS.md), pinned USA ROM and CI routes; Windows portable ZIP builder and user-data root | Assemble one nominated **exact Windows ZIP/hash** from merged code; reuse it for controller, audio, 4:3/16:9, data-restart, ghost/result and 1P/2P acceptance with independent source oracle. | Record each L4/L5 witness against exact build; preserve physical hardware gap and current QA ledger. QA campaign's first **300 productive-agent-hour** tranche is reviewed at 100/200/300, not an accepted cost forecast. |

**Integration rule:** Each feature owner supplies executable output and component proof; QA reuses that exact candidate and adds independent event, lifecycle, persistence and player-visible assertions. Prefer one guest build serving many witness checks, not N duplicate recompilation builds. No new generic harness or extra automatic Actions trigger without a new durable invariant.

## Sequencing and merge boundaries

1. **Refresh live state before editing.** At this checkpoint #1086, #1082, #1079, #1058, #1056 and #1045 are open; #1085 is merged. Resolve branch ownership from GitHub, not this dated snapshot. Do not overwrite stale-branch content into `main`.
2. **Integrate Baldosa's already proven primitives**, using established disposable stages and narrow host C ABI: frame/PPU state → Modern runtime; human input and pause ownership → actual menus; guest result/clock/controller stream → existing stores. Preserve the old shipping core as rollback, not an equal greenfield investigation.
3. **Reuse the same short real route for acceptance where possible:** (a) live 2P input/pause/HD/world + CRC; (b) original/native completed single events; (c) fresh-process Windows player journey with persisted results and resumed input/audio. Do not equate any of these with the others.
4. **Produce the first player-facing vertical slice** before broad parallel course/asset/secondary-platform expansion: launch → profile/racer → authentic race → legitimate result → Records/replay/ghost → retry or quit, in real 16:9 with coherent stable density and optional Original.
5. **Promote only accepted evidence.** The release ledger stays unchanged until specific candidate-bound independent proof meets its gate. Log honest negative outcomes and rerun invalidated assertions after merges.

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
