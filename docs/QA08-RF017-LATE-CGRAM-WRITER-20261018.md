# QA08: read-only current RF017 late-result CGRAM CPU writer
18 October 2026. Experimental descendant of clean production #1780, DO NOT MERGE instrumentation.

The current native original PPU has demonstrated authentic CPU-tagged $2121/$2122
writes at host4028+7k through host4182, four 15-bit grayscale states and
a 28-guest-field phase. The apparent 112-field result discrepancy is a
sampled (16,28) alias. Separately pinned genuine original 2014 Snes9x
writer records include fields 5157,5164,5171,5178, but are not yet
source-joined to CURRENT RF017 Windows at those late fields.

This one exact Windows x64 experiment preserves pinned Baldosa/SNESRecomp,
actual RF015/RF017 regeneration and the two #1780 firstline/V0 corrections,
injecting only an opt-in read-only source port logger. It captures the
unchanged real 5484-guest two-pad input and authentic USA ROM, requires
the full historical b735b018... CRC transcript, and extracts bounded
per-writer native input frames, $6C..$6F CGRAM bytes, CPU tag, V/H and
pre-write latch. The source phase is measured, never guessed.

**Next decision:** Join the new exact current-native frame/values to
the original Snes9x archived true $2121/$2122 writer receipts. If the
original 2014 writer occurs two frame labels later at the same values,
handoff CPU/NMI clock cause to original gameplay owner, separate from
native PPU colour ingestion. A different palette value or writer cadence
requires tracing that first differing source event. Never shift output
frames, modify CPU/APU from graphics, fake blanked pixels, remap final
colours or rewrite medal OAM. There is no QA08/10, physical 4K or HD
racer visual signoff.

Source only and disposable. Preserve compact joined source evidence via
a separate evidence-only PR if exact run succeeds; discard this
instrumented branch without merging it into production.
