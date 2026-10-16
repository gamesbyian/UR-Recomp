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
