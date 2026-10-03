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
