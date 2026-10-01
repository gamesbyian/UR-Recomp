# Repository-owned third-party tool sources

This directory is the boundary for UR-Recomp's offline/island toolchain.

The canonical plan is `docs/ISLAND-TOOLCHAIN-PLAN.md`. `manifest.json` records provenance and migration state. Research evidence remains under `reference/`; do not mix evidence imports with executable dependencies.

Layout as components land:

- `src/` — active vendored/pruned source trees;
- `archives/` — exact immutable upstream source archives used on demand;
- `cargo/` — vendored Rust crate closure;
- `python-wheels/` — offline Python package cache;
- `patches/` — project-owned patches that are part of the islanded source contract.

A component stays in `mode: "pending"` until its repository-owned copy has provenance, licensing, hash validation, and the same smoke/contract behavior as the external pin. Bootstrap must never silently claim an offline path for a pending component.

## Current direct vendors

- `mesen-for-ai`: pruned from pinned upstream commit `a4bda6285eadf69c871135637df29e9c9a8f6f7a`. Runtime bridge/daemon, scripts, patches, tests, packaging metadata, README and GPL-3.0-only license are retained. Upstream agent-instruction/skill metadata is intentionally excluded because it is not required to execute or validate the tool.

- `snes2asm`: pruned pristine source from pinned upstream commit `04023b0b589042b212f30c92ec7acf6e6bd010e4`. CLI runtime, compression modules, templates, README/setup metadata and Apache-2.0 license are retained. GUI code, upstream wrappers and upstream tests/ROM fixture are excluded. UR-Recomp's narrow patch remains separate under `tools/patches/`.
- `pyyaml-6.0.3`: pure-Python runtime subset from upstream tag 6.0.3 / commit `49790e73684bebad1df05ef8d828fa12f685bffb`, retained solely as snes2asm's offline YAML dependency. The optional LibYAML extension is intentionally excluded.
- `superfamiconv`: pruned native Rust CLI source from pinned upstream commit `566522204e271885fb771b56f1f85d62f3f41430` (v0.12.0), with exact `Cargo.lock` and a committed 78-package `cargo vendor --locked` closure. Repository bootstrap builds it with `--locked --offline`; upstream Python wrappers, tests/test data, editor/CI metadata and documentation images are excluded from the executable dependency surface.
- `ghidra-snes`: pruned extension implementation and SNES language/data from pinned upstream commit `d33ce5dbfbc3645f00449be1c7ca1c1c65e81756` (plugin 1.3.2, Ghidra compatibility 12.0.4). The source can be staged offline; Ghidra, Gradle/Maven resolution, upstream CI/editor files, tests and Gradle wrapper machinery remain outside the core automated island boundary.
- `flips`: pruned command-line/core Floating IPS source from pinned upstream commit `6caac470f7fc096b0c5fdc374b65954f8bac5b16`, licensed GPL-3.0-or-later. GTK/Windows frontends and packaging assets are omitted; the upstream-bundled libdivsufsort 2.0.1 build subset and its license are retained, so the CLI has no package-registry dependency.
- `beetle-bsnes-libretro`: essentially complete pinned emulator/libretro source from commit `5f05e4c785e936c928ac468e129c55b6f08592cb`, licensed GPL-2.0-or-later. Upstream CI metadata and Android packaging are omitted; emulator implementation, libretro frontend, headers, embedded license material and Linux build files remain intact so the independent oracle is not weakened by aggressive pruning.

- `cc65-da65`: reduced da65-only closure from cc65 commit `d8a486acdef93ea1ba432a6a35b96cf1b797bda5`, licensed Zlib. Retained roots are `LICENSE`, `src/Makefile`, `src/da65/**` and `src/common/**`; measured source closure is 150 files / 1,100,892 bytes and builds `bin/da65` with ordinary GNU make/C tooling only.

## Current immutable archives

- `snesrecomp`: exact deterministic source archive from pinned framework commit `cd5875cbdaf19f5e324272b1f8051d671fce9215`, PolyForm Noncommercial 1.0.0. Archive SHA-256 `cc5043c4477adaa31210efb88c3423344e2195044e4366795cf1c563e1014b56`; 5,251,351 compressed bytes; 942 archive entries. Optional nested gitlinks `lib/recomp-net` and `lib/retcomm-rbengine` are preserved by revision in provenance but intentionally not dereferenced into the baseline C1 archive. Its baseline `recompiler-rs` analyzer is paired with an 11-package / 476-file / 5,874,431-byte locked Cargo vendor closure under `third_party/cargo/snesrecomp-analyzer/`, overlaid only into disposable staged source so the immutable archive remains pristine.
