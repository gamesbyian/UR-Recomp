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

Use it before writing bespoke tile/palette conversion unless Uniracers data demonstrably needs a custom layer.

### snes2asm + WLA-DX

`snes2asm` can produce configurable LoROM/HiROM disassemblies, trace code paths, extract graphics/tilemaps/palettes/text, and disassemble SPC700 material. WLA-DX supplies the 65816/SPC700 assembler/linker needed for reassemblable projects.

Treat generated disassemblies as working products, not automatically canonical source. Promote symbols and structural findings into project-owned authorities only after validation.

## Additional analysis tools

### cc65 / da65

`da65` supports 65816 and user-supplied information files. Its own documentation notes that 65816 disassembly requires M/X-state knowledge and is best done bank-by-bank. That limitation is useful rather than disqualifying: feed it mode information from traces/CDL instead of pretending static bytes determine operand width everywhere.

Install with:

```bash
python3 tools/bootstrap_toolchain.py --group analysis
```

### Ghidra + ghidra-snes

The pinned `ghidra-snes` extension supplies an SNES ROM loader, SNES-oriented 24-bit 65816 language, memory-map helpers, MMIO/WRAM mirrors, registers and vectors. The pinned extension declares compatibility with Ghidra 12.0.4.

This is a heavyweight interactive workbench, so the bootstrap only pins/checks out the extension source. Install Ghidra separately when a task benefits from cross-references, function/data annotation, or collaborative long-lived static analysis. Keep Ghidra project databases out of Git; export compact symbols/scripts/findings instead.

## Independent emulator workbenches

### bsnes libretro

Pinned as a secondary implementation reference and manual/frame-level oracle. It builds reproducibly through `python3 tools/bootstrap_toolchain.py --tool bsnes-libretro`, but this libretro frontend does not expose `RETRO_MEMORY_SYSTEM_RAM`, so it cannot directly support `snesref`'s WRAM-keyed `until`/dump fixtures.

### Beetle bsnes libretro

Pinned separately as the automated independent state oracle. Its libretro frontend exposes SNES WRAM as `RETRO_MEMORY_SYSTEM_RAM`, which makes it compatible with the existing `snesref` fixture and checkpoint machinery. Build it with `python3 tools/bootstrap_toolchain.py --tool beetle-bsnes-libretro`; CI smoke-builds the core and the independent-reference workflow drives the same first-race fixture through it and Snes9x.

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

Both are pinned under the `agent-debug` group. MesenCE is the community-maintained continuation of Mesen and supplies the SNES debugger/emulator host. `mesen-for-ai` exposes compatible debugger operations to an AI agent headlessly: frame stepping, memory/register inspection, breakpoints, traces, and SNES code/data logging.

```bash
python3 tools/bootstrap_toolchain.py --group agent-debug
```

This is the preferred future route for agent-driven dynamic archaeology when `snesref` cannot answer the question directly. The pinned MesenCE source is intentionally clone-only for now; building/packaging it should be added only when the first headless experiment proves the exact Linux build contract we need.

## Patching

### Floating IPS

Pinned as an on-demand IPS/BPS CLI-capable patcher. Use patches rather than duplicate modified ROMs when preserving third-party fixes, controlled experiments, or reproducible ROM modifications. The original bytes and patch provenance remain separate evidence.

Build the pinned CLI-capable binary with:

```bash
python3 tools/bootstrap_toolchain.py --group patching
```

The bootstrap deliberately builds the CLI target with `make TARGET=cli`, avoiding GTK entirely, and verifies that the `flips` artifact exists. Use `--clone-only` only when source inspection, rather than a usable patcher, is the goal.

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
