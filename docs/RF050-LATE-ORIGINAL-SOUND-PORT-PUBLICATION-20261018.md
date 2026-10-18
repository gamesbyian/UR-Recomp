# RF050: late original source sound-port publication and transaction alias

**CPU/APU historical research only, not game/runtime shipping code. Complete USA original/native events remain 0/45.**

## Why RF049 does not yet identify a matching published transaction

[RF049 executed 42,582 source-original 82:82F0 LDA opcodes](RF049-ORIGINAL-SOUND-FULL-OPERAND-CENSUS-20261018.md), all bank-qualified, and verified that the genuine original `11:C774` LDA at original internal frame6124 V159:H992 executes true `82:82F2 STA $2143` at V159:H1022 (A=63D0) and `82:82F6 STA $2142` at V159:H1072 (A=D063). The RF037 original authoritative `S9xAPUWritePort` observation stopped at age104199985, **before the RF049 source instruction rows were logged**. Consequently the two late original CPU store instructions are real but their *actual downstream APU publication* is not independently captured there.

A value-based retroactive search of the frozen RF049 18-file ZIP, SHA256 `172511ef7d97d76d1c93191ccfd1cea53c5140d5393e9e6e248414aabe8578bd`, finds one earlier original real `port3=D0; port2=63` pair among its 45,645 RF037 `S9xAPUWritePort` rows, at zero-based writer ordinals42931/42932 and source local SPC ages **104162887/104162889**, V186:H1286/H1336. The full matching native writer prefix has **one** pair with the same values/ordinals at native host6105 master **2181986178/2181986228**, scope `Snd_UploadBlockList_82EF_M1X0`. Original prior source port writer lines 89233/89234 precede the later true RF049 `11:C774` LDA/store lines 92047–92049, and have different beam coordinates. They are **not proof of the same original instruction transaction**. Record: [immutable false-aliasing receipt](../analysis/data/rf050-identical-payload-not-same-source-transaction-20261018.json). Matching payloads do not register source and native clocks or original CPU frame versus native host.

## RF050 one-shot read-only discriminator

Stage `tools/qa01_rf050_original_late_port_publication.py` into a **disposable, pinned** original Snes9x `apu/apu.cpp` only **after** the RF037 source writer observer and the RF041 source synchronization observer, without editing their existing calls. At the genuine `S9xAPUWritePort` path **after its single existing `SNES::cpu.port_write` call**, record original source SPC age, source V/H and port/value for source age104200000–106500000 and source V159:H850..1200. Deliberately do **not** access cpuexec.cpp's private `ICPU.Frame` from apu.cpp; the V/H window may recur across multiple CPU frames. Use an explicit overflow marker. Never infer that merely finding an adjacent D0/63 pair proves that the preceding RF049 instruction supplied it: source frame attribution and publication-ordinal calibration require independent evidence.

Re-run exactly one authentic USA 2014 Zoo from frozen source, same unchanged RF049/RF048 original/native staging, ROM/movie/SRAM/controller input, and **78 unmasked whole WRAM** checkpoints, original+native genuine Zoo +5163, Bowl +267, complete earned SRAM pairs and cold ranked-record reload. `tools/qa01_rf050_late_port_publication_report.py` must analyze actual source APU events, fail on malformed/truncated capture, chain the complete RF049 original LDA/STA census and live RF048 native DP63/DP65 bank reads, and compare the exact RF047 whole source/native controls before reporting a proposed transaction link. An absent candidate is only **observer-window missingness**. Publish immutable source SHA/run/artifact/ZIP identities. Remove the one-shot workflow trigger immediately after dispatch, restore the shared QA campaign to main byte-for-byte.

**Stop:** no equal-age SPC scheduling patch (RF042 was a real negative), no CPU/APU runtime changes or masking, no invented original↔native time registration, no independent release QA/USA event admission from a single bus-port trace.

## Genuine RF050 source execution: late port publication proven, source/native equivalence still not

[RF050 original/native Zoo action 39112615924](https://github.com/gamesbyian/UR-Recomp/actions/runs/39112615924) executed its genuine original USA Snes9x and pinned Baldosa guest under immutable research SHA `0c7c17e8a1c0a345256b23667f71bf01af0d01c1`. Independently downloaded 18-file [case artifact 12131342408](https://github.com/gamesbyian/UR-Recomp/actions/runs/39112615924/artifacts/12131342408) ZIP SHA256 **`b6538eb1e1a9b51996690b4baa1303037f8b9f417eaaa5d2189cc6d33c2b4fbd`**, checked full original/native replay logs, case result, and compared *entire* `zoo_race_mesh`, `zoo_next_bowl_handoff`, and `source_terminal_followthrough` records against RF047's immutable 18-file case `1060a98744fb770bbe43fcdddd89b352bdef691e18f1ab24d4ead5f16996bf6b`. All are **exactly unchanged**: 78 original/native full 128KiB WRAM pairs unmasked, 51 exact, 92 differing byte occurrences; actual source+native Zoo result +5163, next Bowl +267, earned 11 full SRAM and fresh guest cold ranked record preserved. `strict_candidate`, no release credit, 0/45 USA complete.

**Actual source CPU instruction publication is now proved.** The original source emission is exactly ordered in the one `reference.log` stream, each actual APU `port_write` printed *inside* the executing 65816 store, with the RF049 opcode completion printed immediately after:

| Source reference.log zero-based line | Original observed operation | Beam, local source-SPC clock |
| ---: | --- | --- |
| 92067 | actual `82:82F0 LDA [$63],Y`, operand **11:C774**, A=630D→63D0, internal CPU frame6124 | V159:H992 |
| 92068 | **real S9xAPUWritePort port3=D0**, after the authoritative single port publication | V159:H1016; SPC age **104485254** |
| 92069 | actual `82:82F2 STA $2143` completes, A=63D0 | V159:H1022 |
| 92070 | **real S9xAPUWritePort port2=63**, after authoritative publication | V159:H1066; SPC age **104485258** |
| 92071 | actual `82:82F6 STA $2142` completes, A=D063 | V159:H1072 |

The RF050 source V159/H850..1200 actual writer emitted **38** untruncated records across source SPC ages104212297..104689974. Only **one** adjacent D0/63 real-source pair occurs in that window, at recorder sequence21/22. A real original first-to-second publication separation of **four source-local SPC ticks** is observed; this is *not* four native-local SPC ticks or an original-to-native clock offset. Crucially, each observed publication is between the proper original LDA/STA completion lines, so it is **the late original transaction**, not a guessed value match from another window.

The earlier RF037 original/native matching D0/63 pair at original ages104162887/889, native host6105 master2181986178/6228 remains real but a **different occurrence**; its first original publication is **322,367 source SPC ticks earlier** than the newly proven late source port3=D0. Do not equate them merely because port bytes agree. See exact independently checked [machine receipt](../analysis/data/rf050-executed-original-11c774-apu-publication-20261018.json).

**What is *not* proven:** the late original SPC700 receiver's actual F6/F7 input/effective echo and whether a corresponding later native AOT transaction exists at a correctly clock-registered host frame; never reuse native host6105 as the corresponding late write merely from identical D0/63 bytes. The 2014 source-original CPU→APU publication is now closed, but CPU/SPC source/native absolute clock registration and all-frame audio/event equivalence remain open. RF042's already failed equal-age queue retiming remains rejected, no gameplay patch justified, and accepted full original USA events remain **0/45**.

