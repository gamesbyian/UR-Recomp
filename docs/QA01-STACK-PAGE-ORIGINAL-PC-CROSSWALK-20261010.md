# QA-01 original opcode source crosswalk: low WRAM stack-page candidates

**Observed evidence and scope (2026-10-10).** This note retains an already-executed original Snes9x opcode-scope observation and relates it to independently executed original/native Race/Stunt memory differences. **It does not claim an original/native complete-event pass, an instruction-semantic proof or a player-facing bug.** Primary release census remains **0/45** USA complete pairs.

## Executed native raw-writer replay: original and native NMI PHA stack mechanics match

An additional **zero-emulator-rebuild** artifact recovery has closed native instruction attribution beyond the earlier generated-function name. [Run 38095592659](https://github.com/gamesbyian/UR-Recomp/actions/runs/38095592659) (green) downloaded the **unchanged, SHA-256-attested** native WRAM writer log from actual paired original/native Switcher run 38090897908, source artifact **11684141556**, and extracted its exact 15-row context around the single native `I_NMI_M1X1`-scoped `7E:01DD` write. Compact recovered artifact **11685473365** (ZIP SHA-256 `a46985a3ec6ba6015df7d7c3749ee21680687ced3bad0e9818b15d43a2ed6936`) and full byte/register context are pinned in [the machine witness](../analysis/data/switcher-native-nmi-01dd-exact-pha-source-20261010.json).

| Native NMI-handler push in exact captured order | Native stack address | Actual written byte/word | Original native register evidence |
| --- | --- | --- | --- |
| `PHB` | `01E5` | `80` | DB=`80` |
| `PHD` | `01E3` | `0000` | D=`0000` |
| `PHX` | `01E1` | `1400` | X=`1400` |
| `PHY` | `01DF` | `87D8` | Y=`87D8` |
| **`PHA` 16-bit** | **`01DD`** | **`4004`** | **A=`4004`, M=0, S=`01DD` at write** |
| `PHA` 8-bit after `SEP` | `01DC` | `00` | M=1 |

This **exact ordered source-visible writer sequence** matches the **actual pinned native generated** `I_NMI_M1X1` prologue in `gamesbyian/uniracers-recomp@10b864b9`, `src/gen/bank00_part00_v2.c`, including `cpu_write16_paced(cpu, 0x00, cpu->S, cpu->A)` and the native `CPU_STACK_OP_PHA` marker. The native raw writer event is a true **16-bit accumulator push**, not just an ambiguous NMI handler scope: it writes the full 16-bit `A=4004` to exactly `01DD` at `S=01DD` with M=0; the written word does **not** equal native X, Y, or D. From the generated two SP decrements, the native PHA enters with **S=`01DE`**, writes at `01DD`, exits with **S=`01DC`**. The separately observed original Snes9x `PHA 00:858E` also enters/exits **`01DE→01DC`**.

**What has converged:** both guests execute the same **16-bit PHA** in original `I_NMI` (original bank `00:858E`, native source `80:858E`), with the **same effective stack address and SP decrement**. **What remains different:** original captured `7E:01DD` changes **`08→42`** at original `ICPU.Frame 5780`; native writes **`4004`** (low byte **04**) at native `snes_frame_counter 5781`. Those are **separate sampling clocks** and do not yet establish comparable pre-PHA accumulator state at the same NMI/beam instant. The stack mechanics appear faithful but accumulator value/phase and stack consumer liveness remain open, as does the strict real original/native result onset **+4704/+4702 FAIL**. No release credit, guest-input edit or parity relaxation.

## Executed original *fresh* result-window 01DD writer and NMI-entry discriminator

The prior original-only trace around the **archived source movie result 17030** found zero changed-byte opcode scopes for `7E:01DD`, but that was a different timeline from the paired **fresh stock Switcher result at host 5783**. The actual follow-up [original/native replay 38094600828](https://github.com/gamesbyian/UR-Recomp/actions/runs/38094600828) (green) used unchanged source movie, original Snes9x and pinned Baldosa. Its disposable original Snes9x CPU observer watched only `7E:01DD` over original **`ICPU.Frame` 5778–5782**, recording ordinary instruction changes **and separately NMI-entry stack prologues**. Full provenance, log/ZIP SHA-256 and captured source values are in [the immutable machine witness](../analysis/data/switcher-original-fresh-01dd-nmi-writer-20261010.json), artifact **11684893524**, ZIP SHA-256 `a95aba4c9118c80efb5ab1fcafbed996a1ee440e9280560bb076029479034e84`.

**Positive writer attribution:** exactly one changed byte in original fresh-window ordinary opcode scopes: **`00:858E` opcode `48` (`PHA`)**, at original `ICPU.Frame 5780`, scanline/V-counter **225**, SP **`01DE→01DC`**. It changes **`7E:01DD` `08→42`**. The two-byte SP decrement and target address are consistent with a 16-bit accumulator push; the original routine's caller and result-consumer liveness are still unproven.

**Explicit interrupt falsification:** the normal original opcode observer cannot see `S9xOpcode_NMI()`, which Snes9x runs **outside** `(*Opcodes[Op].S9xOpcode)()`. The extended observer separately captured **five actual original NMI entries**, frames **5778, 5779, 5780, 5781, 5782** at scanline **225**. All five decrement SP by **four bytes**. None of the five NMI push-address ranges reaches `7E:01DD`, and none changes its byte during NMI entry. Consequently, in **this bounded fresh-original event window**, original `01DD` changes via the observed **`PHA 00:858E`**, not the automatic NMI hardware entry. This does **not** say the address is unmodified in other windows or exclude original NMI *handler* instructions.

**New exact original routine attribution:** the pinned [original disassembly symbols](../reference/imported/reverse-engineering/baldosa-uniracers-recomp/decomp/symbols.txt) identify **`80:8588 I_NMI`** as the original native-mode NMI vector which saves CPU state and dispatches through `[$0053]`. The observed original `PHA` at **`00:858E`** is the corresponding FastROM-mirrored instruction **`80:858E`, exactly +6 bytes after `I_NMI` entry**. The native WLOG independently names **`I_NMI_M1X1`** as the 01DD writer *scope*. This is a meaningful **shared original function-owner crosswalk**, and makes NMI *handler code* the clear next investigation. It is distinct from **automatic NMI-entry stack pushes**, which were instrumented and found not to cover 01DD. Do **not** infer original/native execute the same PHA at the same instant: original `PHA` writes `42`, native scoped write attempt records `04`, and exact instruction-level provenance/phase remains unknown.

**Pinned native generated-code counterpart:** In `gamesbyian/uniracers-recomp@10b864b9`, [`src/gen/bank00_part00_v2.c`](https://github.com/gamesbyian/uniracers-recomp/blob/10b864b9d14a7b7416dd909eb7b054c88faef101/src/gen/bank00_part00_v2.c) defines `I_NMI_M1X1` with entry `cpu_trace_func_entry(cpu, 0x008588, ...)`, block `L_8588_M1X1`, and an actual **16-bit PHA** sequence: decrement SP, `cpu_write16_paced(cpu, 0x00, cpu->S, cpu->A)`, decrement SP again, and `cpu_trace_stack_op(..., CPU_STACK_OP_PHA, ..., -2)`. The game starts its native-mode handler with register saves, so this mirrors the original `00:858E` two-byte PHA instruction **semantics**, not merely a function-name coincidence. However the native `SNESRECOMP_WLOG_ADDR` evidence lacks opcode-local PC, so the single `01DD=04` write attempt **cannot yet be assigned uniquely** to that PHA statement rather than another word push within `I_NMI_M1X1`. Preserve the difference between static emitted code and witnessed dynamic write ownership.

**Native contrast, not yet proven causal mismatch:** a separately executed, genuine native WRAM logger observed **one** `7E:01DD` word-write attempt at native `snes_frame_counter 5781`, scope **`I_NMI_M1X1`**, logged SP `01DD`, byte `04`. A compiled **NMI handler scope is not equivalent to the original hardware NMI-entry push**, and source-original `ICPU.Frame 5780` and native pre-run frame 5781 are **not established as the same instruction boundary or clock**. The original/native authentic result text remains identical at absolute host 5783, but strict independently guest-entry-relative result onset is still **+4704/+4702 (FAIL)**; release stays **0/45**.

**Next smallest investigation:** the original `I_NMI` prologue's `00:858E` PHA versus the native generated `I_NMI_M1X1` inner writer and accumulator/stack register state, then NMI/PPU/host frame alignment and the stack-word pop/read consumer across fresh 5780–5782. Do not retime archived input, adjust gameplay, infer native instruction PC from an AOT function name, or waive parity on the strength of stale stack-page bytes.

## Executed native original-result-boundary discriminator: 32,333 write attempts

The follow-on original/native paired test has now **executed**, not merely been proposed. [Run 38090897908](https://github.com/gamesbyian/UR-Recomp/actions/runs/38090897908) (green, job 114326935017) used the pinned original Snes9x 2014 source, pinned Baldosa guest/framework and the actual fresh original/native Switcher Race B route. The sole native framework edit was a **disposable, read-only frame gate** around the pre-existing `SNESRECOMP_WLOG_ADDR` logger. Unaltered original movie/ROM/entry SRAM, original/native stock entries **1079/1081**, exact host **5782** WRAM differences **eight**, zero VRAM/CGRAM differences, genuine original/native **5783** terminal onset, identical rendered result text and an actual positive timed Race were re-observed; strict guest-relative terminal **+4704/+4702** remains failed. The [compact source-visible native witness](../analysis/data/switcher-native-stack-actual-writers-20261010.json) pins the full native writer histogram, original/native comparisons and artifact **11684141556** (ZIP SHA-256 `9b202ec36bfd60dc1cece9e0d2c9027275d669f8ab4100d349c69848f250eaf9`).

The frame-gated native logger observed **32,333 WRAM write attempts** on the eight target addresses across actual native `snes_frame_counter` values **5775–5788**. It records generated-function scopes, CPU S at memory-write time and individual written-byte samples. **A write attempt is not the original Snes9x opcode observer's changed-byte event**, and the earlier original-only source near movie frame **17030** is not the same host-clock range. Do not equate event counts or infer instruction-PC parity from native AOT function names or `IPC=000000`.

| WRAM offset | Native write attempts | High-information native writer scope |
| --- | ---: | --- |
| `7E:01DD` | **1** | **`I_NMI_M1X1` at native frame 5781**, logged S=`01DD` |
| `7E:01E6` | 11 | **`Text_FormatRaceTime_FastRom_M0X0` (7)**, including frame 5782 |
| `7E:01E7` | 146 | `Res_LoadToCgram_M1X0` (132) |
| `7E:01EF` | 5,390 | `Snd_SendQueuedCommand_M1X0` (4,830) |
| `7E:01F0` | 5,383 | `Snd_SendQueuedCommand_M1X0` (4,830) |
| `7E:01F1` | 8,378 | `Snd_SendQueuedCommand_M1X0` (4,830); `Res_LoadToVram_B1F2_M1X0` (2,774) |
| `7E:01F2` | 8,007 | `Snd_SendQueuedCommand_M1X0` (4,830); `Res_LoadToVram_B1F2_M1X0` (2,774) |
| `7E:01F3` | 5,017 | `Snd_SendQueuedCommand_M1X0` (3,327); `WaitVBlank_M1X0` (1,503) |

The native `01F1` sample records the *same actual return-byte values* `FB` and `F4`, from scopes `Res_LoadToVram_B1F5_M1X0` and `Res_LoadToVram_B1F2_M1X0` respectively, at logger-observed **S=`01F1`**. Original independent opcode PC scopes `82:B1F9/82:B1F2` actually pushed low return bytes `FB/F4` and moved **S=`01F2→01F0`**. This is a particularly strong original/native **stack-mechanism crosswalk**, though it cannot equate native AOT scope with exact PC, or equate an SP sampled during the low-byte store with an original pre/post-instruction SP.

The `01DD` original-only *different timeline* 20-CPU-frame probe found **no changed byte**, whereas this native fresh-result trace captured one NMI-scoped *write attempt*. That is the best new discriminator; it is **not** proof of a native-only write or an incorrect NMI. The minimum next original-only experiment should capture actual `01DD` original stack/PC around the *matched fresh host 5781* (both guests, no original controller retime) and ask whether the differing byte is live to the next result/progression reader. **No native scheduler/gameplay change, parity waiver or 45-course release credit is authorized.**

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
