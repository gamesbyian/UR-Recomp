# QA-01 Switcher: NMI stack consumer discriminator

**Status:** read-only original-source instrumentation, analyzer and synthetic controls added. **Not yet executed with a new original/native replay.** USA complete-event denominator stays **0/45**; the independent release ledger is unchanged.

## Established paired observations

Original Snes9x and pinned native Switcher Race B both display MIKE **1:08.81** at absolute host frame **5783**. Independently observed entry is original **1079**, native **1081**, giving strict guest-relative result onsets **+4704/+4702 (FAIL)**. On host 5782, VRAM, CGRAM and 21 named state fields agree, but WRAM differs at exactly eight stack-page offsets: 7E:01DD, 01E6, 01E7, 01EF..01F3.

Executed original Snes9x I_NMI+6 PHA at source PC 00:858E saves full A=4042 with SP=01DE→01DC at original ICPU.Frame 5780. An independent native generated I_NMI PHA writes A=4004 at the same SP/stack destination at native snes_frame_counter 5781. These counters **are not calibrated to a common CPU/PPU phase**. PHA width, ordering and stack mechanics agree; saved caller-A words differ.

Sources: [executed original A](../analysis/data/switcher-original-nmi-pha-full-accumulator-executed-20261010.json), [native six-push prologues](../analysis/data/switcher-native-nmi-complete-stack-prologues-20261010.json), [same-host memory](QA01-SWITCHER-5782-RAW-MEMORY-EVIDENCE-20261010.md), [stack original-PC crosswalk](QA01-STACK-PAGE-ORIGINAL-PC-CROSSWALK-20261010.md).

## Pinned game source reasoning and remaining unknown

In gamesbyian/uniracers-recomp at native pin 10b864b9d14a7b7416dd909eb7b054c88faef101, generated src/gen/bank00_part00_v2.c implements I_NMI_M1X1 as PHB, PHD, REP, PHX, PHY, 16-bit PHA, SEP, 8-bit PHA, PLB, PEA, PLD, then indirect long tail dispatch via original NMI handler pointer $0053. The 16-bit PHA saves **pre-NMI A**. It does not prove original/native caller A corresponds to the same beam/instruction cycle. The imported symbol Unused_NmiRestoreRti at $80:859C is labeled an unreferenced duplicate; it is not evidence for the live NMI restore PC.

Next prove whether original saved bytes are actually consumed, establish that restore reader's executed PC and post-restore CPU state, and anchor both engines' NMI entries to a shared host/beam timestamp. An outcome-critical reader would require a bounded gameplay correction backed by both engines. No rules/clock changes are justified yet.

## New optional original-only tooling

- tools/qa01_original_nmi_stack_pull_patch.py inserts a narrowly gated **read-only** architectural pull-scope logger around the single original Snes9x opcode dispatch. It requires the existing Switcher stack/NMI observer and full-accumulator PHA observer installed first into a **disposable** snes9x-libretro/cpuexec.cpp. It observes only PLA, PLX, PLY, PLD, PLB, PLP when their pre-opcode S and actual M/X width imply stack reads touching 01DD or 01DE. Each QANMIPULL row contains original CPU frame, V-counter, opcode PC, P/A, SP movement and pre-opcode bytes. The same gated opcode observer now also records candidate RTI scopes as QANMIRTI with handler PC, post-RTI guest PC/bank (strictly checked against stacked return when available), pre/post A/P/S, PPU V-counter and CPU cycles. The pre-RTI stack image also captures up to four guarded bytes (status, PC low/high, PB) so the actual stack-derived return target can be reconstructed independently when the entire image is in range. An RTI alone is not classified as an NMI: original IRQ/BRK exits can use the same instruction.
- tools/qa01_original_nmi_stack_pull_report.py validates the existing actual five-NMI/01DD-PHA source witness **before** accepting any QANMIPULL candidate. It enforces original CPU-frame 5778..5782, finite event budget, chronological order, opcode width, stack-pointer delta, and exact target-byte coverage. A PLA candidate must also restore the observed target byte(s) into the corresponding low/high accumulator position, preserving B on 8-bit PLA. It rejects malformed lines and returns 0/45 release credit. A zero-pull capture is a **bounded negative**, never a claim that no consumers exist.
- tests/unit/test_qa01_original_nmi_stack_pull.py supplies synthetic positive, zero and adversarial cases for pull and RTI, plus read-only/one-opcode-dispatch patch checks. **Synthetic fixtures are not source-executed evidence.**

### Existing-route reproduction

Use the already authenticated **fresh calibrated paired original/native Switcher replay**, **not** the historical 2014 original-source 17030 movie-frame scan. In an isolated original Snes9x source tree, apply these patches in order:

1. instrument_snesref_qa01_switcher_stack.py --single-address 0x01DD --watch-nmi
2. qa01_original_nmi_pha_accumulator_patch.py
3. qa01_original_nmi_stack_pull_patch.py

Set UR_QA_STACK_FIRST=5778 and UR_QA_STACK_LAST=5782 on the fresh original CPU-frame clock and rebuild only that disposable original core. Reuse the original unmodified movie, ROM, calibrated entries, existing runner, and uninstrumented baseline. Retain the actual original log and paired switcher-report.json from that execution. Classify with:

    python3 tools/qa01_original_nmi_stack_pull_report.py --original-log ORIGINAL_LOG --paired-report PAIRED_REPORT --out PULL_REPORT.json

The parser additionally verifies the actual emulation/native CPU mode and corresponding 3-/4-byte RTI return, rejects A mutations and post-opcode PC not matching a fully available saved return image; a same-CPU-frame saved-A/RTI-A comparison is explicitly only a candidate correlation. The parser checks original source NMI/stack-writing evidence and existing original/native paired provenance; compare any positive pull with native I_NMI writer sequence at a common CPU/beam phase. **No execution is claimed by this PR.**

Architectural pull-class logging does not cover RTI/RTS/RTL, indirect/direct memory reads, or reads outside the short window. Even a positive stack pull proves only a candidate address read, not a score/progression effect. A zero count leaves those other mechanisms open. Do not change the strict comparator or shift original/native controller inputs.

## Next event acceptance

The source-backed matching-result candidates remain Switcher Race B, Zoom Zoo Circuit, and Bowl scored Stunt. For the first official USA pass, independently confirm source-authentic input, course entry, game mechanics, exact result timing, score/winner, post-result progression and next-event entry. Reuse existing fixtures and accepted artifact hashes. Neither matching text nor a one-frame observational offset alone establishes a release pass.

**Source-corrected RTI interpretation (2026-10-11):** The pinned Snes9x `third_party/src/snes9x-libretro/cpuops.cpp` `Op40Slow` restores P, PC and (in native mode) PB, and calls `CHECK_FOR_IRQ()` at the end. Crucially, the pinned `third_party/src/snes9x-libretro/cpuops.h` defines that macro as the **empty operation in both branches**. The earlier concern that this exact opcode may immediately chain an IRQ and thereby change post-opcode PC was not valid for this pinned core. When the four-byte stack image is in bounds, the parser now **requires** the restored address to match the post-RTI PC. Native-mode RTI consumes four stack bytes; emulation-mode RTI consumes three and retains prior PB. A missing in-bounds stack image prevents return-PC verification but does not prove a mismatch. A positive original RTI alone cannot identify NMI vs. IRQ/BRK ownership, match native CPU/beam phase, or certify a full event.

**Chronology limit:** The report also records whether a source-observed original NMI PHA preceded the RTI within the same CPU frame. Same-frame register equality alone does not prove these are the same interrupted call, particularly in the absence of a balanced stack-frame or distinct interrupt-chain ID. The baseline paired Switcher result still fails +4704/+4702 guest-relative parity and USA remains **0/45**.
