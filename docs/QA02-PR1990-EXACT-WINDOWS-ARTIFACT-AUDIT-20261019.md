# QA02 independent Windows artifact audit

Review date: 2026-10-19 local. Scope: original downloaded Actions artifacts from PR #1990, not a physical Windows release test.

The five PR-head workflow runs (Windows, tooling units, Modern seam, native build and hygiene) all completed successfully. Offline examination of the original candidate package, its separate binding, the fault corpus, real NTFS exhaustion cases, and player-journey logs produced **167 independent byte/size/hash/structure assertions, zero failures**.

The original four-member candidate package and its PE32+ AMD64 executable matched the separate source binding. Real NTFS exhaustion preserved all four canonical files across before, fault and two cold boots. In the postraw/pretyped case raw data changed while typed bytes remained old; after recovery the typed data reconciled and the second cold boot matched.

**Evidence gap:** The 1P Records report claims an earned run, but the 52-entry archive has no actual 1P run file. It does retain a 2P run/match pair. Request original 1P bytes and before/after Records snapshots for independent verification.

No electrical power interruption, physical controllers, audible audio, UHD output, human recovery, or complete original/native event admission was demonstrated. **Release status remains 0/12 Windows and 0/45 USA events.** No gate credit.
