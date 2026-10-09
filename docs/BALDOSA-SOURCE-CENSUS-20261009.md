# Exhaustive Baldosa repo intake and engineering audit

**Review date:** 2026-10-09. **Exact source:** [baldosa/uniracers-recomp](https://github.com/baldosa/uniracers-recomp/tree/10b864b9d14a7b7416dd909eb7b054c88faef101) at commit `10b864b9d14a7b7416dd909eb7b054c88faef101`. **Machine-readable every-path audit:** [`analysis/data/baldosa-upstream-file-census.json`](../analysis/data/baldosa-upstream-file-census.json). That index individually identifies **all 210 Git tree entries: 186 files, 22 directories, 2 gitlinked submodules**, each with path, exact upstream SHA, size where applicable, purpose and import/retention disposition. An upstream update requires a **new pinned census**, not silently mixing revisions.

## Intake is exhaustive for hand-maintained contents

- **85 of 186 files imported byte-for-byte** under `reference/imported/reverse-engineering/baldosa-uniracers-recomp/`, with `reference/imported/MANIFEST.json` byte count, upstream Git blob SHA and integrity labels. They include **all nonempty hand-maintained sources, tests, scripts, configurations, notes and browser code**, plus the generator's cache index. The existing fork `gamesbyian/uniracers-recomp` also retains the full original repository.
- **94 machine-generated files** remain indexed by immutable upstream Git blob SHA and size, rather than copied: ROM-derived translated C (`src/gen/bank*_v2.c`), compiled dispatch and program manifest, generated `recomp/funcs.h`, and regeneration placeholders. `src/gen/.snesrecomp-cache.json` is an exception **already imported**, to retain compilation statistics and input/output digests. The human-written `src/gen/README.md` is also imported.
- **Five checked-in CPython 3.13 `tools/__pycache__/*.pyc` files** are indexed but intentionally excluded. They are bytecode caches, not extra functions or tests.
- **Two empty `.gitkeep` placeholders** are indexed but intentionally excluded.
- **Two pinned external submodules**, each recorded as Git gitlinks in the census, are deliberately not substituted for UR-Recomp's existing framework: `baldosa/snesrecomp@075fbe4c8e0d97b0013be541795c39cb644a9709` and `RetroPortingToolKit/recomp-ui@7e884a227accea91ddb378671bd49aaeeea13371`. Their entire histories are separate projects; the top-level tree includes exact immutable pointers.
- **No source or generated C from Baldosa is linked into our production target**, no root CI workflow was overwritten, and the `snesrecomp` submodule pin remains owned by the existing runtime/QA lanes. All imported `.github` files are underneath `reference/imported` and cannot trigger as workflows.

## Every upstream folder

| Folder | Role |
|---|---|
| `.github/` | GitHub Actions workflow directory |
| `.github/workflows/` | Native full-AOT, web Pages, and alternative setup-host packaging pipelines |
| `decomp/` | Human-maintained exact-USA disassembly symbols, RAM map, hardware defines, and subsystem partitions |
| `docs/` | Upstream research specifications and agent development records |
| `docs/superpowers/` | Research planning and architectural specifications |
| `docs/superpowers/plans/` | October 6 implementation plan with checked and outstanding steps |
| `docs/superpowers/specs/` | Initial native-AOT and matching disassembly architecture decisions |
| `mods/` | Player-defined mod package area |
| `mods/preloaded/` | Checked-in default-disabled mod catalog contract |
| `mods/preloaded/packages/` | Empty placeholder for reviewed .snesmod packages |
| `recomp/` | Bank-specific 65816 analysis directives, function variants, names, and generated prototypes |
| `scripts/` | Setup-host ZIP packaging and release scripts |
| `src/` | Game-specific host initialization, frame driver, HLE trampoline, web hooks, and generated guest code |
| `src/gen/` | Machine-generated AOT 65816 C translation, dispatch tables, program manifest and cache |
| `tests/` | Deterministic gameplay input and UI oracle routes |
| `tests/routes/` | Nine input scripts for gameplay, multiplayer, menu and SRAM scenarios |
| `tools/` | Native analysis, decompilation, state-diff, routes and build utilities |
| `tools/__pycache__/` | Accidentally tracked CPython 3.13 bytecode caches; not source |
| `tools/cross/` | Zig/aarch64 build, archiver, linker and qemu runner wrappers |
| `tools/decomp/` | Matching Asar generator, dead-code classifier, naming and independent tests |
| `tools/web/` | Emscripten website builder and settings INI parser tests |
| `web/` | Browser HTML/JS launcher, persistent settings, WebRTC transport and debug UI |

The JSON inventory maps **every file** individually, including every multi-megabyte `src/gen/bank..._v2.c` translation unit. These are outputs produced by `tools/regen.sh` from source-ROM bytes, tracked analyzer configuration and its pinned SNESRecomp fork, not independently hand-authored game systems. The source tree is available through the existing `gamesbyian/uniracers-recomp` fork for on-demand inspection without copying 67 MB of duplicative generated content.


**Native framework delta indexed (2026-10-09):** [`BALDOSA-FRAMEWORK-DELTA-20261009.md`](BALDOSA-FRAMEWORK-DELTA-20261009.md) enumerates 86 ancestor commits/121 changed files between our pinned SNESRecomp and Ema's fork, with the game-specific OAM patch preserved but **unapplied** in `analysis/patches/baldosa-oam-address-pin.patch`. This does not supersede the active QA-08 controller/graphics lane or authorize a global framework upgrade.

## High-value technical seams, after inspecting source

### AOT execution and decompilation

The separate game shim (`src/main.c`) uses the shared SNESRecomp desktop host; `src/game_rtl.c` delegates beam-aligned fields/interrupts/PPU drawing and enables native continuation handoff. Ema's `src/gen_stubs.c` contains an authentic RAM-resident `MVN`/RTL HLE trampoline, including CPU register, destination-bank and cycle behavior, not a fake success result. `recomp/bank*.cfg` provide manually proven indirect entries, register variants and direct/ROM-mirror roots. The imported generator cache reports **1,577 emitted variants**, **11 LLE variants**, and **821 roots** across eight analyzed banks. Those are codegen cache statistics, not measured fallback share or proof of event completeness. Upstream's README claims just seven 6502-emulation-mode boot instructions remain interpreted on the nine scripted routes; our project has **not independently run that executable**.

The decomp path (`tools/decomp/decode_dump.py`, `gen_disasm.py`, `apply_names.py`, `export_names.py`, `ownership.py`, `annotate_gen.py`, `build.sh`) builds a byte-identical Asar reconstruction, linking its `decomp/ram.txt` and `decomp/symbols.txt` to the analyzer's generated C. Names, ownership and dead-code filters are now entirely accessible locally as reference source; they are not automatically canonicalized into UR-Recomp. Existing `tools/query_baldosa_symbols.py` and `tools/build_baldosa_symbol_crosswalk.py` should be the first entrypoints.

### Original/reference course and 2P semantics

Nine upstream `tests/routes/*.txt` fixtures cover attract, Dragster, Zoom Zoo, ordinary 2P, split-screen 2P, VS, League, Define and Records. `tools/routes.sh`, `run_ref.sh`, `run_route.sh`, `statetrace.py`, `firstdiff.py` and `compare_dumps.py` are now preserved with their tests. Their comparisons use explicitly masked WRAM timing-phase state; optional OAM is compared at exact checkpoints. Their runner grammar (`until16`, `turbo on`, `p2:` buttons) is **not the same as** UR-Recomp's pre-existing QA syntax. Execute adaptations under the real guest with a valid course, active race, lap/contact sequence and **settled** result before claiming a 45-course gate pass.

Their `src/main.c` sets `g_hdma_oamdata_at_10c=true`, a game-specific opt-in to their framework's extra HDMA OAM-address pin (`runner/src/snes/dma.c` at `baldosa/snesrecomp@075fbe4c`). This is unusually relevant to our independently examined `0x218` high-OAM byte and P1/P2 riders at scanlines 0/112. Integrate only an isolated runtime fix after authentic emulator/native contradictory OAM evidence; don't sidestep source-visible-rider and exact-stock tests.

### Browser, multiplayer and platform paths

The `web/` frontend stores game/ROM/save/settings in IDBFS, offers per-seat keyboard/gamepad binding, optional graphics filters and download/import of SRAM, and exposes a debug overlay with frame cost, audio queue and underruns. `src/web_netplay.c` and `web/netplay.js` run **WebRTC reliable ordered input lockstep** with a 3-frame lead and a WRAM CRC every 120 frames, initial ROM digest comparison and host-supplied SRAM. This is a coherent experimental browser architecture, but has no retrieved independent latency, reconnect, desync-resynchronization or process-reset acceptance. Browser aspect selections affect page presentation, and **do not prove true world-extending widescreen**. It belongs in a separate host/platform experiment after Windows correctness, not in the QA-01 simulation route.

The `tools/cross/` Zig/aarch64 and QEMU wrappers demonstrate an independent portability route; native Linux/Windows workflows, Emscripten `tools/web/build.sh` and setup-host zip packaging are all preserved as **reference**, not active workflows. `mods/preloaded` is an empty default-disabled catalog, not a collection of mods.

### A genuinely actionable upstream inconsistency

The **`.github/workflows/build.yml` and Pages build use committed `src/gen/*.c`**, consistent with Ema's README. However, their separate **human-triggered `.github/workflows/release.yml` lines 195–205 explicitly fail if *any* generated `src/gen/*.c` or `recomp/funcs.h` exists**, while both are present at the pinned main commit. On its face that release path must fail at this preflight. This is an upstream packaging/workflow defect candidate, **not** proof the shipped native/web players fail. If contributing upstream, propose a separate clean setup-host packaging tree or rewrite the gate rather than deleting working AOT source.

## Priority changes to our existing plan

1. **QA-01/07:** use the imported Zoom Zoo route, plus original/native entry and terminal result gates, to turn an observed driving script into a full circuit result. Also try the Dragster and stunt controls once an independently valid witness exists; keep exact **0/45** until proven.
2. **QA-08:** reproduce upstream HDMA OAM target correction in the *pinned* runtime, preserve both P1 and P2 source-visible sprites, stock and HD, at the seam, and port only the smallest required framework change if necessary.
3. **QA-02/03/Records:** inspect fixed reads of indexed SRAM result table `$77:0618` versus real P1/P2 race result blocks before a proposed storage fix, as documented by `BALDOSA-SYMBOL-CROSSWALK-FINDINGS-20261009.md`.
4. **AOT/runtime architecture:** on an isolated test branch, benchmark the optional native resume/interrupt handoff, `paced_bus`, function variants and HLE RAM trampoline against exact original/native parity and actual interpreter share. Reuse the existing CI performance budget and avoid replacing all framework modifications in a single merge.
5. **Decomp accelerated archaeology:** compare Ema's instruction/data filters and function labels to our PAL/prototype homologs and distinguish independently confirmed names from plausible ones. Don't do 1,300 name-only PRs.
6. **Deferred until Windows guest and player QA are solid:** browser, online play, additional Linux/ARM64 packaging, new launcher, mods. These are preserved to avoid future rediscovery but are **not release gates for Windows alpha**.

## Validation and limitations

The whole upstream Git tree was enumerated: no unknown file/folder role in the machine-readable census, and all **85** imported source blobs were SHA/size-compared to their exact upstream counterparts before committing. The import manifest is consumed by our existing `tools/audit_imported_references.py` hygiene checker. The source file census is static evidence, not proof these scripts execute in UR-Recomp, that Ema's timing mask is transferable, or that all generated output can be reproduced byte-identically with our own different pinned framework. For live source-variant parity, use a fresh detached clone/worktree with Ema's exact submodule and USA ROM.
