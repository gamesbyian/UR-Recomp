# Owner HP: manual Ninja build-generator acceptance

**Scope:** opt-in, trusted-main-only Windows x64 experiment. The normal HP
push route and hosted PR route continue using the already accepted Visual
Studio 2022/ClangCL generator. There is no automatic Ninja promotion.

## Grounded starting evidence

- [HP same-source cold/warm run #41130296091](https://github.com/gamesbyian/UR-Recomp/actions/runs/41130296091): source-bound static SDL3 cache `miss` then `hit`, 594s then 446s full job log span, real Windows package/QA 5/5 both green.
- [Hosted Ninja compiled-and-packaged run #41132158388](https://github.com/gamesbyian/UR-Recomp/actions/runs/41132158388): source-derived SDL3, actual Ninja Multi-Config/ClangCL AMD64 executable, complete portable package, race result, QA09, QA05 5/5, fresh-data and startup checks PASS. Ninja configure+build marker 55s on a hosted runner, NOT a proven HP speedup.
- Disposable [#2884](https://github.com/gamesbyian/UR-Recomp/pull/2884) was intentionally closed without merging its hosted caller override, which would have silently replaced the Visual Studio parity route.

## Installation and invocation contract

An owner-invoked one-click package, `UR-Recomp-HP-Ninja-OneClick.zip`, installs
the **official Ninja 1.13.2 Windows asset** into the dedicated portable
`C:/DevNode/runner-tools/Ninja/v1.13.2` directory. It validates the
official release ZIP SHA256
`07fc8261b42b20e71d1720b39068c2e14ffcee6396b76fb7a795fb460b78dc65`,
writes a hash-bound owner-install receipt, grants runner read access and
provides a receipt-checked undo command. No global PATH/service/registry,
pagefile/power, or user files change. The owner has not yet confirmed
installation and this workflow does not perform an installation.

After installation, manually select **Actions > HP current-source native Windows smoke
> Run workflow > main > ninja_trial=true**. All automatic `main` pushes
still pass `hp_ninja_canary=false`, and the reusable workflow rejects
Ninja selection outside a trusted owner HP `workflow_dispatch` on `main`.
Do not dispatch from a PR, fork, alternate ref, or generic matching runner.

Before invoking Ninja, the HP checks its exact existing install path,
receipt identity, Ninja version, SHA256 of the installed executable,
no extra or redirected files, and `hpmini-ur-recomp` runner identity.
Any mismatch fails before building; no downloaded binary, mutable cache
entry, or implicit machine install substitutes for this check.

The accepted compiled executable is the **actual candidate** consumed
by the unchanged canonical PE/import, ROM-free package, Win32 renderer,
race-result, QA09 controller, QA05 audible five-attempt restart, cold
state, persistence, and startup checks. It uses the same source-pinned
static SDL3 package with source fallback disabled and the Visual Studio
ClangCL/SDK environment; a missing prebuilt SDL3 is a failed trial.

## Benchmark and decision

One trusted-main full VS (automatic) and one explicit Ninja trial on the
**same exact source** are needed before adoption. Record source SHA,
SDL3 fingerprint and hit/miss, actual Ninja version, real PE digest,
whole-job elapsed, configure+build versus VS compile phase boundary,
10-second CPU mean/peak, minimum free virtual/physical memory,
all QA outcomes and interrupted-run evidence. The Ninja compile phase
contains CMake *configure plus build*, while the standard VS compile
phase excludes configure; use end-to-end job duration for the primary
comparison. Do not infer 55-second hosted timing on HP or credit
new physical H01-H07, USA original/native events or release gates.

**Stop and rollback:** a missing Ninja install, cache corruption, wrong
receipt, new Win32 failure, or physical HP anomaly leaves the normal
Visual Studio path unchanged. The installer has a separate Undo command.
The workflow never modifies owner machine settings or silently changes
the default generator. Merge/rollout requires final-head hosted unit,
workflow syntax/hygiene, unchanged real Windows VS QA and independent
source review; later HP trial needs actual source-bound results.
