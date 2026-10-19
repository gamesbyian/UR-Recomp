# RF073: authentic native NMI status and compiled-RTI return brackets

**19 October 2026. Original/native source-authentic research, read-only. Not an accepted USA event.** Exact historical RF054 Zoom Zoo archive ZIP SHA256: 3ccb209a92045e9e89113442e68af51b85a453a160a9b9efaf8ca0d59e79631c; GitHub artifact ID 12149640496. Original log SHA256: 308b8e70122fa1f0ba7edcdc4c8d16e4df0137dc289533f0dc1d90bafae14c5a. Native log SHA256: e7aa6bb4340acbdaa1cc38ff39f601dd0a8dbba24d6a244ffcad82fe8bbd705f. Original and native binary hashes, exact ROM/movie/input and source SHA are permanently retained in the [RF073 receipt](../analysis/data/rf073-authentic-rf054-native-nmi-brackets-20261019.json).

## Executed facts

The RF054 original/native archive has **2,741 independently sequenced native RF047 events**, unique, complete, in exact event order. Sixty-two atomic RF047 events have non-RF047 prefixes caused by the separately fragmented RF044 stderr logger. Two of these contain **genuine compiled RTI markers**. The verifier locates and requires complete RF047 atomic payloads from within their physical stderr line, never infers execution from textual line ordering or the stale native RF044 IPC field.

In all nine actual native NMI frames (1017–1025), the following source-local sequence is observed:

1. Native NMI entry: resume context 82:D4EE, stack pointer 01F0.
2. After real native push: stack pointer 01EC; bytes at 01ED..01F0: **26 EE D4 82**.
3. Exactly one actually executed native stack helper read inside the NMI: physical **00:01ED**, width 1, returned status **26**, stack pointer 01ED.
4. Compiled RTI marker with stack pointer 01F0, without any observed native helper read of saved PC or PB bytes at 01EE..01F0 inside that bracket.
5. Native handler return with stack pointer 01F0. The NEXT native stack helper read, OUTSIDE the NMI, is 01F1=26. It is not evidence of saved PC/bank consumption in the handler.

Nine of nine true source original Snes9x NMI witnesses in this **same historical case** also save status 26. Original source guest PC context 82:D4F0 appears in four frames and 82:D4EE appears in five; native after-push saved PC low is EE in all nine. This is **four frame-labelled original/native saved-PC low differences**, not proof that those interrupts arrived at an identical source/native intra-frame semantic or instruction-fetch point. Actual original and native host clock axes have not been rebased. The native RF047 RTI opcodePC=008588 and returnPC=808588 diagnostic fields are NOT independently decoded fetched opcode PCs; RF044 IPC=80EFDA is stale under AOT. Do not reclassify them as actual executed instruction identities.

## Reproduce, falsify and interpret narrowly

Run the independent verifier on the exact frozen case:

    python3 tools/qa01_rf073_native_nmi_brackets.py /path/to/RF054-actual-case.zip --out /path/to/rf073-report.json
    python3 -m unittest tests.unit.test_qa01_rf073_native_nmi_brackets -v

It checks archive ZIP SHA256, original/native logs, ROM/movie/input and built-original/native identities; 2,741 RF047 event ordinals, nine original physical post-NMI pushes, nine native NMI entry/push/status-read/compiled-RTI/return brackets, native own master ordering, raw status value and the nine first outside-handler reads. Synthetic full-2,741-event negative fixtures reject missing sequences, malformed payloads, truncated logs, wrong stack pointers, corrupt saved PC bytes and counterfeited status. It preserves prefixed original event payloads only when completely parseable.

**What remains unresolved:** all genuine native bus paths, actual fetched native opcode PCs, independently equivalent original/native interruption phase, saved PC/PB reads or skips in source-authentic native machine terms, and which (if any) WRAM difference was actually consumed before overwrite. It would be incorrect to transpose later RF069/RF072 original source-local event ordinals onto this historical RF054 native binary. The remaining 92 unmasked residual WRAM byte occurrences from the other separately authenticated experiments are NOT waived by this native snapshot. This is a bounded CPU/NMI mechanism result, not a gameplay correction or a continuous complete-USA-event pass.

**Accepted full USA courses: 0/45. Windows release QA: 0/12.**

## Independent execution of the exact historical case consumer

A separate, disposable **read-only** [RF073 archive verifier run 39315578731](https://github.com/gamesbyian/UR-Recomp/actions/runs/39315578731) independently downloaded the **exact RF054 2014-original/native case bytes** (GitHub artifact 12149640496), validated their SHA256, and executed the complete native source-local 2,741-event bracket consumer on BOTH authentic original and native logs. The job succeeded. Its newly computed [nine-bracket machine report artifact 12218035427](https://github.com/gamesbyian/UR-Recomp/actions/runs/39315578731/artifacts/12218035427) has ZIP SHA256 6badd597bdcdd2f433e8235fa623d6d4abbfb32d006a82d51d8642e90e53e946. That artifact was separately downloaded, reopened and CRC-checked; the full result agrees on all nine status-read ordinals, 62 other-logger prefixes, 2 prefixed actual compiled RTIs, 4 same-numbered-host-frame source/native low-PC snapshots and the strict USA HOLD. The compact immutable [RF073 receipt](../analysis/data/rf073-authentic-rf054-native-nmi-brackets-20261019.json) holds the tested run and artifact digests.

The first one-shot attempt failed *before input retrieval* because an escaped workflow token caused HTTP 401. It was a workflow expression/authorization problem, not a guest/source instrumentation discrepancy; the corrected one-shot ran the genuine case successfully. Its disposable workflow does not belong in main.

Independent successful archive verification qualifies these *observed native helper brackets*, not full CPU bus-path coverage, a decoded executed guest opcode PC or an equivalent original/native intra-frame interrupt point. **Do not promote any saved-PC difference or 0/45 course acceptance.**
