# UR-Recomp: active work queue

**Reconciled 2026-10-10 (see live GitHub for newer merges):** Baldosa integration and adversarial QA share one playable Windows x64 candidate. This queue owns live work; the [release ledger](RELEASE-QUALITY-LEDGER.json) alone owns gate status. Refresh `main` and PRs before assigning lanes.

**Short-horizon coordination:** [Windows beta quality campaign](WINDOWS-BETA-QUALITY-CAMPAIGN-20261010.md) establishes a seven-day review target, no forced ship date, three non-overlapping agent lanes and player-visible beta criteria. Preserve full technical-reference ambition and independent release QA.

## October 10 verified handoff and decision policy

- **Merged:** #1191 real fixed Original 256-wide physical 3840×2160 viewport/matte acceptance; #1185 real paired Original OAM 98/99 deletion with 483/483 final-colour differences inside source union; #1198 overlap counterfactual correlation; #1199 evidence report; #1193 opt-in same-host Switcher raw-memory offset comparison; #1194 visible native pause; #1200 Baldosa causal review; #1203 real Windows launcher diagnostics; #1208 native paused Quit with named-profile SRAM checkpoint.
- **QA-01 diagnostic:** exact original/native host 5782 retained in [QA01-SWITCHER-5782-RAW-MEMORY-EVIDENCE-20261010.md](QA01-SWITCHER-5782-RAW-MEMORY-EVIDENCE-20261010.md): 8 WRAM addresses differ, 0 VRAM/CGRAM; strict terminal comparator still fails, official 0/45. The experimental #1195 workflow is **never to be merged**, even though its expected-red run produced useful evidence.
- **Still P0:** #1204 rear-OBJ and #1207 density diagnostics merged. Native 1P/2P stock entry, pause/Restart, SDL Quit and selected-profile SRAM now have bounded Windows evidence; **profile/racer selection, authentic result→Records capture, pause Exit/Options, controller-only complete journey and fresh-process run publication remain unaccepted**. The native root's other advertised destinations are not yet wired; #1209 merged honest availability labels.
- **Dual enduring deliverable:** a playable remaster **and** the definitive, independent, evidence-backed Uniracers technical reference ([charter](DEFINITIVE-UNIRACERS-TECHNICAL-REFERENCE.md)). Archive every recoverable understanding; do not convert exhaustive archaeology into an unbounded prerequisite for feature development.
- **Resume regular development** once a reproducible Baldosa Windows internal alpha demonstrates authentic 1P/2P, coherent controller-first Modern ownership, pause/restart, one actual result and records/profiles across fresh process, and stable Original/widescreen without known P0 integrity/correctness defects. Full 45-course/QA-01..12 certification and technical-atlas completeness proceed alongside feature work under independent release gates. Preserve old runtime as rollback.

## Baldosa native Modern checkpoint (2026-10-09)

**Components merged, not yet a unified Modern app:**

- **#1090/#1095/#1099/#1100/#1101:** acknowledged native pause, input release, snapshot and CRC parity.
- **#1105:** real SDL Restart rewinds the guest's frame 1952 to race anchor 1783, preserves SRAM and proves changed post-resume WRAM on an append-only host timeline. Guest-indexed frame filenames can be overwritten by a rewind.
- **#1108:** Baldosa uses the existing portable Modern user-data root for config, bindings and SRAM; invalid explicit roots reject.
- **#1113:** opt-in typed Modern state/profile/catalog selection before native `RtlReadSram`; invalid named profiles reject without creating a profile.
- **#1115:** merged green, real Win32/Linux guest loads catalog-backed 8-KiB named SRAM and rejects corrupt profiles; not durable typed snapshot sync (#1125).

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
| **P0 Gameplay fidelity / QA-01/07** | Real original/native Switcher Race B finished **MIKE 1:08.81** on both engines at absolute host **5783** (guest-relative +4704 Snes9x/+4702 Baldosa); **#1169 merged** preserved run 38064406315. Second paired run **38072910224** compared **43** guest-relative snapshots: non-menu/track fields match at every sampled frame; first course/menu phase difference at **+4664** (ref 3/0x00, native 0/0x84), next at **+4697–4698** (ref 0/0x84, native 3/0x16). Original/native guest entries differ by +2 host frames; source 34-frame course-0 prelude must not be reclassified as unrelated race. | Pin the latest artifact/provenance in `analysis/data/switcher-original-baldosa-terminal-handoff-20261010.json`; **sample only missing original restore-boundary frames +4699–4701**, then compare guest-relative and same-absolute-host transitions. Prioritize proving live race timing/terminal gameplay rather than general CRC archaeology; do not edit physics, controller timestamps or thresholds. | Official **0/45** accepted USA full events. Results/display/time match but guest-relative terminal mismatch remains, so no automatic course admission. Independent source score, progression and timing acceptance required. |
| **P0 Source-visible Racer HD + true Widescreen / QA-08** | Accepted native **Original**: #1210/#1211/#1221 prove real post-GO 342×224 split racing at 3840×2160 physical SDL output, all 8,294,400 pixels source-parity exact; zero 256-centre differences at 1856 and 2208; 2,473/2,473 guest CRCs. Stable 1×–4× Original fallback; authored 4× racer work remains in `native/presentation/racer_hd_presenter.hpp`. **#1218 negative:** guarded 2P P1-only after GO rejected 269 P2 occlusions and 215 missing P1 selections/art, 0 actual HD presents. | Finish **one actual Windows graphics product path** with genuine 342-wide world, coherent 1×–4× Original/Remastered and physical 4K. Resolve genuine rider source/foreground visibility BEFORE HD removal; preserve stock fallback. Fixed-width 1P guarded art #1228 and real late 1P source draft #1231 remain diagnostic, not release gates. | Existing single compositor, original 256×224 reference, 7:6 PAR and real 1P/2P/VS inputs. Own graphics/QA-08; never alter guest gameplay, product storage or Modern frontend. |
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

## Three active exclusive lanes

Use the [Windows beta quality campaign](WINDOWS-BETA-QUALITY-CAMPAIGN-20261010.md) for the current three-agent handoff. Every lane starts from fresh main/CI, reuses the existing candidate, and must produce executable evidence; do not create parallel routers, simulators, or repeated AOT builds.

- **A, product / Windows:** Own Baldosa execution, `modern_session_c_api.h`, host input/pause, frontend, profiles/SRAM, results/records and packaging. Accept a controller-first real race through results, records and fresh-process persistence. Preserve existing Modern state machines.
- **B, graphics / QA-08/10:** Own source-accurate racer presentation, 342-wide world, Original fallback, 4x HD, HUD/PAR and physical 4K evidence. Never alter guest gameplay.
- **C, gameplay / QA-01/07:** Own original/native event oracle and complete-event race, circuit, stunt, scoring and progression comparisons. Never promote a bounded checksum to a certified event.

Independent QA reuses their *same exact Windows candidate* for player journeys, durable records and hardware-specific gates. The old backend remains rollback until Baldosa is accepted.

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
