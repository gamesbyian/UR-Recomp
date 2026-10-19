# RF075: pinned native compiled RTI differs from interpreted architectural RTI

**October 19, 2026. Static original/native implementation archaeology only.** This is a condition-specific, pinned-upstream source assertion, *not* a gameplay correction or a newly executed guest experiment. USA course acceptance remains **0/45**, Windows release acceptance **0/12**.

## The exact implementation distinction

Source is pinned to RetroPortingToolKit/snesrecomp commit `075fbe4c8e0d97b0013be541795c39cb644a9709`, used by our authentic source/native Zoo campaigns. The new fail-closed `tools/qa01_rf075_native_rti_source_contract.py` independently authenticates *five complete pristine Git blob identities* before assessing the following control flow:

- **Generated compiled RTI**, `recompiler/v2/codegen.py::_emit_return(op.interrupt)`: increments S to the stacked P byte and really invokes `cpu_read8(00:S)` once, restores P and flag mirrors, then advances S by **two** for the saved PC and (in native mode) **one** for PB, **without loading PC or PB**. It returns `RECOMP_RETURN_NORMAL` to the host C control-flow owner. This is expressly documented in the upstream generated-ABI source.
- **Interpreted RTI**, `runner/src/snes/interp816.c`, opcode `0x40`: genuinely pulls P with `interp816_pullByte`, PC with `interp816_pullWord`, and PB with `interp816_pullByte`. It restores the architectural guest return target from the stack.
- **Interrupt entry**, `runner/src/cpu_state.h::cpu_push_interrupt_frame_at`: writes the *scheduler-provided* 24-bit PC's bank, high, low and P into the actual 65816 interrupt frame, with native/emulation width handling.
- **Frame driver**, `runner/src/beam_frame_driver.c::run_interrupt`: pushes that frame using `s_resume_pc`, runs the interrupt handler via the interpreter/compiled bridge, then republishes the host scheduler resume PC after the handler. It does not inspect the stacked saved-return bytes itself.
- **Native handoff and interpreter boundary**, `runner/src/snes/interp_bridge.c`: the compiled normal RTI reaches the host-C return path; the interpreted opcode RTI first changes its guest PC/bank, and then hits the host interrupt-handler boundary.

The source-pinned test asserts **all** of these mechanisms together. A missing or stale blob, missing genuine P load, missing PC/bank pop in the interpreter, changed original NMI push, changed scheduler order, or a falsely claimed host-return mechanism fails closed. The real pinned source build check uses source checkout, not a string search against a generated archive or guessed branch.

## Conditional fidelity risk, not an observed gameplay difference

If an NMI/IRQ handler **rewrites saved PC or PB**, the interpreted path can follow the modified architectural target while the current compiled RTI discards those bytes. Alternatively, if the host scheduler's saved resume PC differs from the actual interrupted instruction continuation, compiled return control flow can resume somewhere different. Both are **testable conditions**, not established facts about Uniracers. The RF073 archive shows nine genuine compiled NMI status reads and no RF047 helper reads of PC/PB inside those brackets; RF074 is actively testing where the scheduler's published PC actually came from. Neither proves a rewritten stack return or independently equivalent original/native intra-frame interruption point.

For the next source/native experiment, retain exactly one matched compiled original/native ZIP, immutable ROM/movie/converted input/native binary hashes, actual NMI push source bytes, the last NMI guest stack write and first read/overwrite, and **decoded executed opcode PC** rather than using scheduler ring assignments or stale interpreter cache as a substitute. A modified stacked saved-return target, if discovered, needs an end-to-end same-semantic-phase control-flow witness before any correction. Do **not** change native RTI to emit additional guest reads merely for probe coverage, rebase separate guest clocks, mask WRAM, assume a native skipped helper read means the bytes are unconsumed everywhere, or claim the original/native difference is automatically gameplay-visible.

## Validation

The narrowly triggered source contract workflow builds no executable, executes no ROM and adds no new guest memory operations. It checks the five upstream Git blobs, runs the adversarial unit tests, emits a machine-readable contract and archives that actual source verification. For a disposable checked-out pinned upstream source:

```bash
python3 -m unittest tests.unit.test_qa01_rf075_native_rti_source_contract -v
python3 tools/qa01_rf075_native_rti_source_contract.py \
  --root /path/to/pinned/snesrecomp \
  --out /path/to/rf075-static-return-contract.json
```

The result names `compiled_RTI_guest_status_load_count=1`, `compiled_RTI_guest_saved_PC_load_count=0`, `compiled_RTI_guest_saved_PB_load_count=0`, `interpreted_RTI_stacked_status_PC_PB_restored=true`. It **always** declares independent guest-fetched-PC proof, rewritten saved PC/PB observation, first consumed differing byte, full-race equivalence and USA admission **unproven**. This is a guide to the next decision-bearing native NMI test, not an extra acceptance gate.