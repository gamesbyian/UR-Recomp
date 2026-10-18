# RF047 source-qualified Zoo NMI wait-loop return-PC convergence

**Static original-USA disassembly, cross-checked against actual RF045 and native RF047 executed NMI observations. No game runtime patch, time-shift, byte mask, or acceptance credit. 0/45.**

## Proven source instruction path

The repository already preserves Nitrodon's explicit USA disassembly at [`reference/imported/reverse-engineering/nitrodon/bank 82.txt`](../reference/imported/reverse-engineering/nitrodon/bank%2082.txt), around bank82 `D4E9..D4F5`:

```asm
82:D4E9  PHP
82:D4EA  SEP #$20
82:D4EC  STZ $57
82:D4EE  BIT $57
82:D4F0  BPL $D4EE
82:D4F2  STZ $59
82:D4F4  PLP
82:D4F5  RTS
```

The [original bank-80 disassembly](../reference/imported/reverse-engineering/nitrodon/bank%2080.txt) contains `80:85B3 A9 FF / 80:85B5 85 57` (load `#$FF`, store `$57`) in the first NMI program, and `80:862E A9 FF / 80:8630 85 57` in another NMI path. The handler stack return is `80:B0EA RTI` for the observed true source macro path.

Actual [RF045 Zoo execution](https://github.com/gamesbyian/UR-Recomp/actions/runs/39085484707) captured source NMI interrupted PCs `82:D4F0` for source-host 1017/1019/1021/1023 and `82:D4EE` for 1018/1020/1022/1024/1025, each with pushed/restored status byte `26` (N flag clear), PB `82` and matching actual `PullB/PullW/PullB`. Native [executed RF047 V1](https://github.com/gamesbyian/UR-Recomp/actions/runs/39095578733) records actual source-pinned `s_resume_pc=82:D4EE` in all nine native hosts and `01ED..01F0=26 EE D4 82` post-push, and native handler-return SP01F0. The [first V1 machine receipt](../analysis/data/rf047-first-native-nmi-phase-partial-20261018.json) retains the four same-host PC mismatches and 29 damaged native event records without repair or byte masking.

## Conditional semantic result, not a universal CPU clock equivalence

An original NMI that interrupted the `BPL` opcode at `D4F0` restores status `26`, N=0. Consequently `BPL` is taken to `D4EE`; the native host continuation begins at `D4EE` directly. Under the game-observed NMI protocol, the handler stores `FF` at `$57`; the resumed `BIT $57` sets N and the next `BPL` is not taken. Both then reach `D4F2 STZ $59`, `D4F4 PLP`, `D4F5 RTS`.

This **pinpoints an original extra taken `BPL` branch** for four observed source interruptions: a real difference in opcode/cycle history that may still lead to the same post-wait gameplay state. The NMI-flag value and time of its CPU-visible publication must be checked at the actual consumer if a downstream discrepancy challenges this path. Source `BIT` can change N and V flags, but the following `PLP` explicitly restores pre-wait processor flags. No extra user input, course movement or gameplay decision has been shown between these two continuation points.

Native compiled `RTI` intentionally reads the saved status, skips reading the saved PC and PB, and returns via host C, as specified in [Baldosa `codegen.py` `_emit_return`](https://github.com/baldosa/snesrecomp/blob/075fbe4c8e0d97b0013be541795c39cb644a9709/recompiler/v2/codegen.py#L2443-L2457). This differs from the three actual original Snes9x macro reads and would be unsafe for an interrupt routine that deliberately rewrites its saved PC. No such rewrite has been proved in this bounded window. Source RF047 compiled-return snapshots are **not** proof that native read a guest PC/PB from the stack.

**Remaining distinct uncertainties:** actual native interpreted-vs-compiled RTI callsite in the corrected hosted case, first source/native consumed state after the wait loop, and independent CPU/master/beam timing origins. Native V/H is a modeled beam which can lag its CPU master; original Snes9x V/H is not automatically comparable clock-by-clock. These must be independently adjudicated before proposing a correction or changing strict event admission. Full USA complete-event credit remains **0/45**. Separately source-consumed sound pointer `$63` at +5040/+5045 remains unresolved and is not part of this wait-loop result.

## Next acceptance-producing discriminator

Consume the corrected [RF047 one-shot run 39096831814](https://github.com/gamesbyian/UR-Recomp/actions/runs/39096831814), source `f47dda877272c4d1672ba75d8fe36c8efb6fc45b`. Its one-atomic-write native sequence and explicit interpreted/compiled RTI callback must be verified against the original RF045 immutable reference (78 unmasked whole-WRAM pairs, 13 dense sound samples, +5163 result, +267 Bowl and entire cold earned SRAM). If the compiled host continuation is source-equivalent at the first `BIT $57` and tail, submit the observed stack-residue sampling-contract difference for **independent** QA-01/07 review. If a consumed saved PC or post-wait guest state is actually wrong, implement only the smallest source-proven 65816 runtime correction and rerun strict original/native A/B. No invented exemptions or event credit from this conditional control-flow analysis.
