# RF042: rejected native equal-age SPC queue ordering A/B

**Executed source-pinned negative result, 2026-10-17. No production CPU/APU change. Complete original/native USA acceptance remains 0/45.**

## Premise and source identity

Merged [RF041 #1791](https://github.com/gamesbyian/UR-Recomp/pull/1791) proved that original Snes9x at Zoo V116 H442 executes the actual SPC F6 read of incoming old `23` at source local age103919450, SMP debt **0**, *before* CPU port2 publishes new `24` at that same source-local age. Pinned native RF026 SPC bus-cycle runtime applied the queued `24` *before* its same-native-local-age SPC F6 read at age103919434, `cpuCyclesLeft=0`. The original and native SPC clock epochs remain **independent**. Both genuine first-new24 receive→echo24 spans are nine local SPC ticks; RF040 confirmed actual CPU returns source six `23/23/23/23/23/24` versus native three `23/23/24`.

An opt-in *disposable native guest* RF042 variant delayed just an equal-target CPU→SPC queued write at RF026's **last opcode base cycle** until after its single actual `spc_runOpcode`, before its existing portClock increment. Earlier-due writes and ordinary mode (environment flag unset) remained unchanged. No ROM, controller inputs, original source game, persistent Windows/Modern/graphics source or independent release ledger were modified. This was an A/B *hypothesis*, never a correctness correction.

V1 [39071547245](https://github.com/gamesbyian/UR-Recomp/actions/runs/39071547245) failed during build staging, **before a genuine replay**, because the patch targeted pristine Baldosa `apu_cycle` instead of the already-staged RF026 final-cycle source. That harness negative is separate from the actual treatment.

V2 [39072151377](https://github.com/gamesbyian/UR-Recomp/actions/runs/39072151377) ran on frozen source `8be9337d2d8e2480933c18dd8d4d58ae7d68bb65` with genuine unmodified 2014 USA Zoo source movie and original/native controls. The original/native builds passed, and the complete producer exited **0**. Its strict case then failed on a distinct missing **native IPL diagnostic** (`QA01IPLNATIVE` had 0 rows, baseline 117), making the overall run red; the aggregate completed. Crucially, the producer still uploaded a full independent 14-file [case artifact 12115434806](https://github.com/gamesbyian/UR-Recomp/actions/runs/39072151377/artifacts/12115434806), whose ZIP SHA-256 is `1fc55834927fcb5e3fd6f1ec5ba47910f4ffe642c50db2332780228b3be0167b`. The immutable baseline is [RF041 case 12115251490](https://github.com/gamesbyian/UR-Recomp/actions/runs/39069703970/artifacts/12115251490), 18 files, ZIP SHA-256 `1c21481aff42ab3580f6292d94c3b0f255d71d8c548b688f2f4d00ae4190ebb0`. Both archives were independently downloaded, rehashed and their raw original/native logs and whole-state receipts examined. Full [machine-readable negative receipt](../analysis/data/rf042-rejected-equal-age-native-ab-20261017.json).

## Decision-bearing A/B results

| Strict evidence | RF041 control | RF042 V2 variant |
| --- | ---: | ---: |
| Raw paired full 128-KiB unmasked WRAM checkpoints | 78 | 78 |
| Completely equal original/native WRAM pairs | **51** | **46** |
| Total unmasked differing-byte occurrences | **92** | **106** |
| Native IPL events `QA01IPLNATIVE` | **117** | **0** |
| Actual target RF042 tie markers | Not applicable | **0** |
| Original source Zoo result onset | +5163 | +5163 |
| Next Bowl entry | +267 | +267 |

**All 78 original-source full-WRAM sample hashes and relative frame labels were byte-identical between runs.** Therefore native changes are real, not derived from retiming the independent original or moving the comparator. The native guest's full-WRAM hashes changed at exactly seven dense observation frames **+5040..+5046**, increasing sound DP residuals in live `$0063`, `$0064` and `$0069`, while previously clean samples gained new differences. Frame-by-frame totals: +5040 baseline1→trial2, +5041 0→2, +5042 0→3, +5043 0→3, +5044 0→2, +5045 1→2, +5046 0→2. These account for **14 additional unmasked byte-occurrences**. The complete 13-frame sound DP window and Zoo→Bowl handoff/terminal followthrough objects also differ from the RF041 control, though the named game-state progression timing remains aligned.

The native target CPU write scope at host6091 **changed away from `Snd_UploadBlockList_82B4_M1X0` to `Snd_UploadBlockList_82EF_M1X0`**; the exact expected source-equivalent `$2142=24` writer at master2176886834 was absent. The proposed `QA01RF042TIE` witness was never emitted. The variant's native F6 receiver PCs/port values around local age103919434 are not the original RF041 transfer, so a supposed “improved tie” would be an invalid attribution.

The original Zoo result still occurred at +5163, next Bowl entered at +267, 11 sampled next-Bowl full earned SRAM pairs matched, six post-result full SRAM pairs matched, and independent fresh guest source-earned ranked-record reload (2510 centiseconds) worked. These controls show **bounded non-regression**, not full source equivalence. The trial's extra sound DP deviations and missing IPL/target witnesses disqualify it regardless of those results.

## Conclusion and next owner action

**Reject this native equal-age after-opcode queue treatment. Do not retry with arbitrary SPC delays, change the comparator, hide the 90 real Zoo stack residuals or grant an event.** The native port-queue first-divergence problem remains open; the smallest source-qualified future question is the CPU→SPC scheduling/clock epoch anchor and instruction-atomic *visibility at the actual source-qualified transfer*, rather than treating one equal-age label as globally meaningful. Prior RF029, RF031 and RF036 global clock-shift proposals also remain rejected. Independently, resolve the actual writer, next reader and NMI/interrupt ancestry of Zoo stack `01ED–01F1`, plus two live sound-pointer residuals, before any complete USA event acceptance.

The experimental source patch and negative-report tests are retained in historical [closed draft #1795](https://github.com/gamesbyian/UR-Recomp/pull/1795) rather than merged into shipping source. This findings-only record is safe to merge. **Strict complete USA count: 0/45.**
