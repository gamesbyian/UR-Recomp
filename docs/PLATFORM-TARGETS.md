# Platform Targets

Last updated: 2026-10-02

UR-Recomp is a private personal-use preservation/remaster project. The intended end state is one authoritative recompiled Uniracers simulation with multiple host implementations, not separate gameplay rewrites.

## Target matrix

| Target | Role | Status | Host strategy |
| --- | --- | --- | --- |
| Windows x64 | Primary reference shipping build | planned | native C/C++ desktop host; SDL-backed input/audio/windowing; modern compositor |
| macOS current | Native desktop peer | planned | native C/C++ host sharing product/runtime code with Windows |
| macOS 10.13 High Sierra | Best-effort legacy build | feasibility target | separate legacy toolchain/build lane; do not constrain the whole project to obsolete SDKs |
| Web | Browser build | feasibility target | WebAssembly/Emscripten host over the same authoritative simulation; browser storage/input/audio/presentation adapters |
| Nintendo Switch homebrew | Personal-use console build | feasibility target | devkitPro/devkitA64 + libnx, preferably reusing SDL2-facing host seams first |
| PlayStation 5 homebrew/dev environment | Personal-use console build | feasibility target | platform host port only when lawful tooling/access is available; no proprietary SDK material in this repository |

The project is not planning commercial distribution or storefront submission for console targets.

## Architecture rule

Platform ports must share the authoritative simulation and as much product logic as possible:

```
recompiled Uniracers simulation
        |
platform-neutral product/runtime interfaces
        |
HD / Widescreen presentation policy
        |
platform host adapter
        |
Windows | macOS | Web | Switch | PS5
```

Platform-specific code should be limited to:
- executable/bootstrap lifecycle;
- filesystem/config/save locations;
- window/display creation;
- graphics backend glue;
- audio device glue;
- controller discovery, input translation and rumble;
- suspend/resume/focus lifecycle;
- packaging and platform metadata.

Do not move platform assumptions into guest simulation, progression/SRAM semantics, Widescreen materialization, HD semantic replacement selection, Retry rollback semantics, or modern profile/state schemas.

## Display and refresh policy

All graphical hosts should expose presentation settings appropriate to their platform without changing simulation semantics. The cross-platform semantic contract is `DISPLAY-PRESENTATION-POLICY.md`; platform adapters translate that contract into concrete display APIs rather than redefining it.

Shared expectations:

- support native/automatic output resolution plus common explicit resolutions;
- desktop hosts should support windowed, borderless and fullscreen modes;
- output resolution and internal render scale are independent;
- **display geometry / pixel aspect is independent from logical view width**;
- Authentic 4:3, Raw Pixels, and modern square-pixel presentation must preserve their semantic meaning across hosts even when a platform exposes fewer knobs;
- Original/16:9/possible Adaptive or ultrawide view choices must alter presentation extent only, never simulation authority;
- overscan/safe-area treatment is independent from both pixel aspect and logical view;
- VSync and presentation refresh/FPS targets are user-configurable where the platform allows;
- 60/90/120/144 Hz and native/high-refresh presentation should be possible without speeding up or slowing down the game;
- presentation interpolation, if introduced, is strictly host-side and may not become authoritative state;
- Authentic mode must preserve a validated historical/reference presentation path;
- console hosts may expose fewer choices when the platform fixes output modes, but they must preserve the same separation between simulation cadence and presentation cadence.

The canonical simulation rate remains fixed to the original game. No platform may reinterpret a user-selected display FPS as a request to change physics, timers, AI, RNG, stunt windows, replay timing or records.

## SDL backend policy

**SDL3 is UR-Recomp's canonical desktop host backend. SDL2 exists only as a compatibility/platform fallback, and new cross-platform product code must not be designed against the SDL2 API.**

This follows the pinned SNESRecomp framework, whose `runner.cmake` already defaults to SDL3 and keeps SDL2 as an explicit fallback (`SNESRECOMP_SDL_BACKEND`). The host layer (display modes, fullscreen, VSync, output resolution, pause UI, controller handling, presentation timing) is still under active construction. Moving now avoids accumulating glue against an API the project already expects to replace.

| Lane | Backend |
| --- | --- |
| Windows x64 reference build | SDL3 |
| Modern macOS | SDL3 |
| Linux CI / native engineering builds | SDL3, unless a check deliberately exercises the SDL2 fallback |
| Web | whatever Emscripten/framework path proves appropriate; it does not dictate desktop architecture |
| Switch homebrew | SDL2 may remain a platform-specific adapter (homebrew ecosystems lag) |
| macOS High Sierra | SDL2 if required by that separate legacy lane |
| PS5 / other homebrew | decided per platform later |

Implementation rules:
- **SDL source:** SDL3 comes from the repository-owned, hash-pinned SDL 3.4.10 source archive (`third_party/archives/SDL3-3.4.10.tar.gz`). It is byte-identical to the framework pin. Stage it with `python3 tools/bootstrap_toolchain.py --offline --tool sdl3 --clone-only` and pass `-DSNESRECOMP_SDL_BACKEND=SDL3 -DSNESRECOMP_SDL3_FETCH=ON -DSNESRECOMP_SDL3_SOURCE_DIR=<repo>/.tools/src/sdl3/SDL3-3.4.10`. With a local source dir supplied, the build makes no network fetch; the network audit's `sdl3-repo-source` lane traces this.
- **Version differences:** SDL2/SDL3 API differences stay inside framework/host shims (`desktop/sdl_compat.h` and the dual-path host patches). Product code (`native/product/`) speaks normalized host contracts, not SDL version-specific types.
- **Workflow coverage:** every workflow that builds the native game uses SDL3 from the repository source; this was migrated on 2026-10-04. Builds that previously went through `setup_project.sh --build` (framework defaults, i.e. a network SDL3 fetch) now configure explicitly. The SDL2 fallback keeps compile coverage through the network audit's `sdl2-system` lane.
- **snesref exception:** `libsdl2-dev` remains installed where workflows build `snesref`. That reference-emulator harness is a separate framework tool whose CMake requires SDL2; it is not the desktop host.
- **Equivalence evidence (2026-10-04):** guest state is backend-independent. On the race-result route, the SDL3 and SDL2 builds produce byte-identical WRAM, VRAM, CGRAM and SRAM. The SDL3 build matches snesref at all 36 text-parity checkpoints.

## Reference platform policy

Windows x64 is the primary consumer/reference packaging target.

Linux remains acceptable as a CI and engineering host where convenient, but Linux-specific behavior is not product policy.

macOS and Web should be treated as peer hosts, not forks. Switch and PS5 should likewise be host ports over the same simulation/product boundaries.

## High Sierra policy

High Sierra compatibility is desirable but must remain a separate legacy-build concern.

Rules:
- keep platform-neutral code conservative C/C++ where practical;
- avoid requiring new macOS-only APIs in shared code;
- maintain a modern macOS build independently;
- permit a pinned older Xcode/SDK deployment lane for macOS 10.13 if the dependency graph still supports it;
- if a dependency makes 10.13 impossible, record the exact blocker rather than silently raising the target.

## Web policy

Protect WebAssembly portability now even before a browser build exists:
- no required writable process-global filesystem assumptions;
- no dependency on fork/exec;
- no required native threads unless a browser-compatible fallback exists;
- host persistence behind an interface suitable for IndexedDB/OPFS-backed storage;
- browser Gamepad API and keyboard mapping should feed the same semantic host-input layer;
- browser audio and frame scheduling must not become authoritative simulation clocks.

## Console-homebrew policy

Console targets are personal-use feasibility targets.

Only public/community homebrew tooling and project-authored code may be committed here. Proprietary SDKs, keys, confidential documentation, circumvention payloads, or device-unique secrets do not belong in Git.

Switch details are owned by `SWITCH-HOMEBREW-PORT.md`.
