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
- package-registry dependencies required by the vendored tools;
- any visual-reference dependencies that land from the active HD tooling lane, including RetroArch, Libretro Slang shaders and bsnes-hd. Apply the same island criteria: vendor only useful source/preset closure, preserve provenance, and keep heavyweight presentation tools off default CI unless measured workflows justify promotion.

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

### Customization decision rule

Use the least invasive ownership level that solves the measured problem:

1. **Configuration/build recipe first** when flags, target selection or packaging can remove the cost.
2. **Project-owned wrapper/adapter** when the upstream tool is correct but speaks the wrong input/output protocol.
3. **Small vendored patch** when a narrow defect, missing batch mode or instrumentation seam is best fixed in place.
4. **Maintained UR-Recomp fork/derivative** only when repeated patches or architectural changes make the upstream shape a persistent drag.
5. **Project-native replacement** when the useful behavior is small, well understood and cheaper to own than the inherited dependency.

Do not fork simply because source is local. Do not keep an awkward wrapper merely to avoid admitting that the project now owns the implementation.

For every meaningful customization, record:

- the problem/cost being removed;
- baseline upstream behavior/version;
- chosen ownership level and why;
- tests or fixtures protecting required behavior;
- expected maintenance burden;
- rollback/comparison path.

### Optimization/equivalence gate

Performance or workflow optimization must be measurable where practical.

Before promotion:

1. capture a representative baseline for runtime, startup, build time, artifact size, memory or manual steps;
2. implement the smallest candidate change;
3. rerun the same workload;
4. verify semantic/artifact equivalence where equivalence is expected;
5. explicitly document intended behavior changes where equivalence is not expected;
6. keep the optimization only when the gain is meaningful relative to maintenance cost.

For emulator/reference tools, never trade away oracle independence merely for speed. A project-specific fast path may coexist with the unmodified reference implementation, but must not silently replace the independent baseline used for fidelity claims.

### Preferred project-native seams

As islandization proceeds, favor a small number of durable UR-Recomp contracts over tool-specific glue:

- canonical ROM identity/provenance;
- shared fixture/input event streams;
- named WRAM/state checkpoints;
- canonical symbols;
- normalized player/game state;
- trace/CDL events with explicit address-space identity;
- native graphics/palette/tile/map buffers with declared layout;
- machine-readable JSON/JSONL reports.

When several vendored tools touch the same concept, adapt them toward these seams instead of multiplying pairwise converters.

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

- [x] Add `third_party/` structure and machine-readable manifest.
- [x] Add repository hygiene/validation for provenance, licenses and hashes.
- [x] Teach bootstrap to select local vendored source before network.
- [x] Add an explicit offline/no-network verification mode.
- [x] Add a unit-level offline fail-closed test so a pending component cannot silently fall back to GitHub.
- [ ] Extend local bootstrap to exact source archives when the first archive-mode component lands.
- [ ] Add a true network-disabled build smoke once at least one core component is islanded; before that, a successful offline core build would be a false claim.

Current P0-A implementation lives in `third_party/manifest.json`, `tools/validate_island.py`, `tools/bootstrap_toolchain.py`, repository hygiene, and focused unit coverage. Components remain `pending` until their local source/archive, hash and license are present and validated.

### P0-B — Small/high-value direct vendors

- [x] mesen-for-ai. Repository-owned pruned source and GPL-3.0-only license are present; deterministic tree SHA-256 is locked; bootstrap uses a stdlib-only installer with no PyPI/build-isolation dependency; run 36543649163 proves the `--offline` build, vendored tests, and launcher smoke.
- [x] snes2asm. Pristine upstream runtime source and PyYAML 6.0.3 pure-Python dependency closure are repository-owned with locked deterministic tree SHA-256 values. Historical offline smoke exposed a bootstrap boundary bug: `git apply` could discover the parent UR-Recomp worktree and report success without modifying a staged vendored copy that had no `.git`. Bootstrap now anchors such patches at the repository root with an explicit staged-source directory and has regression coverage for the no-op failure mode. Run 36559605681 proves the island manifest contract, offline bootstrap, repository-owned PyYAML closure and adapted snes2asm functional smoke.
- [x] SuperFamiconv plus Cargo dependency closure. The pinned v0.12.0 Rust CLI source is pruned into `third_party/src/superfamiconv/` with its exact `Cargo.lock`, MIT license, deterministic tree hash and a 78-package `cargo vendor --locked` registry closure. Acquisition run 36561241568 proves an isolated-`CARGO_HOME` `--release --locked --offline` build; ordinary toolchain run 36561456234 independently proves the island manifest contract and the normal repository bootstrap/build-smoke path.
- [x] ghidra-snes. The pinned extension implementation, SNES language/data definitions and build metadata are repository-owned with locked provenance/hash. Ghidra 12.0.4 plus Gradle/Maven remain explicit manual-workbench host dependencies outside the core offline guarantee. Toolchain run 36562190715 proves the island manifest contract and `bootstrap_toolchain.py --offline --tool ghidra-snes --clone-only` source staging path.
- [x] pruned Flips CLI. The pinned command-line/core patching source is repository-owned with GPL-3.0-or-later provenance and the bundled libdivsufsort 2.0.1 build subset/license. Acquisition run 36562878693 proves the pruned `make TARGET=cli` build plus `--version`/`--help`; ordinary toolchain run 36562932756 proves the island manifest and fail-closed `bootstrap_toolchain.py --offline` build path.
- [x] Beetle/bsnes libretro. The pinned build tree is repository-owned and proven through ordinary fail-closed offline bootstrap plus the independent seven-checkpoint first-race route. PR #55 subsequently fixed the identified libretro `SAVE_RAM` omission and framebuffer teardown double free with a narrow project-owned patch. Permanent regression now proves exact 8 KiB SRAM preload→dump identity and clean teardown under Beetle; retain cross-core WRAM differences as evidence rather than an equality requirement.

### P0-C — Core reconstruction/build tools

- [x] WLA-DX. The exact v10.7 pin (`91c52b1f4ef3cc8ba3c0638f7536539579af6a9f`) is repository-owned as a pruned 65816/linker closure under `third_party/src/wla-dx/`, with GPL-2.0-or-later provenance and deterministic tree hash `8427742e0a299db184a2ed416a997cc360f36f8117c3fdf524c836c9325d6a9e`. `tools/patches/wla-dx-ur-recomp.patch` narrows upstream CMake to `wla-65816` and `wlalink`; acquisition run 36581411375 proves the pruned source configures, builds both binaries and passes the island manifest validator without a package registry.
- [ ] SNESRecomp.
- [x] cc65/da65 reduced closure. Run 36662983284 proves a self-contained four-root closure (`LICENSE`, `src/Makefile`, `src/da65`, `src/common`) that builds `bin/da65` and disassembles a 65816 smoke byte. Run 36663755722 measures 150 files / 1,100,892 source bytes with island-tree SHA-256 `11cc79b488738f94b5b98ebcb4182fbfa8488a60c637343ea32f425543ec50ea`; that exact closure is now repository-owned under `third_party/src/cc65-da65/` and wired for offline bootstrap.

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


## Tool update policy

Islandization must not turn pinned tools into abandoned fossils. It should make updates safer and more selective.

For every vendored or archived tool:

1. record the upstream revision currently incorporated;
2. periodically check upstream when a concrete workflow depends on that tool, when a relevant bug is suspected, or when upstream publishes changes that affect SNES accuracy, headless execution, debugger behavior, build compatibility, security, or performance;
3. do **not** churn pins merely because a newer commit exists;
4. review the upstream diff from the current incorporated revision to the candidate revision and identify project-relevant fixes/regressions;
5. rebase or remove UR-Recomp patches where upstream has absorbed them;
6. rebuild the tool from the repository-owned source/dependency closure;
7. run the same contract/smoke/differential tests used by the existing version;
8. compare important outputs against the previous incorporated version before promotion;
9. update provenance, hashes, licenses and the island manifest in the same change;
10. preserve the prior known-good revision long enough to diagnose regressions when the update materially changes behavior.

Prefer updates that buy one or more of:

- correctness at an SNES behavior seam we care about;
- deterministic/headless reliability;
- removal of a project-owned patch;
- materially lower runtime/build cost;
- improved machine-readable output or automation APIs;
- dependency/security compatibility needed by supported hosts.

Avoid updates whose only rationale is version freshness.

For emulator/reference tools, version changes may alter the oracle itself. Treat those updates as research changes, not routine dependency bumps: run matched fixtures before/after and record any changed state/frame behavior.

## P0 interaction with newly added tools

Any tool added by another active workstream while P0 is in progress enters the island review automatically. Do not require that workstream to stop or vendor it first.

After the tool lands:

- classify it as direct-vendor, curated subset, exact archive, or optional external/manual;
- close any package-registry dependencies if it becomes part of core automation;
- add provenance/license metadata;
- add it to offline verification only if the core workflow actually depends on it;
- leave heavyweight/manual presentation workbenches outside default offline smoke unless their use becomes routine.

This applies in particular to the HD-reference lane's RetroArch, Libretro Slang shader corpus and bsnes-hd if they land before or during islandization.
