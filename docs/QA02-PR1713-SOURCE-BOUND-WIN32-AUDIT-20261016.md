# QA-02/03/04/09/11/12: independently inspected Windows PR #1713 candidate bytes

2026-10-16. **Source-exact draft-PR Windows technical regression, not release acceptance.** The machine receipt is [qa12-pr1713-win32-byte-disposition-20261016.json](../analysis/evidence/qa12-pr1713-win32-byte-disposition-20261016.json). Original workflow [38958955267](https://github.com/gamesbyian/UR-Recomp/actions/runs/38958955267).

## Actual tested source and package

PR head 6cda18742b85c03f3a381c4b52bc61861d18be83 is not the GitHub checked-out source. The real CI source is **PR merge 075cbb9ca1711d1e22a6369f8bd491232b8b8ef2**, whose two parents are main af85cf1797fc9a4357e2fa67a6d0ad5e59d2b77f and PR head 6cda1874. Independent downloads verified five original Actions ZIP hashes and ZIP CRCs; inner portable ZIP (5,984,347 bytes) SHA256 **3ad74e5d9ab9a921bc7e2bb50add5a5240d54928884be7f6306aba0cac77b3c3**, actual PE32+ AMD64 SHA256 **bef2d8ae426bdb97f1b4650c13e336cf02ddad4465db605e7be111182087e3e0**. Immutable package manifest, recorded Windows journey executable and same-run candidate binding match. The private ROM was not packaged.

The five artifact IDs and **distinct original-wrapper SHA256 hashes** are in the machine receipt. Expiry was October 23 when downloaded; these are PR-derived temporary artifacts, never the still-nominated source 11501a15 and ZIP 5605aaf2.

## Proven hosted Win32 product regression

The downloaded source parallel journey report shows **13/13 executed cases exit zero**, same exact tested PE. Genuine Windows guest route reports a scored MIKE rider-0 vs MARTIN rider-2 2P race, source observed 2761/2757 hundredths and rider-2 winner. The downloaded authentic .urrun checksum matches the .urmatch run binding; the archived disposable profile catalog and both typed stock SRAM hex bodies are byte-identical to their respective **8192-byte raw save**. New real Windows processes opened Records with **MIKE LOSS 00:27.61** and **MARTIN WIN 00:27.57**. No additional match was assumed. That is a real Win32 hosted result-to-record regression, **not** physical pad validation: the logs explicitly show zero joysticks and SDL dummy audio.

## Product owner P0 recovery candidate, independent gap

The genuine Win32 source producer reports a paused guest frame 1952 raw write before injected Exit(86), then an old unjournaled cold refusal and a journaled cold reconciliation followed by an actual guest boot. These are valuable positive product implementation observations, but no newly retained before/crash/after raw and typed SRAM files, pre-write intent, recovery receipt or repeated cold-boot bytes are available in the downloaded 52-member journey evidence. The report field alone does not independently qualify recoverability. The QA-owned [read-only original and journaled archive verifier](../tools/check_qa02_win32_fault_snapshots.py) is merged, green and ready to compare the future original bytes.

**Handoff:** product implementation owner #1713 should export bounded source-pinned disposable archive with full three-stage bytes, intent, recovery receipt and independent cold restarts through the same actual Windows process path. Independent QA will apply the [F0-F7 acceptance protocol](QA02-NEXT-EXACT-WIN32-RECOVERY-INDEPENDENT-ACCEPTANCE-20261016.md) to a **newly nominated merged-main** package, not silently replace the immutable old candidate. Explicit end-user-accessible recovery of historical unjournaled mismatches, genuine IO failure, two physical pads, audible output/display and later tournament legs remain outstanding.

**Release ledger intentionally untouched.** P0 #1214 remains open, zero of twelve independently completed release gates, zero of 45 independently accepted original/native complete USA events and no physical hardware approval.
