# Independent QA-02: real Win32 typed-before-intent-retirement crash

**October 16, 2026.** This is a **positive bounded F3 process-crash subtest** on PR source, not a nominated merged-main release candidate or a QA-02 gate pass. Original source [run 38970800847](https://github.com/gamesbyian/UR-Recomp/actions/runs/38970800847); [machine byte receipt](../analysis/evidence/qa02-pr1713-win32-typed-finalization-independent-20261016.json). The actual tested source was GitHub's merge commit `97df30552f00e0b1446059ce28b64af5bd9fea0b`, with parents main `19cddcba` and Modern `4432ad0c`. It does **not** upgrade the original nominated source `11501a15` or original ZIP SHA256 `5605aaf2`.

## Source and package identity

Independent QA downloaded five **source-original** Actions ZIP envelopes, CRC-checked each and checked all five externally pinned SHA256 hashes. The fault archive was `12077656268`, full ZIP SHA256 `59531ede703663a9cb36d316ca11b91b2eaeae09f9c75ff7c9051e36a9f5db62`, **64/64** members, no ROM or executable. Actual same-run candidate binding identifies ROM-free portable ZIP SHA256 `8ae354c3fb9641d0d7708c09f7521e568baaac65d4c4db30cca1fc97028fb379` and AMD64 PE SHA256 `29d871b06018a5db3134a8552d98c1c6c61a53ecd77c6f056f7d4ebd208ba78c`. QA independently extracted that same executable from the portable ZIP, verified its MZ/PE32+ AMD64 header and manifest hashes, and inspected the 13/13 passing actual Win32 hosted source-guest journeys. Physical SDL joysticks were **zero**; sound ran under dummy/disabled audio, not hardware acceptance.

## Actual original guest crash after typed publication

The Win32 original guest reached source-backed **frame 1952** and wrote a genuine 8,192-byte raw SRAM delta of **28 bytes**. The typed profile checkpoint committed generation **1 → 2** before source instrumented forced process exit **87**, with its prewrite intent still present. Independently checked snapshots show:

- Raw `before` SHA256 `bd9571f8...`, raw `crash` and `after` SHA256 `2f3009bb...`, exactly 28 changes.
- Typed `before` SHA256 `1f98e49d...`, typed `crash` and `after` SHA256 `5b896030...`; complete decoded new `stock_sram` is identical to the real new guest raw.
- Selector and catalog identical across all three stages. The 33,094-byte crash intent and its immutable archived receipt are byte-identical SHA256 `5e32c9df...`, and its versioned frame embeds the exact complete previous/new typed checkpoints.
- A **first real Windows cold guest** log shows reconciliation and then successful stock SRAM boot, while a separate **second cold guest** log shows successful stock SRAM boot **without repeating reconciliation**. The source producer asserts no canonical change across that second boot; independent QA has the three-stage first-boot bytes and the second log, not a full independently hashed fourth-stage after-second-boot snapshot.

The normal earlier post-raw/**pre-typed** crash was independently accepted as a separate positive **subtest** in [the earlier report](QA02-PR1713-REAL-WIN32-JOURNAL-INDEPENDENT-20261016.md), with original-byte equivalence to the immutable negative failure separately executed in [run 38971762540](https://github.com/gamesbyian/UR-Recomp/actions/runs/38971762540). The F3 evidence newly establishes the other side of typed publication, without claiming physical disk power durability.

## Synthetic partial-write recovery is a narrower fixture test

The same Windows candidate's `simulated_partial_raw_explicit_rollback` route takes an **already source-authored genuine guest save**, truncates its copy to **513 bytes in a disposable fixture**, then tests the ordinary actual native executable. The observed new process refuses unsafe recovery; a separate explicitly chosen typed rollback logs a successful choice; two further real Windows processes boot committed SRAM cleanly. The producer reports immutable archiving of the partial raw and intent. Independent QA verified the logs and JSON report SHA, but the complete original 513-byte partial source was **not retained as a separate member** for a direct before/after byte-hash audit. Crucially, **no real Windows partial write or actual full-disk/NTFS denial occurred in this test**. It must not be used as evidence that hardware power loss is safe.

## Evidence preservation and next actions

The five original run-38970800847 ZIP envelopes were separately copied to an owner-private archive before October 23/30 expiry. They were individually downloaded back, and all five complete original SHA256 hashes, byte equality and ZIP CRCs matched. No ROM/private user data or large artifact has been committed. Private storage identifiers remain out of this public report.

**Outstanding P0:** merge a settled Modern owner fix; nominate the actual merged-main source/ZIP/PE; exercise the no-argument packaged player R/T/S/Q menu, historical real two-profile crash and healthy alternate, genuine post-publication Windows I/O denial/full-disk and simultaneous-process races, and independently verify non-destructive restart idempotence on that one candidate. Genuine two-pad/audio/display and power interruption need physical evidence. This is **0 new completed QA gates, 0/45 accepted original/native full USA events, and P0 #1214 remains open** under [RELEASE-QUALITY-LEDGER.json](RELEASE-QUALITY-LEDGER.json).
