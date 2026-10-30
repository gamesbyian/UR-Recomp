# Hosted Ninja Multi-Config full Windows package canary

**Status:** experimental, hosted-only, separate from the owner's HP runner.
Source review and actual hosted Windows gameplay/packaging acceptance are required
before this approach is considered a replacement for any production generator.

## Why this is worth measuring

The owner's HP exact-source VS 2022/ClangCL build on run #41122361691
spent 220 s in its compile phase, and subsequent installed-static-SDL3 cold
HP run #41130296091 spent 126 s in the game build after a separate SDL3
bootstrap. Its 10-second host CPU mean during compile was only 17.7%.

Closed disposable PR #2881 on hosted run #41124179949 independently
produced a Ninja Multi-Config/ClangCL x64 PE in 89 seconds including
configuration, with the original VS generator's configuration and build
requiring substantially more. That pilot proved **only** the compiler
and PE import policy. The Ninja-produced game was *not* subjected to the
canonical package, race-result, restart audio, user-data or Win32 QA.

## This bounded hosted package experiment

The reusable Windows smoke accepts `test_ninja_generator_profile`, which
must be both hosted, `test_hp_compiler_profile=true`, and called from a
same-repository pull request. The HP main caller does not enable it, and
the generator retains its existing Visual Studio default on HP/main.

Under the opt-in, the exact previously generated game and verified
staged static SDL3 library are compiled with Ninja Multi-Config using
the pinned VS Build Tools ClangCL executable and Windows SDK environment.
The source-FetchContent fallback stays disabled: Ninja must actually link
the verified static SDL3 install. The rest of the canonical Windows smoke
owns the resulting executable and runs its unmodified PE/import checks,
portable ZIP, race/result, controller QA09, five QA05 restart/audio
witnesses, Unicode/fresh user-state acceptance and startup negatives.

**Stop on failure** at the first compile, CMake, imported-target, PE,
packaging or real Win32 step. Do not call a Ninja build a release
candidate on compile success alone. Do not enable HP Ninja without
separately verifying available `ninja.exe` on that physical runner;
if local installation is required, prepare a pinned, one-click,
reversible package for the owner. No change to the owner PC is made
by this experiment.

Compare the full hosted source-bound build/QA against the successful
VS/static-SDL3 host #41127822278, then design a reversible HP-only
canary with exact source and identical acceptance if evidence warrants.
Physical H01-H07, 45 authentic USA event and release gate results are
unaffected.
