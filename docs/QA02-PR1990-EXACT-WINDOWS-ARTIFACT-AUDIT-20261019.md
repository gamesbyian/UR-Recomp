# QA02 independent Windows artifact audit

Review date: 2026-10-19 local. Scope: original downloaded Actions artifacts from PR #1990, not a physical Windows release test.

The five PR-head workflow runs (Windows, tooling units, Modern seam, native build and hygiene) all completed successfully. Offline examination of the original candidate package, its separate binding, the fault corpus, real NTFS exhaustion cases, and player-journey logs produced **167 independent byte/size/hash/structure assertions, zero failures**.

The original four-member candidate package and its PE32+ AMD64 executable matched the separate source binding. Real NTFS exhaustion preserved all four canonical files across before, fault and two cold boots. In the postraw/pretyped case raw data changed while typed bytes remained old; after recovery the typed data reconciled and the second cold boot matched.

**Evidence gap:** The 1P Records report claims an earned run, but the 52-entry archive has no actual 1P run file. It does retain a 2P run/match pair. Request original 1P bytes and before/after Records snapshots for independent verification.

No electrical power interruption, physical controllers, audible audio, UHD output, human recovery, or complete original/native event admission was demonstrated. **Release status remains 0/12 Windows and 0/45 USA events.** No gate credit.


## Recovered supplementary independent 224-receipt audit (Agent 3)

This section preserves a second independently produced archived-byte audit originally stranded in a local handoff. The two reviews overlap; **167 and 224 must not be added together to imply 391 independent cases**. These are artifact integrity checks, never physical release gate awards.

- Product PR #1990 source head `3e110163c1d830b71968badf4f6a1ed435a66074`; original Windows-tested merge source `45655cfd9d3794c7174716d48c4891776214f035`.
- Original [Windows run 39352186714](https://github.com/gamesbyian/UR-Recomp/actions/runs/39352186714). Original two-member outer package archive 12234011436 SHA256 `6e16cd1274ba415b1bb5723e837b7a616d7124517aed89500f7c7f16887e3d5e`. Inner four-member ROM-free ZIP SHA256 `f9f67ac6b2f1babf21fd83566611bceef34cd41cf91b6b034fe64a0a9a1a48d1`; actual AMD64 PE SHA256 `37db9ac9d9b0d820e84b3c71e70ba44cccc4472095605abfea3b7012d540c5cc`. Independently parsed PE machine 0x8664 and PE32+ magic 0x20b. Separate binding archive 12233902626 outer ZIP SHA256 `8f830fd9a7353412efa371be1717aa3e9404cbd5af89860a379f8b3a1ac83c5a` agrees with original sizes and component digests.

| Authentic fault-source artifact | Outer ZIP SHA256 | Verified binary byte/length receipts | Narrow observation |
| --- | --- | ---: | --- |
| 12234740760 native recovery | `34c2b5cf5e3e66868498bf996b81f011011b2f785a8e0f4cb1deb1d6cefe4844` | 150/150 | Crash/cold-restart, journal/prewrite archive and profile isolation |
| 12233867802 pre-intent full NTFS | `294727d628536e6f6dddf41f799d0c5b0761e0410a4f42cd69527848cff57c00` | 16/16 | Old four canonical files unchanged before/denied/two cold boots; Win32 error 112 |
| 12234036383 post-raw full NTFS | `6120e98bfea628e716cce3d8309c52d38d24b113ba186f8bebad500654942264` | 22/22 | 74/8192 raw bytes changed, typed remained old while denied; explicit later recovery and two cold boots |
| 12233981895 held-delete T | `1bf9be96c6c5e14060a67931d9cba6437062203d6a717a371e0bec2d974a35d5` | 24/24 | Real Windows journal-delete denial, explicit retry after release |

Fault archives: 212/212; additional package payload digests: 3/3; separate 2P source-run/sidecar manifest entries: 9/9. **Total independently checked archived SHA256/length receipts: 224/224.** The source-created 2P envelope includes a genuine `.urrun/.urmatch` pair; checksummed body parsing reproduced reported FNV-1a. These do **not** substitute for the missing 1P earned run file.

The 13-case pilot's [timing artifact 12233539254](https://github.com/gamesbyian/UR-Recomp/actions/runs/39352186714/artifacts/12233539254) reported 13/13 executed source journeys, zero errors, 459.156 host seconds and three workers. Its parallel path explains 31 skipped serial-duplicate Windows job steps. Four accompanying tooling/Modern/native/hygiene workflows passed at that source epoch. Scripted semantic controllers do not establish physical two-pad/audio/UHD quality.

**Recovered next action:** publish the original source-earned 1P `.urrun` and report/manifest as a separate archive, preserving QA12's fixed-member package. Candidate exporter and three locally passing ROM-free unit tests recovered in [PR #2020](https://github.com/gamesbyian/UR-Recomp/pull/2020); the real Windows run and independent receipt review are still required. No 0/12 Windows or 0/45 USA event gates change.
