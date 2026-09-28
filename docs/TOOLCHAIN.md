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

The bootstrap script never runs `sudo`.

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

Pinned as a secondary libretro oracle. Use it to cross-check emulator-sensitive behavior when Snes9x and recomp disagree, especially PPU/OAM/timing questions. It is intentionally not part of default bootstrap/build cost.

### ares

Accuracy/preservation-focused descendant of higan/bsnes. Use for independent manual behavior checks or emulator-source archaeology. It is large and GUI-oriented, so it remains an on-demand workbench rather than a CI dependency.

### Mesen / DiztinGUIsh

Both are potentially excellent debugger-oriented workbenches. Mesen 2's original repository was archived in June 2026 and its development moved, while DiztinGUIsh emphasizes trace-assisted collaborative 65816 disassembly. Do not pin either into the default bootstrap until a concrete workflow requires it and the current upstream/format is selected.

## Patching

### Floating IPS

Pinned as an on-demand IPS/BPS CLI-capable patcher. Use patches rather than duplicate modified ROMs when preserving third-party fixes, controlled experiments, or reproducible ROM modifications. The original bytes and patch provenance remain separate evidence.

Install sources with:

```bash
python3 tools/bootstrap_toolchain.py --group patching --clone-only
```

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
