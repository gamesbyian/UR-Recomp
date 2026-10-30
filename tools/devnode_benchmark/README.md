> **October 30 update:** The October 29 comparison below is historical. The
> exact-main HP Windows build passed in [run #41122361691](https://github.com/gamesbyian/UR-Recomp/actions/runs/41122361691), including 5/5 QA-05 and concurrent race-result. Its 220-second compile interval averaged 21.2% host CPU; static SDL3 occupied about 88 seconds. This does not meet physical H01–H07 or original/native release-gate acceptance.

# Owner HP Windows runner diagnostic

This manual-only workflow compares a **real repository-owned C++ Tour regression** and three Windows Python unit-test modules on the owner's permanent Windows 10 HP runner and a hosted `windows-2022` reference.

Run `.github/workflows/owner-hp-windows-benchmark.yml` manually with GitHub Actions after it is integrated. The job uses generic `[self-hosted, Windows, X64]` labels, but its Python bootstrap **fails before any benchmark** unless `RUNNER_NAME=hpmini-ur-recomp`, the exact runner name observed in the successful [HP run #40975340422](https://github.com/gamesbyian/UR-Recomp/actions/runs/40975340422). A future second matching Windows runner may receive and fail the job; for deterministic routing, register a unique owner-controlled runner label and narrow `runs-on` in a separately validated workflow change. Never attribute a run to HP from generic labels alone.

The HP bootstrap (`prepare_python.ps1`) caches **Python 3.12.10 from python.org's embeddable distribution** under the runner's writable `_work/.devnode-tools/` directory. It checks the ZIP against SHA-256 `4acbed6dd1c744b0376e3b1cf57ce906f9dc9e95e68824584c8099a63025a3c3`, published for that exact download in the [Python 3.12.10 release SBOM](https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip.spdx.json). Every run rehashes the cached archive and re-extracts its verified contents, rather than executing mutable, previously extracted DLLs. A bad cached archive fails closed; an old extracted installation is replaced. This avoids user-only Python paths and registry changes inaccessible to the NetworkService runner account. The interpreter version is also checked and the repository checkout is exposed for unit tests. Extraction overhead is not a native build-speed measurement.

The benchmark runs the identical source test executable with CMake's **Visual Studio 2022 C++ generator**. Its build directory persists under `C:\DevNode\build-cache\ur-tour-benchmark` on the HP; the hosted build is ephemeral. Record setup, Python unit test, CMake configure, compile, no-op rebuild, and executable durations separately. Warm cache and CPU speed are confounded unless comparing matched cold/warm states.

## Empirical results, October 29, 2026

- Hosted baseline: [run 40972578686](https://github.com/gamesbyian/UR-Recomp/actions/runs/40972578686) had Python tests 10.172s; CMake configure 12.297s; native compile 2.375s; no-op rebuild 0.609s; executable 0.187s.
- HP success: [run 40975340422](https://github.com/gamesbyian/UR-Recomp/actions/runs/40975340422) had Python tests 6.343s; warm configure 0.157s; compile 0.703s; no-op rebuild 0.703s; executable 0.015s. This proves that the runner can perform useful native C++ work, **not** that the HP is faster for a full Windows build.
- A separate [owner native build probe, run 40975673146](https://github.com/gamesbyian/UR-Recomp/actions/runs/40975673146), reached CMake with the genuine `-T ClangCL` generator but failed `MSB8020`: the HP's Visual Studio 2022 Build Tools installation lacks the ClangCL toolset. Fix by adding Microsoft's `Microsoft.VisualStudio.Component.VC.Llvm.Clang` and `Microsoft.VisualStudio.Component.VC.Llvm.ClangToolset` components. Full-game compilation has **not** passed on the HP.

The service account lacks permission to create Windows symbolic links (WinError 1314). The affected symbolic-link negative test now reports an explicit **skip** without skipping separate archive, executable identity, or revision validation. Native launcher CWD comparisons use Windows case-insensitive path normalization.

All results are diagnostics only: **no playable-game, original/native parity, physical machine, release-QA or artifact acceptance credit**. Do not redirect release-critical workflows merely because this small test passes. Source hashes and artifact receipts in the Actions runs remain authoritative; do not publish ROMs or user save data.


## HP reusable static SDL3 install canary

The exact native build currently recompiles SDL3 on every fresh generated
Windows game build. The opt-in/preflighted helper
tools/devnode_benchmark/prepare_sdl3_cache.py builds a local source-derived
**static** SDL3 install with the same ClangCL, VS 2022, static CRT and release
configuration. It writes a manifest containing SHA-256 of every installed
file. An immutable identity includes the canonical source archive, the fully
staged SDL3 source tree, ClangCL/MSBuild/CMake binaries, SDK version set and
compiler recipe. Changed source/toolchain yields a different cache entry;
tampered, incomplete or DLL-bearing entries are rejected.

The HP main-only route uses persistent runner-local storage under the
workspace parent, outside the temporary project generation directory. A
failure preparing this cache leaves the existing source-FetchContent compile
enabled. The hosted Windows PR candidate with test_hp_compiler_profile=true
requires a valid cache-assisted build and reruns package and product checks.
No PR can reserve the owner's HP. A selected valid install must resolve
with find_package(SDL3 CONFIG), with source fallback disabled so a wrong
import cannot silently pass.

Current decision gate: first pass the **hosted final-head canary**, then
observe a cold HP run and a same-key warm HP run with the exact executable,
package and QA checks, compare wall time/CPU/memory to #41122361691, and only
then claim a measured saving. The first cache cold build costs work and disk
space; unchanged product acceptance rules and the separate 4K/physical
release checks remain in force.
