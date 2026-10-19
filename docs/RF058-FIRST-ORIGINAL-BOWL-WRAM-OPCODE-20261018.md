# RF058: original 65816 opcode-boundary mutation witness, USA Bowl → Switcher

**CPU/gameplay source investigation, 2026-10-18. Complete USA events 0/45.** Original source, native guest and full event QA remain independent. No clock, guest state, input, APU, SRAM, memory mask or Windows change.

## Previous genuine evidence and decision

Merged [RF056 #1864](https://github.com/gamesbyian/UR-Recomp/pull/1864) rehashed genuine 2014 USA Bowl original/source/native 78-member artifact12151982503, ZIP SHA256 `c2262b40e43b4e167cbdf291623b0e34207561187e103af39eca7a46fa4b0edc`. The **first 31 unmasked full-WRAM absolute-address, old-byte, new-byte triples** match exactly between fresh original +339→+340 and native +342→+343; the following **642/642** triples also match exactly original +340→+341 and native +343→+344. All 593 supplied original/native controller mask/duration events agree, native event delivery +1 guest host frame, true transition-onset displacement +3 guest frames; the residual +2 does not prove CPU input consumption, actual controller branch or a defect.

Merged [RF057 #1876](https://github.com/gamesbyian/UR-Recomp/pull/1876) established genuine original Snes9x opcode-dispatch heartbeats continuously across frames4678–4702. On source CPU frames4687–4693, first actual V0 PCs include `82:82F9`, `82:8332`, `82:8F95`, `82:A392`, `82:A999`, `82:A05D`, `82:90DA`. The imported bank80/00 postrace/joypad-function PC guesses have **0** actual executions in the qualified 4686–4694 window; previous zero-hit instrumentation failure is no longer a reason to keep those hypotheses alive. Two authenticated RF057 replay archives independently retain **64/64 byte-identical** raw source/original/native full WRAM/SRAM images and the original game result. No actual first writer or input-reading opcode was proved.

The unchanged RF056 2014 source archive's first 31-byte source transition includes the specific **existing full 131072-byte WRAM differences**:

| Full WRAM address | Actual fresh source original before → after |
| --- | --- |
| `7E:0000` | `20→02` |
| `7E:0057` | `E2→00` |
| `7E:006F` | `0F→00` |
| `7E:0083` | `86→94` |

The same four triplets occur native +342→+343. Stack/page `7E:01EC–01F5` changes concurrently, so NMI dispatch and returned instruction boundaries are also candidates. A *static only* xref in pinned Baldosa generated bank80 part00 finds an `$0057` explicit DP write in `NmiHandler_Default_M1X0` and `NmiHandler_Race_FastRom_M1X0`; neither has been witnessed executing at this handoff and both may write intermediate FF rather than the observed final 00. Do not confuse an imported xref with an actual writer.

## Single original source executable discrimination

[Disposable original Snes9x observer](../tools/qa01_rf058_source_opcode_wram_transition_patch.py) reuses the *exact single* pinned `cpuexec.cpp` opcode dispatcher from Snes9x revision `1bcc369e89f08243e0a462882fb1f3e42e51de3a`. Between **actual original CPU frames4686–4694**, every instruction reads exactly the four **raw emulated WRAM array bytes** above once immediately before, once after the one unchanged actual 65816 dispatch. It logs only bytes whose value changed during that actual instruction interval, with actual PC bank/address, real source opcode, A/X/Y, V/H before/after, post instruction PB:PC and the unchanged original core frame. At most 8192 change rows, with a separately validated truncation sentinel, and exactly one heartbeat at the start of each of nine frames. **No additional `S9xGetByte`, `S9xSetByte`, `S9xGetWord` or `S9xSetWord` calls occur**, no CPU bus side effects, no input or memory writes and no gameplay clock changes.

A changed raw WRAM byte *between* opcode boundaries is stronger than a static PC label, but it does **not** yet independently demonstrate that the observed instruction performed the unique physical SNES bus write: an event processor/NMI/HDMA callback may intervene during the instruction. Treat the first original opcode interval as the next *causal discriminator*, then register true direct bus writer only if needed. The [fail-closed executed-source reporter](../tools/qa01_rf058_original_cpu_wram_mutation_report.py) refuses missing actual frame heartbeats, wrong PC/byte addresses or ordinals, empty or truncated recordings, original ROM/movie/controller/SRAM/handoff drift and **any difference across all 64 genuine raw full memory images** against the immutable RF056 baseline. [Negative unit tests](../tests/unit/test_qa01_rf058_original_cpu_wram_mutation.py) require exact dispatch cardinality, no extra bus calls, correct source image identity and a genuine original opcode interval.

## One-shot execution and admission

Run exactly one disposable original source-core experiment using the already established Bowl historical source and QA-only original/native route. Build and verify the modified original core, enable `UR_QA01_RF058_ORIG_BOWL_WRAM=1` only for the real replay, retain full original/raw/native/historical images, original opcode and 2014 source trace, and verify complete byte equality to uninstrumented baseline. A mere successful replay/green job is insufficient: original byte-change log must independently prove actual executed source PC coverage and values, and a strict comparator must show unchanged original/native progression, result and earned SRAM. Remove the disposable experiment workflow immediately after scheduling; never edit the shared Bowl QA fixture. Continue to the exact **original bank82/83 physical WRAM writer and native consumed predicate** only from the recorded real opcode observations.

Three-project preflight: UR original full-memory/true-source opcode chain is authority; pinned Baldosa source can suggest bounded native consumer PCs; Malmazuke labels are advisory until original USA execution, never PAL timing or automatic event credit.
