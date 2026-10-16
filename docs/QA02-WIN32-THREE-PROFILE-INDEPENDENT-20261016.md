# QA-02: independent three-profile Windows isolation and byte preservation

**October 16, 2026. Positive bounded technical subtest, zero release gate promotion.** Original Actions [run 38975446206](https://github.com/gamesbyian/UR-Recomp/actions/runs/38975446206) tested actual GitHub synthetic PR merge **`38d12a32c3023b72a54db934907dfcdc889ff846`**, with parents main `05b51ecf` and Modern implementation `3b0b247b`. The originally nominated negative source remains `11501a15`, ZIP `5605aaf2`. This positive evidence must **not** silently nominate a new release candidate.

## Independent source/PE and original archive

QA separately downloaded four **original** GitHub Actions ZIP envelopes, verified their full SHA256 and CRCs, and independently decoded source-bound package and parallel journeys. Fault archive **12079485622** is **154 entries**, full SHA256 **`f9daca574581efb4e634e689293b282bb692df5e3efdbfb7e586bf1073be3e68`**. Same-run candidate binding is original artifact **12079705129** and portable ROM-free package **12079710047**, inner Windows ZIP SHA256 **`6faf00d9d6571b5c138f6a316affb16e36288abb235b68201d3063e38634a3f5`**, actual PE32+ AMD64 executable SHA256 **`961483ed2961329586ae50e73cb0fdcba0a5105caf1d6f17c8feada648b6871e`**. Pilot **12078629900** records **13/13** source-bound actual hosted Win32 journeys exiting zero. ROM-free package does not bundle game ROM.

## Original three-profile snapshot independent verdict

The added `native_three_profile_unrelated_damage/` group has 35 members. The read-only [source-original independent verifier](../tools/check_qa02_win32_three_profile_original.py) was run directly against the **original Actions ZIP**, not producer summary booleans or a repacked derivative. All **29** canonical binary objects independently match each original receipt SHA256 and byte length, as do the five claimed Windows process logs. Specifically:

- Three independently distinct, canonical **8,192-byte** A/B/C raw saves belong to actual registered names in the source roster.
- The producer deliberately **XOR-corrupts one byte** of selected A raw at offset `0x0711`, and deliberately removes unrelated C typed metadata. QA verifies the *exact one-byte A change* and preserves the original C typed file as a separately hashed exported object. C's actual absence in the live filesystem comes from producer observation rather than a separate read of a running machine.
- A new actual Windows process refuses damaged A before boot. A subsequent attempt to select invalid/damaged C does not complete. The same executable accepts explicit selection of intact B and successfully cold-boots B in **two separate Windows processes**.
- Full A raw, A typed, B raw, B typed, C raw and roster files are unmodified by switching or either cold boot; A's deliberate corrupt raw remains intact for later recovery. Only canonical selector changes A→B exactly once and stays constant through the second cold-boot image. No results or medals are manufactured.

This is evidence that **a damaged unrelated third roster entry does not automatically strand healthy B**. It is *not* a genuine third-profile guest-written post-raw crash, a simultaneous two-process lock race, user-operated interactive packaged R/T/S/Q, real NTFS ACL/full-disk/torn write, or a physical gamepad/audio/display acceptance.

## Negative evidence-contract finding and preservation

The same source original contains a flat `native_intent_restart_recovery/qa02-journaled-snapshot.zip` that is still **18 members**, SHA256 **`baab34946afb4c40d25910620ee9e235a3ea4a846c4085272a826ec2ebdc720d`**, with `intent` incorrectly embedded in the four-label `file-receipt.json` and no standalone `intent-receipt.json`. The merged independent flat QA consumer requires 19 members and a separate intent receipt. This source-level evidence transport mismatch is documented and handed to Modern owner PR #1713. The *original 154-member fault archive* has correctly separated intent and remains independently auditable; no QA verifier should be relaxed to excuse the flat exporter.

All four original whole ZIPs were also copied to owner-private Google Drive and independently downloaded back: every original SHA256, byte count and **158 original ZIP entries' CRC** matched, with no ROM or private backup locator committed. The source-independent [machine receipt](../analysis/evidence/qa02-three-profile-real-win32-original-independent-20261016.json) records exact IDs, hashes, assertions and limitations.

## Gate status

The authoritative [release ledger](RELEASE-QUALITY-LEDGER.json) retains **0/12** independently completed release gates, **0/45** accepted original/native full USA events, QA-02 **in_progress**, and open P0 [#1214](https://github.com/gamesbyian/UR-Recomp/issues/1214). Before full acceptance: settle and merge Modern fix; nominate and independently run the same immutable merged-main ROM-free ZIP/PE, verify real packaged human R/T/S/Q, actual OS I/O and concurrent faults, and genuine two-pad/audio/display. Physical power interruption is not covered by hosted CI.
