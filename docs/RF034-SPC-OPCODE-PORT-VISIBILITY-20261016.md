# RF-034: precise SPC opcode boundary at the CPU-to-SPC first $CC write

**October 16, 2026. CPU/APU research only. USA complete event acceptance: 0/45.**

## Why

RF030 qualified original/native CPU port first CC write, SPC IPL first compare/echo and original CPU echo poll. RF032 proved the actual native queued CC has exact stored target 103322545, applies exactly on that target (not late/rebased) and native CPU first reads echo four local SPC cycles after SPC emits it. RF033 established that, at original CPU beam V119 H312, Snes9x fractional CPU/SPC clock ratio 15664/328125 requested **two nominal SPC ticks**, while the read-only source SPC age advanced **five actual ticks** (103322541→103322546) before the CPU's CC becomes visible. The nominal/actual delta varies across nine original CC writes.

Pinned `apu/apu.cpp::S9xAPUExecute()` subtracts the nominal budget from `SNES::smp.clock`, then `SMP::enter()` invokes `op_step()` while `clock < 0`. An `op_step()` instruction can tick several opcode/data/idle bus cycles, so requested fractional cycles and actually executed SPC bus cycles need not coincide at a CPU port-write boundary. How much is prior clock debt versus current opcode completion remains unobserved. The original/new SPC clocks are independent, and numerical age proximity is **not** proof of phase synchronization.

## The read-only source witness

`tools/qa01_rf034_spc_opcode_boundary_observer.py` stages only after merged RF030/032/033 instrumentation in pinned disposable research guests. It does NOT modify any guest clock, SPC memory, queued write, port latch, ROM, SRAM, input, emulator opcode count or Windows/Modern code.

- Original Snes9x `apu/apu.cpp` captures `SNES::smp.clock` debt, `regs.pc`, `opcode_number` and `opcode_cycle` **before/after S9xAPUExecute()** at the real first CC CPU port write, retaining earlier RF033 nominal/actual clock logs.
- Native Baldosa `apu.c::apu_applyPortWrite` captures actual queue stored target, native SPC `portClock`, `spc->pc` and `cpuCyclesLeft` **before** the unchanged existing port-store call.

`tools/qa01_rf034_spc_opcode_boundary_report.py` refuses logs unless RF030, RF032 and RF033 strict executed source witnesses also qualify. It verifies true first CC writer age, queue-target/application cycle, counter and opcode plausibility, and refuses missing/truncated/tampered or reordered events. No synthetic cross-emulator clock alignment.

## One genuine source experiment, not an acceptance waiver

Use the existing original/native Zoo producer only, full RF015…028 research composite, full real archived USA ROM/movie/SRAM/controller inputs and actual next Bowl. Keep source original/fresh original/native Zoo +5163, source/fresh original/native next Bowl +267, 11 full 8192-byte SRAM pairs, 78 **unmasked** whole 128-KiB WRAM samples and thirteen adjacent sound pointer/transfer samples from +5034 through +5046. Independently rehash case ZIP, producer, original Snes9x core, native ELF and all 78 original and native memory hashes against RF033 [source-run 38977309694](https://github.com/gamesbyian/UR-Recomp/actions/runs/38977309694), ZIP SHA256 `f8ee6fbfbc9540179cea65428e298de3c59d4884f801d04a3ffc1c62663d87c8`. Stop on any drift or missing clock observation.

Temporary branch-only one-shot CI must be retired immediately after run starts. Shared QA campaign must return byte-for-byte to main before merging evidence. This remains CPU/APU source research; not Windows product implementation or an independent release-ledger entry. No third blind global cycle shift. RF029 read advancement and RF031 queue deferral are individually **rejected negatives** from actual source-qualified A/B. The next source-correct implementation candidate must be argued from observed opcode/debt boundaries and separately pass authentic 78-frame, 13-sound-frame, Bowl and earned SRAM comparisons.


## Verified hosted execution: first CC is published on opposite sides of opcode 78

[Actual source-pinned Zoo run 38981131474](https://github.com/gamesbyian/UR-Recomp/actions/runs/38981131474), immutable experiment head `299a200d2fc0252d06f858be81b8262145abafea`, passed original/native plan, exact compilation and true Zoo replay. Its 15-file [case artifact 12081626259](https://github.com/gamesbyian/UR-Recomp/actions/runs/38981131474/artifacts/12081626259) ZIP SHA256 **`6efac6d4d1cf4f5a2b47b4b04c76d2b878a7312bc88641c2ac5e9921cb342052`**, producer report **`605ee54d8cc8dc66a6bbe43e7e86102eae911821140af10a097f2dab76a4a4aa`**, original Snes9x core **`dd10bb54dd79cb8f23cf963e37b5161cdb42cafd3a4543950fcd279be6923c09`**, native ELF **`0b7a83998cdad88330c7e19f87e083f58fd558542635417cda422184941d5c41`**, strict RF034 report **`25a6aa3f450d0df10341ef451d79410adb189dc3a031324c7b079f31c587d97e`**. I independently downloaded it, extracted all actual CPU/SPC logs and matched every raw 128-KiB checkpoint against RF033 control ZIP `f8ee6fbfbc9540179cea65428e298de3c59d4884f801d04a3ffc1c62663d87c8`.

The first actual CPU `2140=CC` exposes a previously unmeasured **SPC opcode boundary**:

| Executed source state when first CC CPU write is handled | Original Snes9x | Native Baldosa |
| --- | --- | --- |
| Port visible at local SPC age | 103322546 | 103322545 |
| SPC PC **before** processing CPU port write | **FFCF** | **FFCF** |
| SPC PC at port-value publication | **FFD2** | **FFCF** |
| SPC opcode at publication | **78 (compare already executed)** | **Next opcode has not yet executed** |
| Clock/debt state at publication | SMP debt **1→4**; two nominal CPU→SPC ticks trigger **five** actual ticks | `cpuCyclesLeft = 0`, exactly at native opcode dispatch boundary |
| First later SPC read returning CC | 103322554 | 103322546 |
| SPC CC echo | 103322580 | 103322571 |
| Actual 65816 CPU sees CC echo | 103322584 | 103322575 |

Source-original before the write is **SMP clock debt 1**, SPC PC `FFCF`, previous opcode `D0`, and `opcode_cycle=0`. After `S9xAPUExecute()` returns it is **debt 4**, PC `FFD2`, executed opcode `78`, opcode_cycle 0; only then does `SNES::cpu.port_write` make CC visible. The original opcode `78 CC F4` is the IPL ready comparator: it ran with the **old** port value, looping once more before reading CC at age 103322554.

Native at actual queue target **103322545** has `apu->cpuCyclesLeft=0` and PC `FFCF`, with port queue head/tail 216658/216659; `apu_cycle` drains due queued port writes before dispatching the next `spc_runOpcode` at FFCF. Hence the native opcode begins with **the new CC** already visible, and its IPL comparator first reads CC at 103322546. The first nine original CC writers versus seven native writers in this ready-loop interval are consistent with that execution ordering. **This is an executed instruction-boundary visibility difference**, substantially stronger than comparing separate emulators' integer clock ages alone.

The observation does **not** establish a universal correction. RF029 globally advancing the SPC read and RF031 globally delaying queued writes each worsened the authentic original/native sound-window WRAM state. Snes9x's atomic-ish `op_step` execution and its carried SMP clock debt, versus Baldosa's split `spc_runOpcode`/`cpuCyclesLeft` accounting, require a source-faithful event-ordering model, not a blind one-cycle offset. Port traffic outside this IPL handshake could respond differently.

No newly introduced guest regression: all **78 original and 78 native full WRAM SHA256 hashes were exactly identical to RF033 independently built control guests**. Source/fresh original/native Zoo still reaches **+5163** and authentic next Bowl **+267**, all **11 complete earned SRAM images** match, **51/78 full original/native WRAM samples** remain byte-exact with **92 unmasked differing-byte occurrences**. Existing sound-pointer residual frames +5040/+5045, transfer counter $69 parity and post-result low-stack differences are unwaived. No sound-output or unsampled CPU instruction parity admission, Windows candidate correction, independent release ledger edit or USA event credit. **0/45.**

[Canonical SHA-verified machine evidence](../analysis/data/rf034-executed-spc-opcode-cc-visibility-20261016.json) preserves original/native pre/post opcode state and exact source identities. The temporary one-shot trigger and shared QA campaign extension were retired from the evidence PR while the immutable run continued. A separately judged, bounded **RF035-class** source-model proposal must preserve the whole 78-frame / 13-sound / 11-SRAM / Bowl acceptance set on genuine source input before a production correction can even be considered.
