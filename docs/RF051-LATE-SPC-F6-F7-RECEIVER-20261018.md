# RF051: late original SPC700 F6/F7 receiver versus native queue window

**Exclusive CPU/APU source research. No gameplay/CPU/APU code changes, unmasked WRAM adjustments or independent release acceptance. USA accepted complete events remain 0/45.**

## Known source first link (RF050)

[RF050](RF050-LATE-ORIGINAL-SOUND-PORT-PUBLICATION-20261018.md) directly proved one genuine original USA transaction: 82:82F0 LDA [$63],Y at 11:C774 original frame6124, V159:H992, A=630D→63D0. A real S9xAPUWritePort published port3=D0 at beam H1016, source SPC age104485254, before original 82:82F2 STA $2143 completed at H1022. The second real publication port2=63 at H1066, source SPC age104485258, preceded original 82:82F6 STA $2142 completion H1072. Exactly four *original-local SPC ticks* separated the publications. All 78 unmasked whole-WRAM checkpoints, 51 exact, 92 differing occurrences, Zoo +5163/Bowl +267, 11 full SRAM pairs and cold guest record preserved. Earlier D0/63 source/native writer ordinal42931–42932 is not the same original instruction transaction.

## One bounded real receiver experiment

`tools/qa01_rf051_late_spc_receiver_observer.py` stages strictly after RF041 into **disposable original/native research guests only**. Actual original Snes9x `apu/bapu/smp/core.cpp` logs an already-performed real SPC `mmio_read` from F6 or F7 at source-SPC-age 104485120–104485800. It retains original local age, CPU V/H, SPC PC, opcode/cycle, debt, port 2/3 and read value. No duplicate bus operation, SPC stepping, clock retime, ROM/movie/input edit.

Native Baldosa observer is strictly inside the existing `ur_qa01_rf037_port` callback, for real `schedule`, `apply`, `spc-read` on native host frames6110–6140 and native `portClock` 104300000–104900000. No new native scheduler/queue, CPU writer, SPC read, or timing change. Native frame and native portClock remain separately tagged; they are not equated to original frame6124 or original SPC age104485254.

`tools/qa01_rf051_late_spc_receiver_report.py` reads a genuine source/native 18-file Zoo case archive, fails on malformed ordinals, impossible clock/port values, receiver truncation or missing original CPU→APU sender, and reuses original RF049 full-operand census, native RF048 DP63+DP65 helper receipts, plus entire RF047 unchanged source-original/native `zoo_race_mesh`, `zoo_next_bowl_handoff` and `source_terminal_followthrough` controls. Original F6/F7 reads chronologically after late source publications are *source candidates*; they do not by themselves prove corresponding native reads, matching clocks, or final audio.

One source-pinned historical 2014 USA original/native Zoo replay suffices. Remove its temporary one-shot workflow immediately after enqueue and restore shared QA campaign byte-for-byte to main.

**Adjudication:** Report actual source F6/F7 value and source age after the proven D0/63 sender. An empty within-window read capture means only missing observation within those bounds, not global nonreceipt. Count native queue/receiver events on independent native axes; match original/native only with separately qualified publication ordinals and host/CPU clock witnesses. Keep RF042 rejected, no timing patch, no byte masks, no new complete USA event acceptance.
