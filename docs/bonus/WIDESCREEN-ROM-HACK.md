# Bonus project: emulator-assisted widescreen ROM hack

> **BONUS / NON-BLOCKING / NOT THE SHIPPING ARCHITECTURE**
>
> This workstream explores a modified Uniracers SNES ROM that renders a genuinely wider game world in **bsnes-hd**. It is intentionally quarantined from the native recompilation/remaster line.
>
> Nothing in this document changes the authority of `docs/PROJECT-PLAN.md`, `docs/WORK-QUEUE.md`, `docs/WIDESCREEN.md`, or `docs/WIDESCREEN-RECONNAISSANCE.md`. Agents working the main line should ignore this directory unless a finding is explicitly promoted into a main-line authority with independent evidence.

## Why this exists

bsnes-hd can render additional horizontal columns instead of stretching a 256-pixel picture. For non-Mode-7 scenes this is experimental and game-dependent, and sprites need ROM-side cooperation for correct rendering in the added area.

That makes a real Uniracers widescreen ROM hack plausible as a side project:

```
stock ROM + stock emulator          -> classic SNES viewport
patched ROM + bsnes-hd              -> wider logical viewport / more world visible
native UR-Recomp shipping runtime   -> separate modern-port architecture
```

The bonus project is useful even if it never ships. It can expose exactly which original-game systems assume the classic viewport and can provide a compact experimental oracle for camera, culling, spawn/activation, tilemap, HUD, windowing and split-screen behavior.

## Hard separation rules

1. **No dependency from the main build to this bonus work.**
2. Bonus code, patches, configuration and reports belong under a future `bonus/widescreen-romhack/` tree unless a tool is generally useful enough to live in the shared toolchain.
3. Do not add bonus milestones to the main critical path in `WORK-QUEUE.md`.
4. Do not describe bsnes-hd behavior as evidence for native-renderer correctness without reproducing the relevant behavior independently.
5. Do not change stock-ROM fidelity behavior merely to make the bonus hack easier.
6. If a discovery matters to the main project, promote the *finding*, not the bonus-project dependency.
7. Release artifacts should be patches/configuration/source only. Do not create a second tracked ROM image.

## What bsnes-hd actually provides

Pinned project source: `DerKoun/bsnes-hd@fc26b25ea236f0f877f0265d2a2c37dfd93dfde9`.

The upstream widescreen model adds columns at the left and right of the classic image. Important controls include:

- widescreen enable mode: Mode 7 only or all scenes;
- arbitrary side extension / aspect selection;
- per-background widening, cropping or disabling;
- sprite policies: `clip`, `safe`, `unsafe`, or disabled;
- window-effect fallback/ignore behavior;
- overscan and pixel-aspect choices;
- optional per-ROM `.bso` setting override files.

For the common no-PAR-correction / overscan-off case, upstream documents a 16:9 extension of 64 columns on each side. bsnes-hd also documents an object/sprite widescreen-area limit of 96 columns per side. These are emulator-extension constraints, not original-SNES capabilities.

Upstream source and technical notes:
- https://github.com/DerKoun/bsnes-hd
- https://github.com/DerKoun/bsnes-hd/blob/master/README.md

## Strongest prior art: Super Mario World Widescreen

`VitorVilela7/wide-snes@b988c0afdb98ec778ce4cd140abc1ae3b5828fab` is the reference implementation to study before inventing an Uniracers-specific architecture.

It demonstrates a useful division of responsibility:

- the ROM hack changes game logic that assumes the old viewport;
- bsnes-hd provides the extended presentation surface;
- a same-basename `.bso` file declares emulator-side widescreen behavior;
- source is assembled with Asar;
- distributable builds use BPS rather than distributing modified ROMs;
- several target widths are treated as explicit build modes rather than one magical "widescreen" constant.

The published build currently documents:
- 352x224;
- 384x224;
- experimental wider modes;
- Asar as the patch-oriented assembler;
- FLIPS/BPS for patch transport;
- paired ROM + BSO testing in bsnes-hd.

References:
- https://github.com/VitorVilela7/wide-snes
- https://github.com/VitorVilela7/wide-snes/blob/master/BUILDING.md

## ROM-hacking hygiene adopted here

SNESdev documentation and current community tooling suggest several practices worth making explicit for this lane:

- use **unheadered** ROM images as the canonical working form; 512-byte copier headers are legacy metadata and modern practice generally avoids them;
- assert the exact base-ROM identity before applying any patch;
- preserve/verify the internal SNES header, memory-map mode and checksum when a build changes ROM layout;
- distinguish CPU addresses from file/PC offsets in tools and documentation;
- keep free-space allocations explicit and machine-checkable;
- prefer source patches plus reproducible build steps over hand-edited binary diffs;
- emit a BPS patch for sharing/replay and retain the source patch that produced it;
- use multiple emulators for regression checking, while accepting that the widened image itself is intentionally bsnes-hd-specific;
- keep stock 4:3 behavior as a control build.

SNESdev references:
- https://snes.nesdev.org/wiki/ROM_file_formats
- https://snes.nesdev.org/wiki/ROM_header
- https://snes.nesdev.org/wiki/Tools

## Tool stack

### Already pinned

- **bsnes-hd**: required execution target for the widened presentation.
- **Flips**: CLI BPS/IPS creation/application.
- **MesenCE**: debugger / trace / memory inspection.
- **bsnes-plus**: secondary debugger-oriented workbench.
- **Snes9x / bsnes / Beetle bsnes libretro**: stock-behavior controls and regression oracles.
- **snes2asm, da65, Ghidra+ghidra-snes, WLA-DX**: static-analysis/disassembly support.

### Added for this bonus project

- **Asar**: patch-oriented 65C816 assembler used by major SNES ROM-hacking projects and by wide-snes. Pinned in `tools/toolchain.json` under the shared `patching` group because it is generally useful beyond this bonus project.

Bootstrap only the patching tools when needed:

```bash
python3 tools/bootstrap_toolchain.py --group patching
```

bsnes-hd remains a manual specialist workbench rather than a default CI dependency.

## Initial technical questions for Uniracers

Answer these before attempting a polished patch:

1. Which BG layers make up the track, distant/background art, HUD and transition masks?
2. Which layers remain valid when bsnes-hd is set to widen all non-Mode-7 scenes?
3. Does the game already maintain world/tilemap data outside the classic view, or does it stream only what can become visible?
4. Where are left/right renderer culling comparisons?
5. Where are object activation/spawn thresholds, and are they intentionally coupled to renderer culling?
6. How are racer X coordinates represented near the screen boundary?
7. How does the game's unusual active-display OAM behavior interact with bsnes-hd's widened sprite coordinates?
8. Which window/color-math effects assume X=0..255?
9. Which UI screens should remain 4:3 or centered instead of exposing more background?
10. What happens to the two-player/Vs. sprite-ripping path when each logical viewport is widened?

The existing native `WIDESCREEN-RECONNAISSANCE.md` taxonomy is useful vocabulary, but this bonus project must keep its observations under its own path until a result is independently useful to the shipping architecture.

## First experiment sequence

### B0: no-ROM-change exposure

Run canonical Uniracers in the pinned bsnes-hd build with a small preset matrix:

- stock;
- widescreen all + BGs widened + sprite safe;
- same + sprite unsafe;
- individual BG widening;
- windows normal vs diagnostic ignore;
- 16, 32, 48 and 64 columns per side where practical.

Goal: classify what is already present outside the normal view and what fails first. Do not infer game correctness from visual plausibility.

### B1: minimal patch scaffold

Create `bonus/widescreen-romhack/` with:

- `src/main.asm`;
- `config/*.bso`;
- base-ROM hash assertion;
- build script using Asar;
- BPS-generation step using Flips;
- a README that repeats the bonus-only boundary.

The first source patch should intentionally do almost nothing beyond proving deterministic patch/build/replay.

### B2: camera/render culling only

Patch the smallest known classic-width comparison and test whether additional BG/world content can be exposed without changing simulation or activation.

If this causes new gameplay behavior, revert and split the domains instead of accepting the side effect.

### B3: sprites/OAM

Work from captured OAM traces and the existing Uniracers active-display OAM research. Determine whether bsnes-hd `unsafe` sprite rendering is sufficient once ROM-side culling is widened, or whether coordinate/OAM rewriting is needed.

### B4: presentation exceptions

Classify title/menu/results/cutscene/HUD scenes as one of:

- widen world;
- fixed 4:3;
- fixed centered;
- mixed;
- special-case.

### B5: multiplayer

Do not call the experiment successful until one-player, two-player and Vs. have been exercised. Uniracers' raster-time OAM behavior makes multiplayer the likely dragon in this particular cave.

## Validation contract

Every meaningful patch revision should preserve:

- source ROM SHA-256;
- patch source revision;
- output ROM SHA-256;
- generated BPS SHA-256;
- Asar revision;
- Flips revision;
- bsnes-hd revision;
- BSO contents;
- target width/aspect/PAR/overscan policy;
- deterministic input fixture where available;
- stock-control result.

For gameplay behavior outside the widened image, compare against the stock ROM in the project's existing deterministic harnesses. A widened build should not silently alter physics, timing, RNG, race logic or object activation unless a change is explicitly required and documented.

## Completion levels

This is deliberately a bonus ladder rather than a main milestone:

- **B0 research-ready**: tools pinned, sources indexed, test matrix documented.
- **B1 scaffold**: reproducible no-op/minimal Asar -> ROM -> BPS build.
- **B2 race prototype**: one representative single-player race genuinely exposes more world.
- **B3 robust race support**: major race surfaces, sprites and transitions behave coherently.
- **B4 multiplayer support**: two-player/Vs. understood and functional.
- **B5 release-quality bonus**: source + BPS + BSO + reproducible validation and user documentation.

Stopping at any rung is acceptable. Main-line work never waits for this ladder.
