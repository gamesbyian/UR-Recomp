# Research and development toolchain

The repository should make useful tools reproducible without turning every checkout into a workstation image. Pinned third-party source checkouts/builds live under ignored `.tools/` and are described by `tools/toolchain.json`.

List available tools:

```bash
python3 tools/bootstrap_toolchain.py --list
```

Install the default scriptable core set:

```bash
python3 tools/bootstrap_toolchain.py
```

Print the recommended Ubuntu packages first if needed:

```bash
python3 tools/bootstrap_toolchain.py --system-packages
```

The bootstrap script never runs `sudo` or build commands through a shell. Manifest build steps are argument vectors, pinned revisions must be full commit IDs, and declared build artifacts are checked after successful builds. Run `python3 tools/bootstrap_toolchain.py --validate` for a no-network schema/integrity check.

Repository-owned third-party migration state is tracked separately in `third_party/manifest.json`. Inspect it through:

```bash
python3 tools/bootstrap_toolchain.py --island-status
python3 tools/validate_island.py --status
```

When a component is marked `vendored`, bootstrap prefers that repository-owned source over the external Git pin. `--offline` is fail-closed: it permits only repository-owned buildable sources and exits before any GitHub fetch for pending/unclassified tools. This is intentionally strict so an "offline" run can never succeed by quietly touching the network.

`mesen-for-ai` and the islanded `snes2asm` source tranche use `tools/install_pure_python_tool.py` instead of pip/build isolation. The helper copies a repository-owned pure-Python package into the isolated venv from an explicit source directory and can generate declared console launchers. `snes2asm` installs repository-owned PyYAML 6.0.3 first, then its patched CLI package. Do not replace these paths with `pip install` unless a measured reason justifies restoring a registry/build-backend closure.

Project patches are applied differently depending on source ownership. External bootstrap sources are real nested Git checkouts and are patched from their checkout root. Repository-owned vendored sources are staged under ignored `.tools/` without nested Git metadata, so bootstrap applies their patches from the UR-Recomp root with an explicit `--directory` prefix; otherwise Git can discover the parent worktree and accept a patch without touching the staged source.

Vendor provenance lives outside the hashed source tree under `third_party/provenance/`; records for `mesen-for-ai`, `snes2asm`, and its PyYAML closure document the exact upstream revision/tree, retained subset, exclusions, license and install contract.


## Already in the repository

### SNESRecomp and snesref

The pinned `snesrecomp` submodule remains the primary recompilation stack. Its `tools/snesref` program is the preferred differential oracle harness: it can drive a real libretro SNES core, run scripted inputs, emit frame-selected dumps, capture WRAM changes, and compare interpreter behavior against the recomp runtime.

Do not create a second project-specific differential harness until `snesref` is proven insufficient.

### Project-native Python analysis

The scripts in `tools/` own reproducible ROM fingerprinting, reference-build comparison, RNC discovery/decompression, and current targeted analysis. Prefer extending a project-native script when the requirement is Uniracers-specific and small.

## Core scriptable tools

### Snes9x libretro core

Default interpreter behind `snesref`. The pinned upstream revision is also the emulator revision already used as research evidence for Uniracers-specific OAM handling. Upstream builds the libretro core directly with `make -C libretro`.

Use it for deterministic reference execution, scripted-input traces, WRAM comparisons, frame/audio capture, and first-divergence work.

### SuperFamiconv

Command-line SNES graphics converter for palettes, planar tile graphics, maps, and image round trips. The pinned v0.12 line is the upstream Rust rewrite. It can emit native binary and JSON/image forms, making it useful both for discovering graphics structure and later for a custom-course/asset pipeline.

UR-Recomp now owns a pruned copy of the pinned Rust CLI source plus its exact Cargo dependency closure under `third_party/src/superfamiconv/`. The source-local `.cargo/config.toml` redirects crates.io to the committed `vendor/` tree, and the toolchain contract requires `cargo build --release --locked --offline`. The acquisition proof used an empty `CARGO_HOME`, so a successful build cannot be attributed to a hosted-runner registry cache.

Use it before writing bespoke tile/palette conversion unless Uniracers data demonstrably needs a custom layer.

### snes2asm + WLA-DX

`snes2asm` can produce configurable LoROM/HiROM disassemblies, trace code paths, extract graphics/tilemaps/palettes/text, and disassemble SPC700 material. UR-Recomp now owns the exact pinned WLA-DX v10.7 source closure needed for reconstruction under `third_party/src/wla-dx/`: common assembler/linker code, the 65816 backend, instruction-table generator and `wlalink`. Other CPU backends and upstream test/documentation/platform material are intentionally excluded.

The project patch `tools/patches/wla-dx-ur-recomp.patch` restricts upstream CMake to `wla-65816` and `wlalink`, matching the artifacts declared in `tools/toolchain.json`. The closure has no package-registry dependency; it requires only ordinary host CMake/C compiler/libc/libm prerequisites.

Treat generated disassemblies as working products, not automatically canonical source. Promote symbols and structural findings into project-owned authorities only after validation.

## Additional analysis tools

### cc65 / da65

`da65` supports 65816 and user-supplied information files. Its own documentation notes that 65816 disassembly requires M/X-state knowledge and is best done bank-by-bank. That limitation is useful rather than disqualifying: feed it mode information from traces/CDL instead of pretending static bytes determine operand width everywhere.

Install with:

```bash
python3 tools/bootstrap_toolchain.py --group analysis
```

### Ghidra + ghidra-snes

The pinned `ghidra-snes` extension supplies an SNES ROM loader, SNES-oriented 24-bit 65816 language, memory-map helpers, MMIO/WRAM mirrors, registers and vectors. The repository owns a pruned copy of the exact pinned extension source, language/data definitions and build metadata under `third_party/src/ghidra-snes/`; the extension declares compatibility with Ghidra 12.0.4.

This remains a heavyweight interactive workbench. `bootstrap_toolchain.py --offline --tool ghidra-snes --clone-only` stages the preserved extension source without network access, but UR-Recomp does not claim an offline Ghidra/Gradle/Maven build. Install Ghidra separately when a task benefits from cross-references, function/data annotation, or collaborative long-lived static analysis, and provide the compatible Gradle/Maven build environment when compiling the extension. Keep Ghidra project databases out of Git; export compact symbols/scripts/findings instead.

## Visual-reference and upscaling workbenches

### RetroArch + Slang shaders

RetroArch is pinned as an on-demand presentation/reference frontend, and the Libretro Slang shader corpus is pinned separately as data. Their project role is **comparative visual evidence**, not gameplay authority.

Use a small curated preset matrix against identical source frames and, later, isolated extracted assets. The initial families should include:

- nearest-neighbor integer scaling as the factual control;
- Scale2x/ScaleNx-style conservative edge continuation;
- HQx;
- xBR/xBRZ;
- SABR;
- ScaleFX;
- Super-xBR;
- simple bilinear/bicubic/Lanczos controls where available;
- representative NTSC RGB/S-Video/composite treatments;
- a deliberately small set of CRT reconstructions.

The output is an ensemble of hypotheses about high-resolution contour/edge structure and period display appearance. No filtered result becomes canonical art by itself. Agreement across unrelated algorithms is evidence; disagreement identifies ambiguous source pixels that deserve explicit design review.

Prefer offline/image-domain implementations for bulk processing of extracted PNG assets when equivalent output is available. Launch an emulator/frontend only when the result depends on PPU composition, shader passes, aspect/display behavior, NTSC simulation, or another emulator-specific surface.

### bsnes-hd

bsnes-hd is pinned as a specialist workbench. Use it selectively for higher-resolution rendering and layer/sprite-isolation experiments where those capabilities answer a concrete graphics question. Do not treat HD Mode 7 as a generic sprite upscaler, and do not make bsnes-hd part of routine CI unless a measured workflow demonstrates unique value.

### Capture reproducibility

Any promoted visual-reference capture must record at least:

- canonical ROM/build identity or extracted asset hash;
- emulator/core/frontend revision;
- shader/preset identity and parameters;
- source frame or semantic asset key;
- source and output dimensions;
- aspect/pixel-aspect handling;
- color-space/NTSC/CRT assumptions;
- whether the input was a composited framebuffer or isolated asset/layer.

The planned capture harness should make the same semantic source fan out into multiple deterministic reference outputs so future asset-generation work receives a compact reference dossier rather than one arbitrary upscale.

## Headless execution posture

Repository automation should prefer tools that are natively command-line, library-style, or explicitly designed for headless control. `tools/toolchain.json` records one of three statuses for every pinned tool:

- **native**: the UR-Recomp build/runtime surface is CLI, libretro, or a headless daemon and needs no desktop session;
- **wrapped**: the tool itself still needs a display-capable host, but an established wrapper supplies that environment deterministically;
- **manual**: an interactive workbench kept off default CI.

Current posture:

| Tool family | Status | Repo behavior |
|---|---|---|
| Snes9x / bsnes / Beetle libretro | native | Shared libraries driven by `snesref`; no emulator GUI is built or launched. |
| Flips | native | Builds `TARGET=cli`; GTK is intentionally excluded. |
| SuperFamiconv | native | Release CLI only. |
| snes2asm | native | Python CLI installed in an isolated venv; unused GUI code is not an execution dependency. |
| cc65 / da65 | native | Build only the `da65` target instead of the compiler suite, libraries, docs, utilities and samples. |
| WLA-DX | native | Build only `wla-65816` and `wlalink`, not every CPU assembler and ancillary target. |
| mesen-for-ai | native bridge | MCP/JSON-RPC daemon is headless. |
| MesenCE | wrapped | Upstream automation still launches the actual Mesen binary through `xvfb-run -a ... --testrunner`; isolated HOME/settings disable random power-on state and permit Lua I/O/network access. |
| Ghidra, ares, DiztinGUIsh, bsnes-plus, bsnes-hd | manual | Source pins/workbenches only; never default CI dependencies. |
| Slang shaders | native data | Data-only pinned shader corpus; runtime posture depends on the chosen frontend. |
| RetroArch visual-reference route | wrapped | Keep off default CI until a deterministic Xvfb/software-or-GPU capture experiment establishes the cheapest stable runtime contract. |

Do not patch a GUI-heavy workbench merely to call it "headless." The criterion is wall-clock/resource value. For MesenCE in particular, the supported `mesen-for-ai` path still requires Xvfb, but it does not require a visible desktop or human interaction. A custom GUI-stripped Mesen fork would be justified only by measured startup/runtime savings large enough to outweigh carrying that fork.

Fresh bootstrap is also optimized for CI: initialize an empty Git checkout and fetch only the exact pinned commit with blob filtering, rather than cloning the default branch first. Python venv creation uses the stdlib-provided pip instead of performing an unconditional network upgrade.

A before/after GitHub Actions smoke comparison on the same audit branch showed the build-scope changes were material: WLA-DX fell from roughly 83 s to 19 s when restricted to `wla-65816` + `wlalink`, and cc65 fell from roughly 57 s to 20 s when restricted to `da65`. Hosted-runner timings are noisy, so these are representative measurements rather than performance contracts, but the reductions are large enough to justify the narrower builds.

## Independent emulator workbenches

### bsnes libretro

Pinned as a secondary implementation reference and manual/frame-level oracle. It builds reproducibly through `python3 tools/bootstrap_toolchain.py --tool bsnes-libretro`, but this libretro frontend does not expose `RETRO_MEMORY_SYSTEM_RAM`, so it cannot directly support `snesref`'s WRAM-keyed `until`/dump fixtures.

### Beetle bsnes libretro

Pinned separately as the automated independent state oracle. Its libretro frontend exposes SNES WRAM as `RETRO_MEMORY_SYSTEM_RAM`, which makes it compatible with the existing `snesref` fixture and checkpoint machinery. UR-Recomp owns the complete pinned Linux/libretro source tree under `third_party/src/beetle-bsnes-libretro/`, omitting only upstream CI metadata and Android packaging because the entire fidelity-sensitive source closure is small enough that deeper pruning would add risk for little value. Build it with `python3 tools/bootstrap_toolchain.py --offline --tool beetle-bsnes-libretro`; CI smoke-builds the repository-owned core and source changes trigger the independent-reference workflow, which drives the same first-race fixture through it and Snes9x.

### ares

Accuracy/preservation-focused descendant of higan/bsnes. Use for independent manual behavior checks or emulator-source archaeology. It is large and GUI-oriented, so it remains an on-demand workbench rather than a CI dependency.

### DiztinGUIsh + bsnes-plus

Both are now pinned as on-demand workbenches. DiztinGUIsh can consume live CPU trace information from its compatible bsnes+ workflow, track 65816 execution-state details that static disassembly cannot infer safely, classify code/data, and export reassemblable assembly. The ordinary bsnes-plus pin is separately useful for breakpoints, ROM/RAM inspection, trace logging, and VRAM/OAM/tilemap debugging.

Install exact sources without making either part of the default build:

```bash
python3 tools/bootstrap_toolchain.py --tool diztinguish --tool bsnes-plus --clone-only
```

Treat workbench databases and bulk trace logs as ignored scratch products. Promote only reproducible scripts, compact exports, symbols, and evidence.

### MesenCE + mesen-for-ai

Both are pinned under the `agent-debug` group. MesenCE is the community-maintained continuation of Mesen and supplies the SNES debugger/emulator host. Its pin was deliberately advanced from the June 2.2.1 release to the 2026-09-26 head because intervening upstream work includes a SNES mid-scanline PPU register fix, corrected Lua callback addresses for non-default memory types, and debugger fixes that directly overlap UR-Recomp's raster and agent-debug use cases. `mesen-for-ai` exposes compatible debugger operations to an AI agent headlessly: frame stepping, memory/register inspection, breakpoints, traces, and SNES code/data logging.

```bash
python3 tools/bootstrap_toolchain.py --group agent-debug
```

This is the preferred future route for agent-driven dynamic archaeology when `snesref` cannot answer the question directly. The pinned MesenCE source is intentionally clone-only for now; building/packaging it should be added only when the first headless experiment proves the exact Linux build contract we need.

## Patching

### Floating IPS

Pinned as an on-demand IPS/BPS CLI-capable patcher. Use patches rather than duplicate modified ROMs when preserving third-party fixes, controlled experiments, or reproducible ROM modifications. The original bytes and patch provenance remain separate evidence.

UR-Recomp owns a pruned copy of the exact CLI/core source plus the upstream-bundled libdivsufsort implementation under `third_party/src/flips/`. It has no package-registry dependency: the only build boundary is the host C++ toolchain.

Build the repository-owned CLI binary with:

```bash
python3 tools/bootstrap_toolchain.py --offline --group patching
```

The bootstrap deliberately builds `make TARGET=cli`, avoiding GTK and Windows frontends entirely, and verifies that the `flips` artifact exists. Use `--clone-only` only when source inspection, rather than a usable patcher, is the goal.

## Generic conversion/inspection utilities

The recommended system package set includes:

- `ffmpeg` for lossless frame/video/audio extraction and comparison;
- ImageMagick for deterministic image conversion/cropping/compositing;
- `jq` for compact JSON analysis;
- `ripgrep` for cheap repository/source discovery;
- `file`, compiler/build essentials, CMake/Ninja, Rust/Cargo, Python venv, and SDL2 development files.

These solve a surprising amount of archaeology without adding bespoke code.

## What we are deliberately not installing everywhere

Avoid default installs of large GUI emulators, full Ghidra, historical editors, tile GUIs, or multiple near-identical assemblers. Catalog them when useful; bootstrap them only when an active workflow needs them.

Avoid using an emulator's debugger output as an undocumented one-off artifact. When a manual debugger reveals something important, turn it into a stable address/symbol, trace, script, patch, or reproducible local test.

## Tool promotion rule

A tool earns a permanent default slot when it is:
1. repeatedly useful to current work;
2. scriptable/reproducible;
3. reasonably cheap to install/build;
4. not redundant with an existing project or SNESRecomp facility.

Everything else can remain an on-demand pinned workbench.


## Bootstrap trust model

`tools/toolchain.json` distinguishes tools with a reproducible project-owned build recipe from tools whose source is merely pinned for manual use. A successful checkout of a heavyweight emulator or debugger is not described as an installation.

The bootstrap validates before network or build work:

- repository-local installation root;
- unique conservative tool IDs;
- HTTPS GitHub source;
- full lowercase 40-hex revision;
- explicit `build` or `manual` install mode;
- argv-vector build commands with only known placeholders.

This is intentionally stricter than upstream build documentation. The manifest is an execution contract for this repository, not a bag of shell snippets.


Python-packaged third-party tools are installed into separate virtual environments under `.tools/venvs/<tool-id>/`. This avoids dependency coupling between unrelated research tools while keeping the entire installation disposable.


## Project-owned patches

A build-mode tool may declare hash-pinned patches under `tools/patches/`. Bootstrap order is deliberately strict:

1. verify the manifest and exact upstream commit;
2. reset and clean the disposable checkout;
3. verify each patch SHA-256;
4. require `git apply --check`;
5. apply the patch;
6. build and verify typed artifacts.

`--clone-only` stops before patching, so it always leaves an exact upstream source checkout for comparison. Keep patches small and purpose-specific; when an upstream pin changes, reconcile or remove them explicitly.
