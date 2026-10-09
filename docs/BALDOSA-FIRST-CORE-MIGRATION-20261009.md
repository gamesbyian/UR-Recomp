> **2026-10-09 current-main correction, after #1083:** The two equal greenfield spikes proposed below have been overtaken by real merged Baldosa bridge and presentation work. **Read [the repository-wide first-party code/asset reuse audit](BALDOSA-UR-RECOMP-REUSE-AUDIT-20261009.md) first.** Baldosa is now the leading integration path, with merged guest, human-input, native pause, 4x HD+Original fallback, real +24 world and Windows PE compilation gates. Continue from these reusable implementations; retain selective old-core upgrade only if a specific Baldosa compatibility blocker warrants it. This banner changes priority, **not** the genuine full player-journey/45-course acceptance standards.

# Baldosa-first remaster-core migration decision

**Decision proposal, 2026-10-09.** Owner goal: an otherwise gameplay-faithful Uniracers with **true 4K-capable presentation, actual widescreen world visibility, modern menus, controller-first accessibility, customization, profiles, records, ghosts, replay, and multiplayer**. A standalone faithful recomp is an enabling core, **not the differentiated product**.

## Executable decision, not open-ended research

**Default hypothesis: start from Ema Guillén's playable AOT core and re-host our product/presentation layers** rather than continuing to rebuild 65816 execution. **Challenge it with a bounded competing path: transplant Ema's critical framework improvements into our existing core.** Choose the path providing a repeatably playable, correct Windows x64 vertical slice with the least migration complexity and remaining maintenance burden. The prior hours committed to either implementation have zero decision weight.

Immutable inputs:
- Baldosa game repo `baldosa/uniracers-recomp@10b864b9d14a7b7416dd909eb7b054c88faef101`; full existing fork `gamesbyian/uniracers-recomp`; our intake `reference/imported/reverse-engineering/baldosa-uniracers-recomp/` (85 hand-maintained files, checked byte-exact).
- Ema framework `baldosa/snesrecomp@075fbe4c8e0d97b0013be541795c39cb644a9709` and `recomp-ui@7e884a227accea91ddb378671bd49aaeeea13371`; exact 86-commit upstream framework ancestry index in `analysis/data/baldosa-framework-delta-20261009.json`.
- Existing UR-Recomp framework `cd5875cbdaf19f5e324272b1f8051d671fce9215`, its repository-owned staged archive, Cargo closure, **dozens** of project-owned ordered host/runtime patch artifacts catalogued in `tools/toolchain-entries/snesrecomp.json`. Do not assume those patches apply cleanly to Ema's fork or can all be removed.
- Only targeted USA ROM digest `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478` is compatible. Never compare with a silently different PAL/prototype build.
- Read `docs/SEMANTIC-SUFFICIENCY.md`, `docs/QA-BOUNDED-RELEASE-CAMPAIGN.md`, `docs/ORIGINAL-COURSE-EVENT-CENSUS.md`, `docs/MODERN-FRONTEND-SHIPPING-STATUS.md`, `docs/SNESRECOMP-ISLAND-SCOPE.md`, `docs/BALDOSA-FRAMEWORK-DELTA-20261009.md` before claiming a pass. Data and tests under `analysis/` and `tests/` are not implicitly new evidence.

## Initial hard gate: prove Ema's binary, untouched

Run the fork as Ema actually ships it, with exact pinned submodules and owned-USA-ROM input, clean process and controller settings. First do his own nine supplied routes against his stated reference oracle and examine **unmasked** differences separately. Then require a live two-player split-screen race, a full non-Dragster race, a complete multi-lap circuit, a scored Stunt, and terminal result screens. Record event identity, inputs, frame bounds, final scoreboard and guest state, PPU/OAM and sound. Since their routes primarily assert masked checkpoints rather than our accepted terminal-result protocol, **none of these are credited as passed before running**.

If this untouched baseline fails to build/run or only passes under substantial framework repair, stop the wholesale-swap premise and favor selective transplantation for that defect. Preserve exact failure traces and the original repository state.

## Competing spike A: Ema-first host

Use a separate worktree/branch built from the **existing full Baldosa fork**, not `src/gen/` in the UR-Recomp source tree. Produce a Windows x64 title executable capable of:
1. Running the unmodified AOT guest with host hooks only and exporting **the minimum authoritative per-frame contract**: CPU/WRAM/SRAM, actual OAM/VRAM/CGRAM/palette state, PPU/window/HDMA state, audio clock and per-seat input. Record snapshots on native 256x224 logical geometry, including horizontal world offsets; do not fake HD via screenshots.
2. Passing a **stable frame-boundary and process-restart test**, with no invented result state. Separate true guest frame, renderer frame and simulation controller ownership. All product actions (pause/reset/restart/quit/profile selection/records) need explicit host-vs-guest authority and input release.
3. Rendering one authentic stock 1P race and **a correct 2P split** through the existing UR-Recomp renderer interface or a narrow adapter to it. Implement the same OAM high-table evidence gate as QA-08. Preserve the option to fall back to stock original sprites.
4. Displaying a **real +24 native logical extension** (or smallest already verified host-owned widening configuration) without changing gameplay geometry/checkpoint semantics. Then exercise one 4K output mode: 4K alone is just output resolution; *true* widescreen requires preserved world visibility and correct 7:6 original pixel-aspect accounting.
5. Round-trip one existing modern profile, one completed `.urrun` plus `.urghost`, and one records/result action across a **fresh process**, with byte-for-byte compatibility or an explicit versioned migration. Never overwrite a player's save just to bootstrap a spike.

**First adapter design** should live on our side of a C ABI boundary, leaving Baldosa's `src/gen` and analyzer cfg untouched. Avoid building a new renderer, save store, profile model or frontend. Do not integrate the entire external `recomp-ui` at this stage: our Modern frontend is product-specific and already substantially implemented. Evaluate launcher components selectively only if they replace an existing UI seam with fewer regressions.

## Competing spike B: keep UR-Recomp core and take Ema's execution

Starting from **latest** UR-Recomp main in a separate isolated branch, apply the minimum compatible framework changes, in dependency order, using exact upstream commits, not a fork-head merge:
1. Test and opt-in `g_hdma_oamdata_at_10c` plus the title-level enablement, measuring actual original/native sprite high-table and scanline-0/112 behavior. Keep the change disabled by default until validated.
2. Bring clock-driven HVBJOY (`96b7e9f5`) together with its beam-frame ownership dependency, then `paced_bus` (`b7b4318f`) only if source/recompiler/runner integration builds repeatably. These are timing semantics changes, not presentation tweaks.
3. Native guest continuation/handoff (`5882addc`) and pinned M/X variant/landing support (`ce196a45`) behind an explicit feature switch; prove no return-stack corruption, silent interpreter fallback or timing regression.
4. Trial the real `$00:0199` HLE MVN/RTL trampoline from `src/gen_stubs.c` with exact 8/16-bit index mode and cycles, only if interpreted work is measurable and significant. No synthetic behavior or fabricated completion.
5. Regenerate from the **verified USA ROM** and run the same shared vertical-slice input, terminal-result, OAM and host-product tests as spike A.

First map changes against `tools/toolchain-entries/snesrecomp.json` and the offline staged-source machinery. The existing Modern host hooks, widescreen/OAM/presentation modifications, P2 input handling and `source-gamepad` integration have a real conflict surface. Preserve their ownership; don't assume `git apply` success proves behavioral compatibility.

## Same acceptance scorecard for both spikes

| Gate | Minimum witness | Admission |
| --- | --- | --- |
| Startup and usability | Clean Windows launch, ordinary controller, no developer shortcuts, visible root, race, return to Records and quit | Required |
| Fidelity | Real USA-ROM full non-Dragster Race, multi-lap Circuit and scored 45-second Stunt against authentic oracle input/result | Required for core parity; keep 0/45 until independently checked |
| 2P | Two physical/logical seats with independently governed input, uncorrupted P1/P2 OAM/HDMA, leg/result, pause/restart | Required |
| Presentation | Correct authentic 4:3/7:6 baseline; real +24 horizontal world extension, non-cropped 16:9, coherent Original/HD fallback; native 4K output | Required for differentiation |
| Persistence | Existing profile/save/progression and `.urrun`/`.urghost` open across fresh processes; no loss or ghost/result fabrication | Required |
| Measurement | Record build reproducibility, clean CI time, frame pace/latency, interpreter share, rendering fallback, diff and outstanding defects | Required |
| Maintenance | Enumerate needed framework patches, local code deltas, extra owners and source-closure obligations; preserve provenance | Selection criterion |

No single small test can substitute for these player outcomes. Use **one reusable route/evidence runner** for both spikes; do not fund a third universal framework or count masked WRAM parity as game completion.

## Stage gates and stop rules

- **Gate 0, approximately 8–12 productive agent hours:** make upstream title executable independently, compile the existing application from clean source, record available runtime baselines and gap list; no code migration until both baselines are reproducible. Hard-fail missing ROM/runtime/prerequisites as blockers, not false successes.
- **Gate 1, up to 20 productive agent hours per spike:** complete native host + stock/2P/real widened display + at least one product hook. If spike A requires replacing our entire host stack or loses controller authority, stop A and evaluate B. If B's patched framework needs rewrites across most existing toolchain patches, stop B and evaluate A. **40 hours maximum for the initial competition**, not an estimate for product completion.
- **Gate 2, 8–12 hours:** run common acceptance and maintenance/cost comparison. Select A or B by correct player-visible results first, engineering cost second, performance third. If both fail, keep proven main, isolate and fix the cheapest named blocker. No unbounded dual-track work.
- **After selection:** deliver **one** player-facing vertical slice before pursuing full 45-course breadth, speculative microarchitecture or independent alternate launchers. Slice: Modern root → racer/profile selection → stock/HD 16:9 race → real result → replay/Records → repeat or quit. Count every released feature against the existing QA ledger.

These are **engineering-effort ceilings/decision checkpoints**, not wall-clock promises or guaranteed completion costs. A demonstrable new P0 player-data corruption or gameplay correctness issue is an explicit scope exception with its own tracked fix.

## Replace/retain/delete rules

| Existing work | Action after selection |
| --- | --- |
| Hand-translated machine-code semantics, duplicate cfg and incomplete execution tracing | **Replace** with proven upstream versions if parity and regeneration show no regressions; retain our PAL/prototype homolog notes as independent comparison oracle |
| Our SNESRecomp fork/staged archive and patch list | **Replace as an isolated whole or selectively upgrade**, whichever passes Gate 2. Never leave two runtime sources of truth in the shipping product |
| Original ROM/route provenance, 45-course census, Snes9x acceptance and QA release ledger | **Retain** independent proof gates; avoid treating upstream self-comparisons as proof of our integration |
| Modern 5-destination UI, input focus policies, profile chooser, native controller glyphs | **Keep and adapt** via host ABI, not rewritten against Ema's generic launcher |
| HD art assets, source-visible sprite gating, OAM/PPU bridge, real widened viewport | **Keep and adapt**: these are product-defining; remove renderer plumbing only when replaced with visibly correct test parity |
| Records, tour/progression, replay, ghost and tournament storage/transaction invariants | **Keep**, preserve live data compatibility and fault tests; adapt guest-state boundaries, not storage authority |
| Platform prototypes (Switch/macOS/Browser), web lockstep | **Defer** until the selected Windows vertical slice ships; source captured with provenance |
| Redundant investigation and broad QA duplicating passed high-confidence evidence | **Stop/de-scope explicitly**, linked to replacement evidence; never simply erase facts, proofs or known red defects |

## Immediate ownership / operational instructions

Assign one agent to spike A and a separate agent to spike B, with **one** integration/evidence owner for the shared route and scoring harness; each stays in its own branch, no changes to production `main` until Gate 2. Coordinate with QA-01/07, QA-08, QA-02/03 and QA-05/09 so their current work is either reused or deliberately paused, not overwritten. Use PRs for source changes, merge bounded validated improvements, update `docs/PROJECT-PLAN.md`, `docs/WORK-QUEUE.md` and the authoritative QA ledger **only with real results**.

First useful deliverable is a **side-by-side playable evidence report**, not another documentation-only framework transplant. Every transplant gets an upstream SHA, local patch, affected symbols/components, rollback command, regression fixtures and measurable before/after.
