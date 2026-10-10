# QA-01 original opcode source crosswalk: low WRAM stack-page candidates

**Observed evidence and scope (2026-10-10).** This note retains an already-executed original Snes9x opcode-scope observation and relates it to independently executed original/native Race/Stunt memory differences. **It does not claim an original/native complete-event pass, an instruction-semantic proof or a player-facing bug.** Primary release census remains **0/45** USA complete pairs.

## Three independent evidence classes, not one time-aligned trace

| Family / genuine event | Source | Observation | Limits |
| --- | --- | --- | --- |
| **Zoom Zoo Circuit**, original 2014 source | [executed original CPU scope, run 38011250306](../analysis/data/zoo-original-menu-host-order-20261009.json) | Original opcode scopes **`82:B1F2` and `82:B1F9` repeatedly change `7E:01F1`** during an observed frame. | Exact source PC scopes, but no opcode byte, original SP before/after, native corresponding PC or original Switcher attribution |
| **Switcher Race B**, original vs Baldosa | [same-host 5782 memory](QA01-SWITCHER-5782-RAW-MEMORY-EVIDENCE-20261010.md), independent run 38078429375 | **`7E:01F1`** is one of eight different WRAM bytes exactly one host frame before both guests report **MIKE 1:08.81** at host 5783; VRAM/CGRAM fully equal | No causal original instruction writer/read site at Switcher host 5782; still failed strict guest-relative acceptance |
| **Bowl scored Stunt**, original vs Baldosa | [eight genuine same-host tally samples](../analysis/data/bowl-original-native-observed-tally-wram-offsets-20261010.json), run 38025090532 | Six of eight Switcher offsets recur in Bowl's 57-address union; **`7E:01F1` and `01F2` are absent** from the eight sampled Bowl difference sets | Absence is limited to these eight noncontinuous samples; does not mean the bytes were unwritten or equal throughout the event |

The pinned imported original symbol catalogue [`decomp/symbols.txt`](../reference/imported/reverse-engineering/baldosa-uniracers-recomp/decomp/symbols.txt) labels **`82:B1D8 Res_LoadToVram`**, with `82:B1F2` and `82:B1F9` lying at offsets **+$1A** and **+$21** inside the named routine region, before the next label `82:B241 Res_RleRunToVram`. The catalogue describes `Res_LoadToVram` as a VRAM resource loader, with compressed resources going through `sub_81BB89`. This is **named source proximity, not a demonstrated dynamic call stack** for Switcher or proof that a resource loader is the original owner of its observed result discrepancy.

## Stack hypothesis, original implementation, and falsification

All eight actual Switcher differing offsets, `7E:01DD,01E6,01E7,01EF,01F0,01F1,01F2,01F3`, lie in the 65C816 conventional **`$0100..$01FF` stack page**. The pinned original Snes9x implementation in [`cpuops.cpp`](../third_party/src/snes9x-libretro/cpuops.cpp) has `PushB` write via `S9xSetByte(b, Registers.S.W--)` and `PushW` via `S9xSetWord(w, Registers.S.W - 1, ...)`, followed by a two-byte SP decrement. The pinned RAM label catalogue does **not** name the eight byte addresses, and its `sSavedDirectPage` SRAM mirror covers only `$0000..$019D`. That makes **transient stack residue a high-information hypothesis**, but regular RAM or interrupt-related code can also touch this page. Original CPU stack pointer and M/X/E mode still require measurement.

The already merged [opt-in Switcher original opcode diagnostic](../tools/instrument_snesref_qa01_switcher_stack.py) and [fail-closed report tool](../tools/report_qa01_switcher_stack_trace.py) now discriminate:
- Actual original opcode PC and opcode on changing the targeted bytes.
- SP before/after plus whether the address is **consistent** with a candidate 1-, 2- or 3-byte push (not automatic instruction attribution).
- Original 2014 event/input/ROM/SRAM and exact 128-KiB entry/horizon memory invariance after disposable emulator instrumentation.
- Whether `01F1` under original Switcher is touched by the same source PC neighborhood as original Zoo, and whether the higher-frequency Bowl overlap address `01DD` behaves as push-consistent memory.

Invoke the **existing manual** GitHub Actions workflow `qa01-switcher-original-2014.yml` using `source_horizon=22000` and `stack_writer_probe=true`. The probe starts from the **independently observed original archived source movie result frame** (previously 17030) and scans its bounded CPU window. The fresh original/native same-host **5782** pair is a **different replay timeline**; do not equate those clocks or call source-only opcode traces a native CPU scheduling verdict.

### Explicit outcomes

1. If SP/address/opcode are consistent with stack pushes, investigate whether any original result/progression consumer actually reads the differing byte *while live*, not merely its value retained at host 5782. A stale byte of no consumer significance must still be recorded, not silently removed from strict parity without a defensible acceptance comparator policy.
2. If a non-stack opcode writes the offset, identify its actual original instruction, caller and read consumers with the smallest frame-local experiment. A routine name from the imported symbols remains an attribution lead only.
3. If no target changes in the scoped source result window, record a bounded negative with the CPU-gate evidence; do not infer the address was never written. Expand the window once only if a specific result/progression hypothesis requires it.

Neither outcome waives original/native result-phase, next-event progression or candidate-bound Windows QA. **No source input shifting, guessed pass, synthetic award or release-ledger change.**

Related governing reference: [representative event adjudication](QA01-REPRESENTATIVE-EVENT-ADJUDICATION-20261010.md).
