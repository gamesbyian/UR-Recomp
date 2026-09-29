# Tooling Audit Closeout Plan

Last updated: 2026-09-29

This document defines the remaining work needed to close the repository-wide tooling audit. It exists to prevent settled audit questions from being repeatedly reopened and to separate genuine tool-integration work from experiments that now belong to the main reverse-engineering plan.

The audit is substantially complete. The repository has a pinned and provenance-checked toolchain, explicit imported-code policy, deterministic shared-fixture infrastructure, a machine-readable producer/consumer graph, headless execution policy, independent reference cores, symbol fan-out into snes2asm/da65, and documented boundaries between project infrastructure and historical evidence.

## Closeout rule

A tooling-audit item is complete when one of these is true:

1. the tool or handoff is exercised by a deterministic repository test or fixture;
2. the interface is documented and deliberately classified as manual/supported rather than automated;
3. the item is explicitly transferred into a main-plan phase because the remaining work is a game-behavior experiment rather than a tooling question;
4. the item is explicitly deferred because measured cost does not justify implementation.

Do not keep the audit alive merely to read more upstream source. Prefer small discriminating fixtures.

## Priority order

### P0 - repository-island acquisition

Owned by the repository-island workstream in `docs/ISLAND-TOOLCHAIN-PLAN.md`. P0-A infrastructure is now underway: the repository has a machine-readable island manifest, hash/license validation wired into repository hygiene, local-source preference in bootstrap, and an explicit fail-closed `--offline` mode. Actual tools are still marked pending until their source/archive and dependency closure land.

Do not duplicate acquisition work here. The tooling audit should consume the islanded tools once available, especially MesenCE/mesen-for-ai, rather than maintaining a second acquisition path.

### P1 - prove Mesen as the third deterministic execution engine

Current state:

- `tools/run_fixture_mesen.py` already maps the shared `wait / press / until / dump / quit` grammar onto mesen-for-ai;
- ROM-free parser/input/frame/dump semantics are tested;
- MesenCE is deliberately pinned;
- the intended Linux route is `Mesen --testrunner` under Xvfb with isolated settings.

Remaining proof:

1. make the pinned MesenCE Linux executable available through the reproducible bootstrap path;
2. run `tests/input/reach-first-race.script` unchanged;
3. emit the same named full-WRAM checkpoints used by native and snesref;
4. compare every checkpoint with the existing comparison tool;
5. record expected emulator variance rather than silently tolerating it;
6. only then upgrade the Mesen handoffs/chains in `tools/tool_interop.json` from supported to verified.

This is the highest-value remaining pure tooling item because it turns a designed adapter into a proven independent engine.

### P1 - validate the Mesen CDL bridge

Goal: one Mesen execution should be able to produce dynamic code/data evidence usable by the static-analysis workbenches.

Do not assume Mesen CDL and bsnes/BizHawk-style usage data are byte-compatible. Build the adapter from evidence.

Required sequence:

1. capture a deliberately tiny known execution corpus in Mesen;
2. inspect Mesen's exact SNES CDL byte flags and ROM-address mapping;
3. capture or synthesize the equivalent known corpus in the target bsnes/DiztinGUIsh/da65 workflow;
4. map only semantics that are proven equivalent;
5. preserve unknown or lossy flags explicitly;
6. write ROM-free unit fixtures for the transformation;
7. verify at least one emitted artifact is accepted by the intended consumer and produces the expected code/data classification;
8. document whether DiztinGUIsh and da65 require one shared compatibility representation or two narrow adapters.

Until this is proven, the interop graph must continue to classify the Mesen-CDL handoffs as candidate.

### P1 - complete canonical symbol fan-out

Current canonical authority:

`docs/SYMBOLS.md -> analysis/generated/symbols.json -> tools/export_symbol_adapters.py`

Already generated:

- snes2asm label/memory YAML;
- da65 label info files.

Still needed:

- Mesen label import;
- Ghidra symbol import.

Implementation requirements:

1. generate both from `analysis/generated/symbols.json`; never create parallel hand-maintained symbol lists;
2. keep address-space conversion explicit and tested, especially LoROM CPU address vs ROM-file offset vs WRAM offset;
3. emit only names/addresses the canonical symbol schema can justify;
4. keep comments/confidence/provenance where the target format can safely carry them;
5. add `--check` coverage so generated files cannot silently drift;
6. update `tool_interop.json` with explicit formats/handoffs.

Mesen supports imported label files and SNES-specific ROM/WRAM memory spaces. Confirm the exact pinned MesenCE import syntax before committing an exporter. Ghidra should use a project-owned importer/script or other deterministic format rather than relying on manual GUI entry.

### P2 - exact graphics round-trip fixtures

This is now part of the Phase E asset-extraction program, not a reason to keep the general tooling audit open.

Prove at least one real Uniracers graphics asset can travel:

`snes2asm native bytes -> SuperFamiconv representation -> native bytes -> reconstruction worktree -> WLA-DX rebuild`

The fixture must catch:

- palette order and bit depth;
- tile order;
- flips;
- map dimensions;
- deduplication behavior;
- base/index offsets;
- transparency/index-zero assumptions;
- any conversion that changes unused/padding bytes.

The acceptance criterion is byte identity at the relevant native asset boundary, followed by reconstruction integrity. Until then SuperFamiconv is an inspection/conversion aid, not an authoritative replacement pipeline.

### P2 - turn emulator assumptions into Phase 4 discriminators

This work is transferred to `docs/WORK-QUEUE.md` Phase 4.

Known source findings already justify tests:

- old and current Snes9x contain named Uniracers handling at the active-display OAM seam;
- jgenesis provides a generic state-machine model;
- MAME's treatment is explicitly approximate at the relevant seam;
- the Canoe patch provides another concrete implementation strategy.

The audit contribution is finished when those source claims have been converted into the smallest deterministic runtime tests. Do not extend this into an open-ended emulator-source survey.

Start with active-display OAM/sprite ripping, then the already-listed SRAM, window/XOR and color-math seams.

### P3 - diagnose Beetle teardown abort if cheap

Current behavior is operationally quarantined: Beetle completes the canonical fixture, writes the terminal checkpoint, then may abort with exit 134 during libretro teardown. The workflow accepts that status only after completed evidence exists.

Investigate only if it is inexpensive to isolate among:

- snesref teardown/lifetime order;
- libretro core teardown behavior;
- pinned historical library/toolchain interaction.

A small fix is welcome. A deep upstream archaeology expedition is not required for audit closure.

### P3 - autonomous-bot policy adaptation decision

The historical Lua source has already yielded valuable state labels and frontend behavior. Historical SMV replay is preferable whenever fixed input is sufficient.

Only port race-driving policy if it adds a capability fixed movies do not provide, such as:

- long-duration state-responsive regression;
- whole-race coverage across variable conditions;
- autonomous recovery from small timing differences;
- broad course traversal without storing a separate movie per case.

If those benefits do not materialize, record the decision and close the item without porting the policy.

### P4 - bootstrap reuse only after measurement

Do not add cache/reuse complexity speculatively.

If repeated same-checkout agent sessions still spend material time rebuilding identical pinned tools, implement a fingerprinted reuse mode keyed at minimum on:

- upstream commit;
- project patch hashes;
- build recipe;
- platform/architecture;
- relevant compiler/toolchain identity;
- expected artifact list.

CI and evidence-producing clean runs should retain the pristine-build path.

## Not active tooling-audit work

The following remain useful project resources, but they are not tooling-audit blockers unless explicitly promoted into executable infrastructure:

- historical SNasm builds/versions;
- Mike Dailly's editor/framework and related missing binaries;
- Canoe patch acquisition/history beyond the already-preserved artifact;
- old level-viewer binaries;
- graphics/MIDI/A0-plotter historical tools.

Likewise, Ghidra, ares, DiztinGUIsh and bsnes-plus do not need heroic headless conversions. Their current pinned/manual role is acceptable unless a concrete workflow proves otherwise.

## GitHub Actions outage handling

The audit must not depend on Actions being available in order to make progress.

During a GHA outage:

- prefer ROM-free unit tests and static validators that can be run locally by an agent with a working checkout;
- prepare fixtures, adapters and documentation without asserting runtime verification that has not occurred;
- do not weaken checks just to make an unverified change mergeable;
- record any required clean post-merge run as housekeeping rather than babysitting the service.

PR #13 was merged during a repository-wide zero-step runner failure after the same code state had already passed the unit suite and nine-tool matrix on its predecessor branch. When Actions is healthy, one clean mainline toolchain run is sufficient housekeeping.

## Audit closure condition

The general tooling audit can be declared closed once:

- Mesen executes the canonical first-race fixture end-to-end or is explicitly rejected with a documented technical reason;
- the Mesen CDL bridge is either verified or split into clearly bounded consumer-specific adapters with fixture coverage;
- canonical symbols fan out to Mesen and Ghidra;
- the remaining graphics/emulator experiments are owned by their main-plan phases;
- Beetle teardown, bot-policy porting and bootstrap reuse each have an explicit fix/defer decision.

After that point, new tool work should enter the repository through ordinary need-driven engineering rather than reopening a global audit.
