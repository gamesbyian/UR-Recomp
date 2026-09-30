# SNESRecomp islandization scope

Status: reconnaissance / execution boundary for P0-C.

This note maps the exact dependency surface of UR-Recomp's pinned SNESRecomp revision before any source migration. It is deliberately narrower than a generic SNESRecomp packaging plan: the goal is to make the framework pieces UR-Recomp actually needs reconstructible offline without silently importing optional network/UI/tooling features.

## Canonical pin

UR-Recomp's `snesrecomp` gitlink is pinned to:

`cd5875cbdaf19f5e324272b1f8051d671fce9215`

The pinned upstream tree contains 942 Git entries. Upstream license at this revision is PolyForm Noncommercial 1.0.0; any repository-owned copy must preserve the license and attribution exactly.

The framework itself contains two nested gitlinks:

| path | upstream | pinned gitlink |
| --- | --- | --- |
| `lib/recomp-net` | `RetroPortingToolKit/recomp-net` | `a65fdcfc044a492ab76385a061459b43f6888b55` |
| `lib/retcomm-rbengine` | `RetroPortingToolKit/rbengine` | `2a03e73693acee0fb78076ea058642c931bef12e` |

Do not flatten those into the baseline closure merely because they are submodules. SNESRecomp's own CMake keeps netplay opt-in.

## Dependency classes

### A. Baseline framework source

The main SNESRecomp tree contains the recompiler, runner, host support, `snesref`, generated-project tooling, bundled small third-party code and tests.

This is the first ownership target. Preserve the exact upstream revision and license before pruning anything. Large generated validation evidence such as `docs/validation/disassembly-2026-09-28.json` is not automatically part of an executable closure and should be classified separately from source.

Preferred first experiment:

1. materialize an exact repository-owned copy/archive of the pinned framework tree;
2. omit nested gitlink contents initially, but preserve their path/revision metadata;
3. prove the existing canonical Uniracers generation/native build with netplay and Lua disabled;
4. only then decide whether a pruned active-source tree is worth maintaining versus an immutable source archive plus extraction step.

### B. SDL desktop backend

The pinned runner defaults to SDL3. If no SDL3 package is found, `runner.cmake` can FetchContent a pinned SDL3 release.

Pinned fallback at this framework revision:

- SDL3 version: `3.4.10`
- source URL: GitHub SDL release tarball
- SHA-256: `12b34280415ec8418c864408b93d008a20a6530687ee613d60bfbd20411f2785`
- local-source override: `SNESRECOMP_SDL3_SOURCE_DIR`
- network fallback switch: `SNESRECOMP_SDL3_FETCH`

Island rule: never allow a supposedly offline build to reach the FetchContent URL. Choose one explicit policy for UR-Recomp:

1. host-provided SDL3 as an ordinary system prerequisite; or
2. repository-owned exact SDL3 source/archive wired through `SNESRECOMP_SDL3_SOURCE_DIR`.

Do not vendor SDL3 merely because SNESRecomp supports doing so. Measure the project's actual clean-checkout requirement first.

### C. Rust analyzer

`recompiler-rs` is a Rust 2021 package with minimum Rust 1.85 and one direct dependency, `serde_json = "1"`.

Its pinned `Cargo.lock` currently resolves ten registry packages:

- itoa 1.0.18
- memchr 2.8.3
- proc-macro2 1.0.106
- quote 1.0.46
- serde 1.0.228
- serde_core 1.0.228
- serde_derive 1.0.228
- serde_json 1.0.150
- syn 2.0.119
- unicode-ident 1.0.24
- zmij 1.0.23

(The analyzer package itself is also present in the lockfile and is not a registry dependency.)

This is a small Cargo closure. If UR-Recomp's active analysis path requires the Rust analyzer after the framework source is islanded, use the same `cargo vendor --locked` discipline already proven for SuperFamiconv rather than relying on crates.io.

### D. Lua bridge

Lua is explicitly opt-in:

`SNESRECOMP_ENABLE_LUA=OFF` by default.

When enabled, the framework FetchContent path uses:

- Lua 5.4.9
- `https://www.lua.org/ftp/lua-5.4.9.tar.gz`
- SHA-256 `2335b6c582a52654f94612bf10d2f4672805d05329aa6568b1d8cd9e5c6fb8e6`

Therefore Lua is not a blocker for the baseline P0-C island gate. Keep it as a later optional closure unless a current UR-Recomp workflow proves it is required.

### E. Netplay / rollback

SNESRecomp's netplay layer is opt-in:

- `SNESRECOMP_ENABLE_NET=OFF` by default;
- `SNESRECOMP_NET_ICE=OFF` by default;
- `SNESRECOMP_NET_FORCE_TURN=OFF` by default.

When enabled, the framework expects the pinned `recomp-net` and `retcomm-rbengine` trees above. ICE can add a libjuice FetchContent dependency inside recomp-net when not otherwise vendored/installed.

UR-Recomp's product plan deliberately leaves online functionality as a future door rather than current infrastructure. Consequently these two nested gitlinks must be preserved/reconstructible, but they should not expand the baseline offline build closure until an enabled netplay build is actually part of the project gate.

### F. CI/toolchain convenience downloads

SNESRecomp also contains helpers that can download:

- prebuilt compiler/toolchain packs;
- SDL3 source;
- project metadata/box art;
- other development conveniences.

These are not baseline runtime dependencies. Islandization should disable or route around them in core CI rather than vendoring every convenience asset.

## Recommended P0-C execution order

### C1 — exact framework ownership

Create a reproducible repository-owned source/archive at the pinned `cd5875c...` revision with license/provenance and a deterministic tree/archive hash. Preserve nested-gitlink revision metadata but do not silently dereference optional netplay contents.

Gate: the current canonical analyzer/generation/native build can consume that copy without fetching SNESRecomp from GitHub.

### C2 — baseline build network audit

Run the canonical build with outbound source fetches disabled. Record every attempted external access. Classify each as:

- required baseline dependency;
- optional feature accidentally enabled;
- convenience download;
- test-only/development-only dependency.

Do not pre-vendor from static source inspection alone.

### C3 — SDL policy

Resolve the first demonstrated SDL3 dependency either as a documented host prerequisite or exact local SDL3 source/archive. Force `SNESRECOMP_SDL3_FETCH=OFF` in the offline gate unless a local `SNESRECOMP_SDL3_SOURCE_DIR` is explicitly supplied.

### C4 — Rust analyzer closure, if active

If the canonical analysis path invokes `recompiler-rs`, vendor its locked Cargo closure and require `--locked --offline`. The registry surface is small enough that this should be a bounded tranche.

### C5 — optional features

Only after the baseline build is green:

- Lua 5.4.9 closure if a current workflow enables the bridge;
- `recomp-net` + `retcomm-rbengine` + libjuice closure when online/netplay becomes an active tested feature;
- manual/workbench helper downloads as separate optional tooling.

## Anti-goals

- Do not replace the pinned framework with an untracked copy.
- Do not turn optional netplay/Lua dependencies into baseline requirements.
- Do not preserve network FetchContent paths inside an `--offline` success case.
- Do not prune source before a complete exact copy/archive and license record exist.
- Do not treat upstream validation JSON, docs, demos, or CI helpers as executable dependencies without evidence.
- Do not conflate “repository-owned” with “must be built in every CI job.”

## Immediate next experiment

C1 should be the next SNESRecomp implementation tranche.

The safest first artifact is an exact source archive or mechanically materialized tree of `cd5875c...`, accompanied by:

- source hash;
- PolyForm license/provenance;
- explicit records for the two nested gitlinks;
- an acquisition workflow that can rederive the copy from upstream once;
- a bootstrap path that consumes the local copy;
- a clean-checkout canonical generation/build smoke with network source fetching disabled.

Only after that experiment should the project decide whether to keep SNESRecomp as an immutable archive, an active vendored tree, or a small maintained UR-Recomp derivative.
