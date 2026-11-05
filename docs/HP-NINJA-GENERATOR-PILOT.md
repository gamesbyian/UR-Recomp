# Owner HP: manual Ninja build-generator acceptance

**Scope:** source-bound Windows x64 acceptance. The owner-run manual Ninja
trial passed actual full HP game packaging, QA09 and QA05 5/5. A proposed
trusted-main-only automatic HP selection retains canonical Visual Studio
fallback if the installed tool or source-pinned SDL3 cache is unavailable.
Hosted PR acceptance remains Visual Studio. No PR checkout is sent to HP.

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
pagefile/power, or user files change. The owner installed it, and a real HP
manual run verified the receipt and pinned executable before compiling.
The workflow itself never installs any machine software.

To repeat the strict manual trial, select **Actions > HP current-source native
Windows smoke > Run workflow > main > ninja_trial=true**. Manual dispatch
with `ninja_trial=false` continues using Visual Studio. Trusted-main push
builds may separately request `hp_ninja_auto=true`: if and only if the
read-only pinned executable check and fully validated static SDL3 package
succeed, the HP selects Ninja. Otherwise it explicitly logs VS fallback.
No PR, fork, non-main branch or generic matching runner may select either
Ninja route. A selected Ninja CMake/compile failure fails the job and is
**not** silently replaced by a passing VS build.

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


## Physical same-source generator A/B, October 31, 2026

The owner's installed Ninja 1.13.2 was actually verified by the trusted
main manual workflow. Both runs used source SHA
`a4d365b42dc8fd92cb1ece45e61f878c45d7f599`, HP runner
`hpmini-ur-recomp`, static SDL3 cache HIT and identical fingerprint
`8c3bc49199d48d7ea5a49085`.

| Actual host result | Visual Studio | Ninja Multi-Config |
| --- | ---: | ---: |
| Windows Actions run | [#41138892673](https://github.com/gamesbyian/UR-Recomp/actions/runs/41138892673) | [#41148220801](https://github.com/gamesbyian/UR-Recomp/actions/runs/41148220801) |
| Whole job log span | 423s | 338s |
| Compile phase (Ninja includes configure) | 112s | 33s |
| Mean/peak 10s host compile CPU | 12.7% / 15.6% | 45.3% / 57.6% |
| Minimum available physical memory | 7,491 MiB | 7,823 MiB |
| PE/ZIP/race/QA09/QA05 | PASS/5 of 5 | PASS/5 of 5 |

Ninja's actual executable SHA-256 is
`e52a7ad9538d9618c67a0bd777964e2eec8a30f68b810a2f6adce1f2daf847b8`
from `HP_NINJA_CANARY=verified`. The Ninja job logged
`HP_NINJA_CANARY=actual_game_compiled` and passed the same real Windows
package/boot/controller/audio and user-state tests. This is a **20.1%
whole-job saving (85s)** and 70.5% shorter timed compiler phase, with
roughly 3.6x the average host CPU use during that phase. Neither result
credits original/native game fidelity, owner physical H01–H07 or release
gates.

## Automatic main-push rollout and fallback contract

The HP owner-installed binary is still *optional*. The new caller input
`hp_ninja_auto` is true **only** for owner HP main push; the reusable job
refuses it on hosted PRs, alternate branches, manual dispatch and when
combined with the strict `hp_ninja_canary` trial mode. The Python preflight
refuses automatic push use unless passed the explicit
`--allow-trusted-main-push` argument **and** the exact private runner,
repository and main ref match. It rechecks the receipt, SHA-256, Ninja
version, no redirected ancestors or extra files every run. No environment
change persists beyond the single build step. A missing/invalid tool,
missing approved SDL3 static install or refused preflight selects the
unchanged Visual Studio source build with an explicit fallback marker.
A selected Ninja compiler or real package/QA failure fails the job.

On regression, rollback is a one-line workflow input change:
`hp_ninja_auto: false` in the owner HP caller, leaving the earlier
strict manual trial intact. No Windows machine action is required; the
owner can also use the separate one-click Undo package if desired.
The PR requires full hosted VS package and tooling acceptance, independent
review, then **one actual post-merge HP automatic Ninja run**. Never
ascribe the manual timing to an automatic run before that evidence exists.

## Owner HP compiler-worker utilization experiment (10-job candidate)

The verified Ninja selection on [HP automatic run #41149867355](https://github.com/gamesbyian/UR-Recomp/actions/runs/41149867355)
configured and compiled in **39 seconds** using the original hardcoded
`--parallel 6`, averaging **53.1%** host CPU in 10-second compile windows,
peaking at **64.7%**, with at least **8,020 MiB** of free physical RAM
during the job. The machine has 12 logical processors. The actual full
Windows package/QA (including QA05 5/5, QA09, race result) passed.

The bounded next experiment raises **Ninja compiler concurrency from 6
to 10** only in the source-owned Ninja canary script. It logs
`HP_NINJA_BUILD_JOBS=10`. This leaves two logical processors of
nominal capacity for the OS and other work. The already source-pinned
SDL3 static cache, verified Ninja executable identity, canonical
Windows package and gameplay acceptance are unchanged. There are no
machine service, PATH, paging, power or runner-installation changes.

**Acceptance before promotion:** exact-head tooling and hygiene,
independent review of the compiler change and full hosted VS Windows
package acceptance. After merge, observe a normal trusted-main HP run
and compare its actual Ninja compile phase, mean/peak host CPU, available
physical and virtual RAM, entire job elapsed, and every mandatory
package/controller/audio/race-result test against the 6-worker baseline.
Do not infer a gain from the job-count value alone. If compiler failure,
memory pressure, physical HP instability or QA regression appears,
revert the one-line job count to six. No claim to physical owner
H01–H07, original/native event parity or a release gate.
