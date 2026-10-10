# QA-01 original opcode source crosswalk: low WRAM stack-page candidates

**Observed evidence and scope (2026-10-10).** This note retains an already-executed original Snes9x opcode-scope observation and relates it to independently executed original/native Race/Stunt memory differences. **It does not claim an original/native complete-event pass, an instruction-semantic proof or a player-facing bug.** Primary release census remains **0/45** USA complete pairs.

## Executed original Switcher stack result: 13,709 actual opcode scopes

The source experiment has now **run**, not merely been designed. Original Snes9x [run 38088102870](https://github.com/gamesbyian/UR-Recomp/actions/runs/38088102870) independently qualified the real 2014 Switcher Race B result at **source movie host frame 17030**, then replayed the identical input through an instrumented disposable Snes9x core. The original/source event and exact 128-KiB source-entry/horizon WRAM equivalence validator passed before the initial reporter rejected more than 5,000 changes. The original raw log was preserved as artifact **11683670622** (ZIP SHA-256 `9f3f8020ea12f58b9094e0fbfe00d6161d9c6812dbf49837c91c7e5a57c29e95`). A corrected, exhaustive-count/96-sample maximum reporter passed three checks in merged #1232, then [run 38088688106](https://github.com/gamesbyian/UR-Recomp/actions/runs/38088688106) processed that **same hash-attested artifact without rerunning an emulator**. Compact recovered artifact **11684005205** is preserved in [machine-readable evidence](../analysis/data/switcher-original-jsr-stack-opcode-scopes-20261010.json).

All **13,709** observed original opcode-scoped changed bytes across **seven** monitored stack-page addresses are compatible with the recorded push-family opcode, the stack-pointer decrement and the written address. The eighth, **`7E:01DD`**, did not change in this 20-original-CPU-frame result window; its earlier or other-event owner is **not** classified. These are **exact original-only observations**, not an executed native instruction schedule or full 45-event admission.

| Target WRAM address | Original changed-byte opcode scopes | Push/SP/address compatible |
| --- | ---: | ---: |
| `7E:01DD` | 0 | n/a: unobserved |
| `7E:01E6` | 11 | 11 |
| `7E:01E7` | 141 | 141 |
| `7E:01EF` | 57 | 57 |
| `7E:01F0` | 44 | 44 |
| `7E:01F1` | **13,204** | **13,204** |
| `7E:01F2` | 188 | 188 |
| `7E:01F3` | 64 | 64 |

The decisive source-level subcase is **`7E:01F1`**. The original CPU performs opcode **`20` (`JSR`)** at `82:B1F2` (**6,469** observed changes) and `82:B1F9` (**6,470**). Both move original SP **`01F2→01F0`** and change `7E:01F1`. The pushed low return-address byte for a 3-byte `JSR` at `82:B1F2` is **`F4`** (`B1F4`), while at `82:B1F9` it is **`FB`** (`B1FB`). The actual archived original changes alternate exactly between those bytes, matching the instruction's stack-return semantics. These two source PCs account for **12,939 / 13,204**, about **98%**, of all observed `01F1` changes. Their presence in the independent original Zoo trace is no longer merely a source-neighborhood coincidence: these are repeatedly exercised original-game subroutine stack writes in two event families.

**What remains open:** The eight *cross-guest* Switcher bytes were measured at **independently calibrated absolute host 5782**, whereas this original-only writer trace is from the **archived movie** near result movie host **17030**. Do not equate host/CPU counters or declare those eight original/native byte differences entirely harmless. Need a native same-event PC/SP or instruction-boundary comparison and a result/progression read-consumer test where appropriate. The strict source-relative terminal mismatch and official USA **0/45** complete admissions are unchanged.

## Three independent evidence classes, not one time-aligned trace

| Family / genuine event | Source | Observation | Limits |
| --- | --- | --- | --- |
| **Zoom Zoo Circuit**, original 2014 source | [executed original CPU scope, run 38011250306](../analysis/data/zoo-original-menu-host-order-20261009.json) | Original opcode scopes **`82:B1F2` and `82:B1F9` repeatedly change `7E:01F1`** during an observed frame. | Exact source PC scopes, but no opcode byte, original SP before/after, native corresponding PC or original Switcher attribution |
| **Switcher Race B**, original vs Baldosa | [same-host 5782 memory](QA01-SWITCHER-5782-RAW-MEMORY-EVIDENCE-20261010.md), independent run 38078429375 | **`7E:01F1`** is one of eight different WRAM bytes exactly one host frame before both guests report **MIKE 1:08.81** at host 5783; VRAM/CGRAM fully equal | No causal original instruction writer/read site at Switcher host 5782; still failed strict guest-relative acceptance |
| **Bowl scored Stunt**, original vs Baldosa | [eight genuine same-host tally samples](../analysis/data/bowl-original-native-observed-tally-wram-offsets-20261010.json), run 38025090532 | Six of eight Switcher offsets recur in Bowl's 57-address union; **`7E:01F1` and `01F2` are absent** from the eight sampled Bowl difference sets | Absence is limited to these eight noncontinuous samples; does not mean the bytes were unwritten or equal throughout the event |

The pinned imported original symbol catalogue [`decomp/symbols.txt`](../reference/imported/reverse-engineering/baldosa-uniracers-recomp/decomp/symbols.txt) labels **`82:B1D8 Res_LoadToVram`**, with `82:B1F2` and `82:B1F9` lying at offsets **+$1A** and **+$21** inside the named routine region, before the next label `82:B241 Res_RleRunToVram`. The catalogue describes `Res_LoadToVram` as a VRAM resource loader, with compressed resources going through `sub_81BB89`. This is **named source proximity, not a demonstrated dynamic call stack** for Switcher or proof that a resource loader is the original owner of its observed result discrepancy.

### Executed original byte chronology (higher-confidence detail)

The original Snes9x CI job **114091531165** in [run 38011250306](https://github.com/gamesbyian/UR-Recomp/actions/runs/38011250306) logged these two ordered opcode-scope changes at **ICPU.Frame 6756, PPU V-counter 0** (unaltered original Zoom Zoo controller stream):

| Original CPU scope | Address | Previous byte | Next byte |
| --- | --- | --- | --- |
| `82:B1F2` | `7E:01F1` | `FB` | `F4` |
| `82:B1F9` | `7E:01F1` | `F4` | `FB` |

The original byte is **restored in the same observed CPU frame**. The [machine evidence record](../analysis/data/zoo-original-menu-host-order-20261009.json) now retains this reversible sequence. This is direct original opcode-scope evidence of a *transient* byte value; it does **not** establish that the instruction is a push or pop, prove the byte was never read between stores, identify its Switcher writer, or waive any guest-relative comparison. It is consistent with temporary working data in the named resource-loader neighborhood, but no causal claim about the latest Switcher result or progression follows.

## Stack hypothesis, original implementation, and falsification

All eight actual Switcher differing offsets, `7E:01DD,01E6,01E7,01EF,01F0,01F1,01F2,01F3`, lie in the 65C816 conventional **`$0100..$01FF` stack page**. The pinned original Snes9x implementation in [`cpuops.cpp`](../third_party/src/snes9x-libretro/cpuops.cpp) has `PushB` write via `S9xSetByte(b, Registers.S.W--)` and `PushW` via `S9xSetWord(w, Registers.S.W - 1, ...)`, followed by a two-byte SP decrement. The pinned RAM label catalogue does **not** name the eight byte addresses, and its `sSavedDirectPage` SRAM mirror covers only `$0000..$019D`. That makes **transient stack residue a high-information hypothesis**, but regular RAM or interrupt-related code can also touch this page. Original CPU stack pointer and M/X/E mode still require measurement.

The already executed [opt-in Switcher original opcode diagnostic](../tools/instrument_snesref_qa01_switcher_stack.py) and [fail-closed report tool](../tools/report_qa01_switcher_stack_trace.py) now discriminate:
- Actual original opcode PC and opcode on changing the targeted bytes.
- SP before/after plus whether the address is **consistent** with a candidate 1-, 2- or 3-byte push (not automatic instruction attribution).
- Original 2014 event/input/ROM/SRAM and exact 128-KiB entry/horizon memory invariance after disposable emulator instrumentation.
- Whether `01F1` under original Switcher is touched by the same source PC neighborhood as original Zoo, and whether the higher-frequency Bowl overlap address `01DD` behaves as push-consistent memory.

Invoke the **existing manual** GitHub Actions workflow `qa01-switcher-original-2014.yml` using `source_horizon=22000` and `stack_writer_probe=true`. The probe starts from the **independently observed original archived source movie result frame** (17030) and scans its bounded CPU window; the actual recovered original result is recorded above. The fresh original/native same-host **5782** pair is a **different replay timeline**; do not equate those clocks or call source-only opcode traces a native CPU scheduling verdict.

### Explicit outcomes

1. If SP/address/opcode are consistent with stack pushes, investigate whether any original result/progression consumer actually reads the differing byte *while live*, not merely its value retained at host 5782. A stale byte of no consumer significance must still be recorded, not silently removed from strict parity without a defensible acceptance comparator policy.
2. If a non-stack opcode writes the offset, identify its actual original instruction, caller and read consumers with the smallest frame-local experiment. A routine name from the imported symbols remains an attribution lead only.
3. If no target changes in the scoped source result window, record a bounded negative with the CPU-gate evidence; do not infer the address was never written. Expand the window once only if a specific result/progression hypothesis requires it.

Neither outcome waives original/native result-phase, next-event progression or candidate-bound Windows QA. **No source input shifting, guessed pass, synthetic award or release-ledger change.**

Related governing reference: [representative event adjudication](QA01-REPRESENTATIVE-EVENT-ADJUDICATION-20261010.md).
