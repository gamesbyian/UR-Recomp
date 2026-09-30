# SNESRecomp islandization scope

Status: C1 implementation active; dependency boundary remains canonical for P0-C.

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

Its pinned `Cargo.lock` currently resolves eleven registry packages:

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

Implemented in PR #64 as a deterministic `git archive | gzip -n -9` snapshot of `cd5875cbdaf19f5e324272b1f8051d671fce9215`: SHA-256 `cc5043c4477adaa31210efb88c3423344e2195044e4366795cf1c563e1014b56`, 5,251,351 compressed bytes, 942 archive entries. PolyForm Noncommercial 1.0.0 is preserved beside provenance. Nested gitlinks remain excluded from the baseline archive but pinned explicitly in provenance.

Archive-mode bootstrap stages the framework with `--offline`; the ordinary toolchain matrix builds `tools/snesref` from the extracted repository-owned copy. C1 is complete when that final matrix is green.

### C2 — baseline build network audit

Completed by PR #67. The canonical generated-project path now has a measured network boundary:

- the repository-owned C1 archive stages and generates without SNESRecomp submodules;
- a fresh `CARGO_HOME` with `CARGO_NET_OFFLINE=true` cannot build `snesrecomp-analyze`, proving the Rust registry closure is a baseline generation dependency;
- ordinary generation currently makes 36 observed AF_INET/AF_INET6 connect/send attempts while first building that native analyzer;
- after generation, SDL2 configure + full native Uniracers build complete with zero observed internet socket attempts;
- SDL3 with `SNESRECOMP_SDL3_FETCH=OFF` fails only because the Ubuntu host lacks SDL3, also with zero configure/build network attempts.

Therefore the next closure order is evidence-driven: close the native analyzer Cargo registry surface first, then choose the SDL3 host/source policy. Optional Lua/netplay remain outside the baseline closure.

### C3 — SDL policy

C2 proved this is a runtime/backend dependency, not the generation-time network blocker. System SDL2 already completes the full generated Uniracers native build offline. The default SDL3 path still needs an explicit host-SDL3 or repository-owned-source decision.



Resolve the first demonstrated SDL3 dependency either as a documented host prerequisite or exact local SDL3 source/archive. Force `SNESRECOMP_SDL3_FETCH=OFF` in the offline gate unless a local `SNESRECOMP_SDL3_SOURCE_DIR` is explicitly supplied.

### C4 — Rust analyzer closure — complete

C2 proved the canonical generation path invokes `recompiler-rs`. PR #68 vendors the exact locked closure: 11 registry packages, 476 files and 5,874,431 bytes. Bootstrap overlays the repository-owned Cargo source config and `vendor/` tree into the disposable staged `recompiler-rs` directory while byte-checking its copied `Cargo.lock` against the immutable framework archive. Acquisition run `36667274511` proves an empty-`CARGO_HOME` `cargo build --locked --offline --release --bin snesrecomp-analyze` succeeds. A broad repository `private/` ignore initially omitted checksum-protected crate files; the repair gate force-tracks the complete vendor tree and proves worktree/index parity at 476 files. Final network audit `36668207804` proves both SDL2 and SDL3-fetch-off lanes rebuild the analyzer from empty Cargo homes, regenerate Uniracers, and make zero observed AF_INET/AF_INET6 connect/send attempts during project generation/configure/build. SDL2 also completes the full native executable build. Rust 1.97.1 remains an explicit host/compiler prerequisite provisioned before tracing.

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

C4 is complete. Resolve C3 SDL3 policy next, then migrate the permanent native build smoke away from recursive SNESRecomp submodule checkout.

The safest first artifact is an exact source archive or mechanically materialized tree of `cd5875c...`, accompanied by:

- source hash;
- PolyForm license/provenance;
- explicit records for the two nested gitlinks;
- an acquisition workflow that can rederive the copy from upstream once;
- a bootstrap path that consumes the local copy;
- a clean-checkout canonical generation/build smoke with network source fetching disabled.

Only after that experiment should the project decide whether to keep SNESRecomp as an immutable archive, an active vendored tree, or a small maintained UR-Recomp derivative.
