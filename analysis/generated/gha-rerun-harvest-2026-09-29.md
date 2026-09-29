# GHA rerun evidence harvest — 2026-09-29

This note records the one-retry harvest of the reconciled race/course research workflows from main commit `c189e6f48e9cdb69b2f74a54f86f696497fc38c6`.

## Why several useful reruns were red

The research steps themselves completed in several workflows, but the persistence steps attempted ordinary `git add analysis/generated/...`. The repository's broad `generated/` ignore rule also matched the nested canonical `analysis/generated/` directory, so new evidence files could not be staged. The repository now explicitly re-includes `analysis/generated/**`; disposable build/game-derived generated output remains ignored elsewhere.

## Promoted rerun evidence

| Workflow | Attempt-2 run | Outcome worth retaining | Durable repository evidence |
|---|---:|---|---|
| Course byte11 exact writer PC | 36538122650 | Exact writes captured. Decoded `0x0F` write is IPC `81:B9C8`; all `0x10..0x16` mutation writes are IPC `82:E1E1`. | `course-byte11-exact-writes.json` |
| course runtime payload probe | 36538122823 | Expected stream 11 wins; decoded cursor advances exactly 21 bytes to `decoded_size - 1`. | `course-runtime-tour2-tail-cursor.json` |
| Historical SMV first-race replay | 36538122590 | 2014 submission reaches first race at frame 794 and first results at frame 2874 on pinned Snes9x/snesref. | `historical-2014-smv-metadata.json`, `historical-2014-first-race-reference.json` |
| RNC scope-entry decoder probe | 36538122596 | Decoder/scope classification completed; persistence alone failed. | `rnc-writer-decode.json` |
| Course header cadence | 36538122757 | Header report remained current; trailer corpus/report regenerated. | existing `course-header-cadence.md`, new `course-trailer-structure.md` |
| RNC static integration classification | 36538122812 | Classification regenerated; content matches the already tracked report. | existing `rnc-decoder-signature-search.md` |
| trace course-buffer writers | 36538122669 | Trace succeeded and corroborates the 0F then 10..16 write sequence. | key result promoted into exact-writer JSON and research ledger |
| trace race-entry WRAM writers | 36538122700 | Trace succeeded. | retained as Actions artifact; no duplicate raw trace promoted here |
| Analyze reference ROMs | 36538122617 | Completed successfully. | normal generated inventory commit path already succeeded |
| SMV tooling regression | 36538122573 | Completed successfully. | regression validation only |

## Deliberately not promoted as a completed result

The 2008 historical WIP run 36538122647 successfully extracted the controller stream, built the reference engines, traced a complete reference replay, and composed reference-side evidence. Native historical replay then failed. The uploaded artifact is useful diagnostic evidence, but no complete native/reference comparison was produced, so this harvest does not invent `historical-2008-dragster-replay.json` or claim that milestone closed.

The trailer workflow also generated a machine-readable `course-trailer-structure.json`, but that file was neither uploaded nor printed in the retained log. Only the exact recoverable human-readable report is promoted here. It can be regenerated deterministically now that `analysis/generated/` is stageable.

## Workflow lesson

A red research workflow is not automatically a failed experiment. Read step-level status before rerunning: computation, validation, persistence, and publication are separate failure domains. When computation succeeded and an artifact/log preserves the output, harvest it instead of burning another research run.
