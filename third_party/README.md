# Repository-owned third-party tool sources

This directory is the boundary for UR-Recomp's offline/island toolchain.

The canonical plan is `docs/ISLAND-TOOLCHAIN-PLAN.md`. `manifest.json` records provenance and migration state. Research evidence remains under `references/`; do not mix evidence imports with executable dependencies.

Layout as components land:

- `src/` — active vendored/pruned source trees;
- `archives/` — exact immutable upstream source archives used on demand;
- `cargo/` — vendored Rust crate closure;
- `python-wheels/` — offline Python package cache;
- `patches/` — project-owned patches that are part of the islanded source contract.

A component stays in `mode: "pending"` until its repository-owned copy has provenance, licensing, hash validation, and the same smoke/contract behavior as the external pin. Bootstrap must never silently claim an offline path for a pending component.

## Current direct vendors

- `mesen-for-ai`: pruned from pinned upstream commit `a4bda6285eadf69c871135637df29e9c9a8f6f7a`. Runtime bridge/daemon, scripts, patches, tests, packaging metadata, README and GPL-3.0-only license are retained. Upstream agent-instruction/skill metadata is intentionally excluded because it is not required to execute or validate the tool.
