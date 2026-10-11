# Baldosa Windows shared-build reliability campaign

**Classification:** manual, bounded research/reliability testing; not a release pass or independent QA-01 event oracle. Entry point: [Baldosa Windows shared-build reliability campaign](../.github/workflows/baldosa-windows-reliability-campaign.yml). See [CI workflow practices](CI-WORKFLOW-BEST-PRACTICES.md), [player journeys](QA-PLAYER-JOURNEYS.md) and [Baldosa migration](BALDOSA-FIRST-CORE-MIGRATION-20261009.md).

## Why this campaign exists

The existing [Baldosa native Windows x64 bridge](../.github/workflows/baldosa-windows-native-bridge.yml) already compiles and exercises the **actual pinned Baldosa executable with UR host hooks**. It proves guest-level 1P/2P execution, authentic native pause/resume/restart, exact guest-frame CRC stability, Modern profile SRAM, fresh-process restarts, invalid roots and corruption rejection. Its **actual ROM-free Windows ZIP** is separately exercised with the real CMD launcher against missing/wrong ROM, junction/unsafe data roots, valid guest boot and failed profile selection. These are already-source-owned producers, not new simulation models.

Previously, running this again meant rebuilding the Windows executable for each invocation. The new manual wrapper **calls the existing full Windows bridge once**, exports its *previously verified*, SHA-256-pinned Windows executable, real typed-profile codec fixture and ROM-free ZIP, and fans out four independent runners against the same exact bytes. There is no source ROM, save file or secret in the shared artifact. The independently checked original USA retail ROM and pinned historical controller script come from each runner's exact source revision and 10b864b9 Baldosa checkout. A change in source, artifact hash or expected route identity fails closed.

## Test population and execution

The matrix has **two independent guest-lifecycle shards** and **two independent ROMless-CMD-launcher shards**. Each repetition receives a newly created private data root, launches genuine Windows processes and runs the *unchanged* respective existing producer.

| Suite | Actual checks repeated | Explicit exclusion |
| --- | --- | --- |
| `guest-0`, `guest-1` | Real Windows native guest 2P route and 2,473 per-frame WRAM CRCs versus paused execution; SDL pause and delayed restart, 1P/2P Modern root/race entry, named two-profile SRAM, fresh-process persistence, pause/quit, interrupted raw-versus-typed publication, corrupt profile and bad data roots, Records read-side | Does not finish a complete authenticated Race/Circuit/Stunt event or prove physical gamepad/audio |
| `launcher-0`, `launcher-1` | Extract the exact ROMless ZIP; actual Windows CMD refuses missing/wrong ROM, package-local/relative and reparse-point save paths; legitimate stock ROM boots native shared Modern root and saves 8-KiB SRAM externally; bad native profile fails without changing saved bytes | Doesn't prove a full controller-first 1P/2P result-to-Records journey or hardware |

The `trials_per_shard` input allows `1`, `3` or `10` repetitions: **4, 12 or 40 full producer invocations** in one dispatch. Each guest invocation itself supervises many distinct actual game processes and hundreds/thousands of frame assertions, so a 40-invocation run is far larger than 40 individual assertions. **Two** Windows shard runners execute concurrently; each has a four-hour bound. Failed suites stop after two failures, preserve bounded diagnostic excerpts in the machine result and leave their private roots only on the ephemeral runner. They never upload raw gameplay ROMs or personal data.

**Start with `1`**, first validating the build-export/reuse, Windows dependencies, genuine script route and four coherent SHA-bound receipts. Advance to `3` and then `10` only after reviewing actual wall time and first-run classifications, never to mask a real failure. A later manual run starts from a nominated exact ref; automatic PR behaviour of the underlying bridge remains unchanged. Manual dispatches are never cancelled by new commits.

## Outcomes and maintenance

The producer `tools/qa_baldosa_windows_reliability_batch.py` does not reimplement gameplay or native stores. It spawns the two existing source-authenticated Windows acceptance programs and validates their original typed receipts. The independent aggregator requires all four named shards, identical source SHA, same verified native binary/fixture/ZIP/script/ROM hashes, exact requested trial count and no unexpected receipts. It distinguishes `completed_positive` from `invariant_violation` and `incomplete_or_failed` without giving a green job to missing results. Compact JSON and Actions Job Summary name the exact failing shard/iteration. Artifact receipts have 14-day retention.

**Limits:** even a green 40-invocation batch certifies only the repeated established Windows native bridge and the ROMless launcher contract. The old patched Modern backend and current Baldosa integration are not proven interchangeable; this is not a full, settled-result Windows product acceptance or release-ready ZIP. Independent original/native QA-01 and Windows physical gamepad, audio, graphics, real 4K and release ownership remain separate. **QA-01 0/45**, `RELEASE-QUALITY-LEDGER.json` and source-owned scientific validators are never changed by this workflow.

**Retirement:** once an integrated, single exact Windows/Baldosa candidate publishes genuine 1P and 2P results then reopens Records in a fresh process, migrate the same shared-build/shard/receipt mechanism to those real product journeys and retire this historical bridge research campaign if superseded. Avoid a second generic CI framework.
