# RF059: actual original CPU opcode intervals authoring persistent Bowl→Switcher scene state

**October 18, 2026. Original/native USA gameplay-research only. Complete independently accepted USA events: 0/45.**

## Why this experiment is different from the earlier two

RF056 merged source-original/native Bowl case (2014-USA SHA, movie/seed SRAM/input pinned) independently proves the first 31 changed full-WRAM byte triples match exactly at source original +339→+340 and native +342→+343, followed by 642/642 exact next-frame byte triples. The 593 supplied P1 controller masks and durations are identical with native +1 host-frame supply offset, leaving an unexplained two-frame residual beyond input delivery.

RF057 independently proved **actual original CPU execution throughout the whole relevant handoff window**, ruling out five imported bank-80 menu/confirm candidate PC intervals, which were never executed in source CPU frames4686–4694. Source instruction samples are instead predominantly bank82/83 racing and sound code.

RF058 [true source run 39183201114](https://github.com/gamesbyian/UR-Recomp/actions/runs/39183201114), exact original/native source `ab392bcd8e2fc14d45c1550fec92e6737ea4691f`, artifact12157461467 ZIP SHA256 `2248cf04d75208a4b55da83fd18af11b57ddf37148b7ddf4b9446e39f880cd04`, recorded **358 real original executed-opcode interval WRAM mutations**. The apparent first-transition changes in direct page do not identify the scene trigger: `7E:0057` alternates via real source `82:D4EC STZ` and `80:8630 STA` in the NMI handshake; `7E:006F` decrements incrementally by source `82:8318 DEC`; `7E:0083` increments repeatedly by `82:82B5 STX` in audio upload; `7E:0000` is low-WRAM scratch overwritten 315 times. No global timing shift or input correction follows. **All 64 genuine full 128KiB/8KiB original/native/historical source-movie images from RF058 equal RF056 baseline byte-for-byte, unmasked.** RF058 also identified precisely two non-gameplay producer metadata differences, the intentional Snes9x instrumented-core hash and a new false Dragster diagnostic flag, with all actual ROM/movie/SRAM/input/handoff fields unchanged.

## What source CPU instructions to observe

The 31 true source +339→+340 whole-guest-WRAM mutations contain 17 more promising next-race persistent/scene setup fields, all tied directly to the immutable RF056 128-KiB source snapshots:

| Addresses in 7E WRAM | Observed original end-frame before→after |
| --- | --- |
| `121F`, `126B`, `1277` | `00→01`, `00→01`, `00→60` |
| `1359`, `135B`, `135D`, `135F` | `00→FF`, `00→7F`, `00→FF`, `00→7F` |
| `2000`, `2002`, `2004` | `01→02`, `01→04`, `80→40` |
| `2007`, `2008`, `2009` | `04→FF`, `90→7F`, `0F→02` |
| `2017`, `2018`, `2019`, `2069` | `02→08`, `03→07`, `02→01`, `0F→60` |

These addresses are **candidates**, not proven scene-transition predicates. The 31-byte result may mix scene setup, sound, timers and intermediate return-stack changes; two full guest snapshots alone never identify a single authoring instruction.

[Source-only disposable opcode observer](../tools/qa01_rf059_source_scene_transition_opcode_patch.py) transforms the *unique original Snes9x v1.63 65816 dispatch* in pinned `snes9xgit/snes9x@1bcc369e89f08243e0a462882fb1f3e42e51de3a` `cpuexec.cpp`. During **genuine original CPU frames4686–4694**, compare only these **17 unchanged raw guest WRAM bytes before and after the existing genuine opcode**; record changes with real source bank:PC, opcode byte, A/X/Y, V/H clock and old/new values, one source heartbeat per frame. Neither observer nor [fail-closed reporter](../tools/qa01_rf059_original_scene_writer_report.py) invokes guest `S9xGet/SetByte/Word`, changes ROM/WRAM/controller/CPU/APU, adds an instruction or source timing cycle. The [unit negatives](../tests/unit/test_qa01_rf059_original_scene_writer.py) refuse wrong source frame, opcode sequence, absent heartbeats, nonexistent watcher address, truncation and modified bytes. The report distinguishes **actual source-opcode-boundary mutation** from **a uniquely proved bus write or downstream transition branch**.

## Advisory source labels for interpreting real RF059 opcode rows

The already imported `reference/imported/reverse-engineering/baldosa-uniracers-recomp/decomp/ram.txt` independently labels `7E:121F` as **HDMA6 theme table index**, `7E:126B` as **CPU rival level**, `7E:1277` as **CPU rival base speed**, `7E:1359/135B` as **race sound parameters**, `7E:2000/2002/2004` as sound command queue/handshake indices and `7E:2069` as bottom-half INIDISP. These are useful *semantic hypotheses* but only raw exact-USA source opcode values and actual guest memory are admissible. The imported source-code symbol list identifies potential authentic setup routines `83:C8E0 Race_Main`, `82:D849 Race_InitState`, `82:D56A Race_InitHdma`, and `83:9987 Track_SetCurrent`. Their names are **not evidence that the original CPU executes them at the Bowl first transition**, and the initial RF059 probe does not restrict to any of their PCs. Qualify any eventual actual original source PC against the pinned USA ROM/code before attributing a scene transition or a native timing fault.

Source-compiled **writer/read discriminators** from the exact pinned Baldosa guest `gamesbyian/uniracers-recomp@10b864b9d14a7b7416dd909eb7b054c88faef101` sharpen this slightly: `src/gen/bank82_part0a_v2.c` contains an explicit `cpu_write8_paced(cpu, 0x7e, 0x2069, value)` in generated `Race_InitHdma` around guest `82:D61E` (more than one M/X variant); `src/gen/bank83_part0c_v2.c` separately contains a `2069` write in `Race_UpdateFinish` around `83:EA45`. Therefore `2069` is *not* an unambiguous one-writer marker until actual source PC/mode executes. The same pinned generated code contains only direct **reads** of `0x126B` around `83:E119/E147` in `Race_UpdateCpuRival` and a direct **read** of `0x1277` in `Uni_ClampSpeed` around `82:A7BE`; these do not reveal where their source values were written. An `82:DEFE` podium-mode `0x135B` explicit word write exists but no genuine original Bowl execution of that mode is inferred. The RF059 source observer deliberately does not preselect these function names; a real original bank:PC and old/new byte comes first.

## Qualification and next causal step

Run one temporary **original 2014-USA Bowl / independent fresh Snes9x / stock Baldosa native** case from exact research source with only read-only original core instrumentation. No shared workflow, permanent Actions or controller rephase. Retain full original/native 2014 source movie/full WRAM/SRAM, real guest earned score and cold ranked-record reload, all 593 exact supplied input events, raw memory comparison and full producer report. Rehash original source and new binary identity, **require all 64 full 128KiB/8KiB memory images identical to RF056's frozen case**, and verify only the explicitly qualified metadata and Snes9x core SHA provenance differ.

If the first true persistent writer is witnessed, inspect source opcode/control flags and consumer in the already executed bank82/83 (or newly observed bank) around that exact CPU time. Native follow-up is mode-qualified and separate from Zoo sound-branch owner #1845. Do not infer native guest PC or correct +2 input/clock on the basis of a merely similarly timed stored byte.

**Stop gate:** no USA event admitted without independent actual original/native complete-event QA and equal-relative-time controls. Work is CPU source-research only, not Modern, graphics, alternative event fixture or QA ledger.
