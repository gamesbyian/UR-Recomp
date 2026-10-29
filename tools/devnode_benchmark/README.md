# Owner HP Windows runner diagnostic

This manual-only workflow compares a **real repository-owned C++ Tour regression** and three Windows Python unit-test modules on the owner's permanent Windows 10 HP runner and a hosted `windows-2022` reference.

Run `.github/workflows/owner-hp-windows-benchmark.yml` manually with GitHub Actions after it is integrated. The owner machine is selected by `[self-hosted, Windows, X64]`; its existing runner must be online and registered in this repository.

The HP bootstrap (`prepare_python.ps1`) installs **Python 3.12.10 from python.org's embeddable distribution** in the runner's writable `_work/.devnode-tools/` cache. This avoids accessing user-only Python installations and avoids registry changes that fail under the NetworkService runner account. It is reused across jobs, checks the interpreter version, and exposes the repository checkout for project unit tests.

The benchmark runs the identical source test executable with CMake's **Visual Studio 2022 C++ generator**. Its build directory persists under `C:\DevNode\build-cache\ur-tour-benchmark` on the HP; the hosted build is ephemeral. Record setup, Python unit test, CMake configure, compile, no-op rebuild, and executable durations separately. Warm cache and CPU speed are confounded unless comparing matched cold/warm states.

## Empirical results, October 29, 2026

- Hosted baseline: [run 40972578686](https://github.com/gamesbyian/UR-Recomp/actions/runs/40972578686) had Python tests 10.172s; CMake configure 12.297s; native compile 2.375s; no-op rebuild 0.609s; executable 0.187s.
- HP success: [run 40975340422](https://github.com/gamesbyian/UR-Recomp/actions/runs/40975340422) had Python tests 6.343s; warm configure 0.157s; compile 0.703s; no-op rebuild 0.703s; executable 0.015s. This proves that the runner can perform useful native C++ work, **not** that the HP is faster for a full Windows build.
- A separate [owner native build probe, run 40975673146](https://github.com/gamesbyian/UR-Recomp/actions/runs/40975673146), reached CMake with the genuine `-T ClangCL` generator but failed `MSB8020`: the HP's Visual Studio 2022 Build Tools installation lacks the ClangCL toolset. Fix by adding Microsoft's `Microsoft.VisualStudio.Component.VC.Llvm.Clang` and `Microsoft.VisualStudio.Component.VC.Llvm.ClangToolset` components. Full-game compilation has **not** passed on the HP.

The service account lacks permission to create Windows symbolic links (WinError 1314). The affected symbolic-link negative test now reports an explicit **skip** without skipping separate archive, executable identity, or revision validation. Native launcher CWD comparisons use Windows case-insensitive path normalization.

All results are diagnostics only: **no playable-game, original/native parity, physical machine, release-QA or artifact acceptance credit**. Do not redirect release-critical workflows merely because this small test passes. Source hashes and artifact receipts in the Actions runs remain authoritative; do not publish ROMs or user save data.
