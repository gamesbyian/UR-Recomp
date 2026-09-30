# Offline Core Host Prerequisites

This document defines the intentional **host boundary** for Priority 0 island/offline operation. The repository owns the game-specific tool sources, source archives, package-registry closures, patches, ROM evidence, and build recipes. It does not attempt to vendor a Linux distribution or ordinary compiler/runtime packages.

## Supported proof environment

The permanent proof target is GitHub's current `ubuntu-latest` runner family. Equivalent modern Linux hosts are acceptable when they provide the same ordinary build/runtime capabilities.

The dedicated `.github/workflows/offline-core-smoke.yml` installs host packages **before** entering a fresh network namespace. Every game/tool source operation and the canonical native generation/build then runs with no external network interface.

## Required host capabilities

For the canonical native/reference proof lane:

- POSIX shell utilities and coreutils
- Python 3
- Git only as a local patch/build utility where a repository-owned recipe requires it; no clone/fetch is permitted in offline mode
- C/C++ compiler toolchain and make
- CMake
- pkg-config
- SDL2 development headers/libraries
- ordinary Linux/X11/Wayland/audio development headers required by the generated host runtime

The CI proof installs this concrete Ubuntu package set:

```text
cmake
ninja-build
pkg-config
libsdl2-dev
libgl1-mesa-dev
libx11-dev
libxext-dev
libxrandr-dev
libxcursor-dev
libxi-dev
libxfixes-dev
libxkbcommon-dev
libwayland-dev
libasound2-dev
libpulse-dev
libxss-dev
libxtst-dev
```

The runner image already supplies Python, the compiler toolchain and standard shell utilities.

## Tool-specific host capabilities

Some repository-owned tools require additional ordinary host toolchains:

- Rust/Cargo for SuperFamiconv and the SNESRecomp analyzer. Their crate dependencies are repository-owned and builds must use the vendored closure in offline mode.
- A JDK/Gradle/Ghidra installation for the optional `ghidra-snes` manual workbench. This is outside the core automated offline guarantee.
- ffmpeg/ImageMagick and heavyweight presentation/debugger applications remain optional host tools unless a future measured core workflow promotes them.

## What must remain impossible during the proof

Inside the offline core namespace, successful execution must not depend on:

- GitHub or any other source host
- PyPI
- crates.io
- git submodule initialization
- CMake/FetchContent downloads
- box-art, UI, netplay, or other optional SNESRecomp fetches

A green proof means a clean checkout already contains every non-host input required to verify the canonical ROM, stage/build the Snes9x reference core, stage/generate SNESRecomp, and compile the actual `UniracersSNESRecomp` target.

## Boundary rule

If a future core workflow needs a package that is game/tool source, a language-package dependency, a project patch, or a deterministic build input, bring it under repository ownership.

If it is an ordinary compiler, runtime, system development library, kernel facility, or general-purpose host executable, keep it at the host boundary unless repeated evidence shows that relying on the host makes the workflow unstable or non-reproducible.
