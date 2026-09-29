# Priority 0 — Island / Offline Toolchain

This is the current **Priority 0 infrastructure workstream**.

## Goal

Make UR-Recomp as self-contained as practical without turning the repository into an operating-system image.

Target condition:

> On a compatible Linux host with ordinary system/compiler prerequisites already installed, a clean checkout can build and run the core automated research toolchain with GitHub, PyPI and crates.io unavailable.

The repository should continue to work if an upstream project disappears, a package registry is unavailable, or an agent has no network access after checkout.

## Why this is Priority 0

The project increasingly depends on a growing graph of external emulators, assemblers, disassemblers, converters and agent/debug bridges. Every external fetch is a failure mode, a latency cost and a constraint on project-specific adaptation.

Islandization should happen before those external contracts spread further through the project.

This work must **not** interrupt active race/course, UI/navigation or HD-reference research. It is infrastructure work around those lanes, not a reason to rewrite or invalidate them.

## Island boundary

### Bring into repository ownership

Preserve exact provenance, upstream revision and licensing for vendored material.

First tranche:

1. SNESRecomp
2. snes2asm
3. mesen-for-ai
4. SuperFamiconv
5. Beetle/bsnes-derived libretro core
6. WLA-DX
7. ghidra-snes
8. a pruned Flips CLI source snapshot

Evaluate in the same pass:

- cc65/da65 source closure;
- Snes9x libretro-oriented source closure;
- ordinary bsnes-libretro source/archive;
- package-registry dependencies required by the vendored tools.

### Prefer immutable archives or targeted snapshots for large workbenches

Do not expand huge GUI/debugger projects into the active source tree merely for the sake of saying they are vendored.

Candidates include:

- MesenCE;
- ares;
- DiztinGUIsh;
- bsnes-plus;
- full Snes9x/bsnes trees when a smaller build/source closure is sufficient.

Where practical, keep exact source archives with hashes and unpack them on demand.

### Keep outside the repository

Ordinary host prerequisites remain the host boundary:

- compiler toolchains;
- CMake / make;
- Python runtime;
- Rust toolchain;
- SDL and other ordinary system libraries;
- ffmpeg / ImageMagick where needed;
- OS package manager state.

Do not vendor an operating system into Git.

## Package-registry closure

Vendoring project source is insufficient if builds still require package registries.

### Rust

For vendored Rust tools such as SuperFamiconv:

- run `cargo vendor`;
- commit the exact crate closure;
- configure builds to use the repository vendor directory;
- verify the build with network disabled.

### Python

For vendored Python tools:

- create a repository wheel/sdist cache for required third-party packages;
- install with `--no-index --find-links`;
- avoid accidental build-time downloads;
- keep package hashes and provenance.

Known examples:

- snes2asm requires PyYAML;
- mesen-for-ai has minimal runtime dependencies but its packaging/build requirements must also be closed offline.

## Repository structure

Use a deliberate hierarchy rather than mixing vendored implementation source with research evidence:

```text
third_party/
  README.md
  manifest.json
  src/
    snesrecomp/
    snes2asm/
    superfamiconv/
    wla-dx/
    beetle-bsnes/
    mesen-for-ai/
    ghidra-snes/
    flips-cli/
  archives/
  cargo/
  python-wheels/
  patches/
```

Exact layout may be refined during implementation, but keep these concepts separate:

- active vendored source;
- immutable source archives;
- package-registry closure;
- project-owned patches/adaptations;
- provenance/license metadata.

Do not merge these with `references/imported/`, which is the research-evidence corpus.

## Manifest contract

Add a machine-readable island manifest that records, at minimum:

- component ID;
- upstream URL;
- exact upstream revision/tag;
- source/archive SHA-256;
- license/SPDX status and bundled license path;
- vendored/pruned/archive-only mode;
- files or directories intentionally omitted;
- project patches;
- build entrypoint;
- expected artifacts;
- offline dependency closure status;
- replacement for the corresponding `tools/toolchain.json` external-fetch path.

Repository hygiene must reject:

- unmanifested vendored components;
- missing required license/provenance material;
- source hash drift;
- an automatic core-tool build that unexpectedly requires network access.

## Migration rule

Move tools incrementally.

For each component:

1. preserve current external pin and known-green behavior;
2. create the vendored/source-archive copy with provenance and license;
3. make bootstrap support the local copy without removing the external path;
4. run the existing smoke/contract tests against both sources where practical;
5. prove artifact equivalence or explain intended differences;
6. switch the default to the repository-owned source;
7. remove the network fetch only after the local path is green;
8. update the interoperability/toolchain authorities;
9. preserve a clear rollback path until the tranche is complete.

Do not migrate several critical tools in one opaque commit.

## Customization policy after islandization

Vendored tools are allowed to become **UR-Recomp-owned adaptations** when doing so saves meaningful time, exposes needed evidence, or removes project-specific friction.

Prefer:

- thin patches;
- headless-only build targets;
- reduced feature/build closures;
- machine-readable output modes;
- stable exit codes;
- project-native symbol/state/input formats;
- deterministic batch modes;
- direct interoperability adapters;
- instrumentation useful to Uniracers research;
- removal of unused GUI/runtime dependencies from our build closure.

Do not preserve upstream awkwardness merely for museum accuracy.

Keep the upstream snapshot/revision reconstructible and make every project modification reviewable.

## Safety around work in progress

At the time this P0 item was created, active work exists on:

- PR #9 — race/course research;
- PR #11 — UI/navigation mapping;
- PR #14 — HD/upscaling reference tooling.

This workstream must not casually overwrite their files or generated evidence.

Before every implementation PR:

1. inspect all open PRs and likely unsubmitted branches;
2. identify changed-file overlap;
3. choose an isolated tranche whenever possible;
4. record overlaps in the PR description;
5. do not merge across an active owner's changes merely because Git reports the branch mergeable.

Before merging any islandization PR:

1. rebase/merge current `main`;
2. re-check open PR overlap;
3. reconcile concurrent `tools/toolchain.json`, documentation, manifests and generated files by intent;
4. regenerate any derived artifacts invalidated by the reconciliation;
5. run repository hygiene, toolchain contract tests and the relevant build smoke matrix;
6. verify no active research fixture/evidence path was weakened or deleted;
7. update PR description with the final reconciliation checkpoint.

If an active PR owns the same files and its work has not landed yet, keep the island PR draft or split out a disjoint tranche rather than forcing a merge.

## Execution tranches

### P0-A — Island infrastructure

- [ ] Add `third_party/` structure and machine-readable manifest.
- [ ] Add repository hygiene/validation for provenance, licenses and hashes.
- [ ] Teach bootstrap to select local vendored source/archive before network.
- [ ] Add an explicit offline/no-network verification mode.
- [ ] Add an offline smoke workflow or test harness that fails on unexpected dependency fetches.

### P0-B — Small/high-value direct vendors

- [ ] mesen-for-ai.
- [ ] snes2asm, incorporating the existing UR-Recomp patch cleanly.
- [ ] SuperFamiconv plus Cargo dependency closure.
- [ ] ghidra-snes.
- [ ] pruned Flips CLI.
- [ ] Beetle/bsnes libretro.

### P0-C — Core reconstruction/build tools

- [ ] WLA-DX.
- [ ] SNESRecomp.
- [ ] Evaluate cc65/da65 reduced closure and vendor it if practical.

### P0-D — Larger emulator/reference dependencies

- [ ] Establish the smallest reproducible Snes9x source/build closure required by `snesref`.
- [ ] Decide source-tree versus archive strategy for ordinary bsnes-libretro.
- [ ] Preserve larger manual workbenches through exact source archives when useful.

### P0-E — Offline completion

- [ ] Close Python package-registry dependencies.
- [ ] Close Rust crate-registry dependencies.
- [ ] Run the core automated research workflow with outbound network disabled.
- [ ] Document remaining host prerequisites as the intentional island boundary.
- [ ] Remove obsolete external-fetch paths after all local replacements are proven.

## Exit criteria

Priority 0 is complete when:

- core automated research/build tools no longer require GitHub/PyPI/crates.io after checkout;
- vendored/archive sources have exact provenance and licensing;
- the regular toolchain/interoperability tests pass against repository-owned sources;
- a network-disabled build/research smoke run succeeds;
- active research branches have been reconciled without losing work;
- external fetches that remain are explicitly optional/manual rather than hidden requirements.

## Follow-on optimization opportunity

Islandization deliberately increases the project's freedom to modify tooling. Once a source tree and dependency closure are under repository control, evaluate project-specific optimization by measured value rather than upstream convention.

Likely opportunities include:

- merge several one-shot adapters into common project libraries;
- add direct JSON/JSONL output where tools currently emit prose;
- bypass intermediate files when two vendored tools can share a stable library/API boundary;
- expose Uniracers-specific batch probes without maintaining game-specific emulator hacks;
- add deterministic snapshot/checkpoint APIs;
- compile only the subsystems used by UR-Recomp;
- remove unnecessary GUI/platform backends from project builds;
- fuse extraction/conversion/reassembly steps where doing so preserves evidence boundaries;
- instrument RNC, OAM, PPU, input and state paths at the exact seams this project studies.

Any such optimization should retain a reproducible upstream baseline so behavior can still be compared against the unmodified source.
