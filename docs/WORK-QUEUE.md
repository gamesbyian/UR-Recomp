# UR-Recomp: active work queue

**Reconciled 2026-10-10 (see live GitHub for newer merges):** Baldosa integration and adversarial QA share one playable Windows x64 candidate. This queue owns live work; the [release ledger](RELEASE-QUALITY-LEDGER.json) alone owns gate status. Refresh `main` and PRs before assigning lanes.

**Short-horizon coordination:** [Windows beta quality campaign](WINDOWS-BETA-QUALITY-CAMPAIGN-20261010.md) establishes a seven-day review target, no forced ship date, three non-overlapping agent lanes and player-visible beta criteria. Preserve full technical-reference ambition and independent release QA.

## October 10 verified handoff and decision policy

- **Merged:** #1191 real fixed Original 256-wide physical 3840×2160 viewport/matte acceptance; #1185 real paired Original OAM 98/99 deletion with 483/483 final-colour differences inside source union; #1198 overlap counterfactual correlation; #1199 evidence report; #1193 opt-in same-host Switcher raw-memory offset comparison; #1194 visible native pause; #1200 Baldosa causal review; #1203 real Windows launcher diagnostics; #1208 native paused Quit with named-profile SRAM checkpoint.
- **QA-01 Switcher stack evidence:** Same-host **5782** original/native WRAM differs at eight stack-page bytes, VRAM/CGRAM equal; real positive result at **5783**, yet guest-relative onset **+4704/+4702** still fails (0/45). Executed original [JSR witness](../analysis/data/switcher-original-jsr-stack-opcode-scopes-20261010.json): **13,709 changed-byte scopes**, including original `82:B1F2/B1F9` return lows `F4/FB` at `01F1`. Paired native [writer witness](../analysis/data/switcher-native-stack-actual-writers-20261010.json): **32,333 write attempts**, corresponding `01F1` bytes and one native `I_NMI_M1X1` write to **`01DD` at host 5781**. **Next:** original same-fresh-host 5781 `01DD` PC/SP and live result/progression reader. Source archived movie 17030 uses a different clock and event counts; never shift inputs, alter guest rules, merge one-shot #1244, or waive strict parity.
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
| **P0 Integrated Windows Modern/Baldosa lifecycle** | Merged #1212/#1213/#1216: physical SDL Quit, fresh-process named SRAM, input guard and genuine 2-process profile conflict; #1229 native read-only settled 1P/2P result observer; #1230 Records archive read-only. Existing Baldosa execution bridge and Modern session authority are preserved. | Complete controller-first racer/profile → native 1P/2P → authentic result → newly published Records, durable fresh-process validation, lifecycle. Old backend remains rollback; neither test fixtures nor source-only observations count as finished runs. | QA-05/06/09/10; one exact Windows candidate and guest event acceptance. |
| **P0 Gameplay fidelity / QA-01/07** | Original and native Switcher Race B both show MIKE **1:08.81**. Paired run #1169 and 43 guest-relative snapshots locate result/menu phase differences at +4664 and +4697–4698; race entry differs by 2 host frames, with a genuine original course-0 prelude. [Canonical witness](../analysis/data/switcher-original-baldosa-terminal-handoff-20261010.json). | Compare missing +4699–4701 restore samples and absolute-host versus guest-relative transitions; preserve controller inputs, original rules and strict comparator. | Official **0/45** complete USA events accepted, pending source-derived result and progression parity; QA-01 owns. |
| **P0 Source-visible Racer HD + true Widescreen / QA-08** | **Original source proof accepted:** #1221 real post-GO split 3840×2160 physical SDL pixels and stock-centre parity; #1231 seven independent source-exact 342×224/1368×896 1P frames including active race2208, 5,447 guest CRCs. **Authored HD bounded:** #1228 fixed-1P first source-positive 4× racer captures (3422/3526 bottom-only pixels, native top preserved) and #1245 safe original-OAM pixel footprint; full 2P HD remains blocked by #1218 real occlusion. | **Next: actual integrated Windows visuals**, then original-PPU OBJ/depth visibility for motion-cycle `08D5/0855/0895` (1,552/1,679 moving 1P guest frames). Do NOT prioritize late held `0A4B` (1,512 contiguous after 3639) from raw frequency. #1257/#1259 archive temporal proof; #1255 source-OAM eligibility is diagnostic until native accepted. Preserve 7:6 PAR, 4× Original fallback, genuine 342-world, original HUD/P1/P2 and source-safe art. | QA-08 graphics owner; no guest gameplay or Windows profile/Records/Modern frontend edits. Source geometry is not PPU opacity/final BG priority or HD release. |
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
