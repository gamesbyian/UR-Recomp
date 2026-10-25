# One-build Windows candidate-only producer

An opt-in reusable GitHub Actions workflow, .github/workflows/windows-exact-build-only.yml, exposes a byte-verified Baldosa AMD64 product candidate **without running the existing ~13 real player journeys in its producer job first**. It reuses the actual five unmodified source-pin, RF015/RF017 boundary, clang/toolchain, build and fixture commands from the main Windows native bridge. The strict read-only source-body auditor rejects silent divergence whenever that bridge evolves.

The candidate-only producer checks exact pinned Baldosa submodules, original USA ROM, AOT LLVM 22.1.8, source-epoch COFF PE timestamp, and package manifest contents. It exports the same five named ROMless candidate transport files as the existing full bridge: source-commit.txt, SHA256SUMS, UniracersSNESRecomp.exe, ur-baldosa-modern-profile-fixture.exe, and UR-Recomp-Baldosa-Windows-x64-ROMLESS.zip. These are compiler/package artifacts, **not** accepted Windows functional evidence. They contain no ROM or user saves.

The existing windows-acceptance-fanout-pilot.yml consumer jobs may use one of these verified artifacts on the exact same source. A consumer still independently reruns all 13 original Windows bridge player journeys, fail-closed on missing or cross-source evidence, while the full Windows bridge still owns its additional Options, display, fault, ROM startup, CMD, packaging and release QA routes.

Before promoting this approach, dispatch an end-to-end compute pilot and compare *candidate-build-only + two real consumer jobs* with the measured ~17-minute full native bridge (same source, same target). Track wall time, per-runner minutes and all original test success. A passing candidate-only build is strictly not a release gate; independent Windows/hardware review remains separate.

Unit contract: python3 -m unittest tests.unit.test_check_windows_build_source_reuse
