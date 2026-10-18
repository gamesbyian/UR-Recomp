# RF054: authentic late native 65816 CPU sound writer / ROM operand provenance

**Status: one research-only source-pinned 2014 USA original/native Zoo candidate; zero production timing changes.** Never update the independent release ledger; complete USA events remain **0/45**.

## What is already established

RF050 [#1830](https://github.com/gamesbyian/UR-Recomp/pull/1830) proves the **actual original** 82:82F0 LDA from physical operand `11:C774` at original CPU frame6124 V159 H992, original accumulator 630D→63D0, original actual CPU APU publication port3=D0 at local original SPC age104485254 and port2=63 at104485258. RF051 [#1832](https://github.com/gamesbyian/UR-Recomp/pull/1832) proves original real SPC F6/F7/F6 reads 63/D0/63 at original source ages104485261/266/269. RF052 [#1834](https://github.com/gamesbyian/UR-Recomp/pull/1834) proves **native queue** schedules D0/63 at native `portClock=104485222`, applies at104485230/233, with genuine native SPC700 receiving 63/D0/63 at104485238/243/247. RF053 [#1837](https://github.com/gamesbyian/UR-Recomp/pull/1837) independently aligns the **entire 322/322 actual source/native SPC instruction reads**, requiring equal SPC PC, F6/F7 port and byte, once uniquely among 1,959 real native reads in each of two genuine 2014 USA Zoo replays. The 22–23 local-SPC-tick observed offset is restricted to that read sequence; there is *no proved universal original/native CPU clock phase* or matched original/native CPU writer instruction yet.

## A bounded, executable native discriminator

`tools/qa01_rf054_native_sound_writer_identity.py` stages **only in a disposable, pinned Baldosa native guest** after the existing RF037/RF041/RF052 sound observers and native writer-window infrastructure. It has three explicit, noninterchangeable probes, all bounded to native host6124:

1. Native `RtlApuWrite` post existing filter: observes the **actual CPU→APU publication invocation**, register address/value, live recompiled function scope, original compiled CPU A/Y/D/DB/PB and direct WRAM mirror pointer bytes. It neither calls the APU routine again nor alters scheduling.
2. Native `cpu_read8/16` helper entry on ROM banks10..13: observes an **actually invoked CPU memory-read helper**, its physical bank+address, AOT scope and CPU register state. It makes no additional bus request and does not itself establish that it supplied the immediately following APU value.
3. Native `RomPtr` on ROM banks10..13: observes a **ROM pointer mapping request**, not a proven dereference or emulated 65816 bus access. Generated AOT code may dereference the pointer later, or use it for unrelated work. Treat it as candidate address-mapping evidence only.

The recorder reports typed, separately counted `writer`, `rom-map` and `read8/read16` rows and explicit overflow sentinels. Use a single genuine compiled/runtime Zoo replay with *unchanged* USA ROM/movie/input/SRAM, RF050/051 original source observers and RF052 genuine native queue/receiver observer. The disposable research workflow must be deleted immediately after scheduling, and the reusable QA workflow restored byte-for-byte to main. The run must preserve 78 unmasked whole 128-KiB WRAM paired checkpoints (51 exact, 92 differing occurrences), genuine original/native Zoo +5163 and subsequent Bowl +267, 11 full earned SRAM pairs and cold guest ranked-record reload. If the new observer alters any of those controls, reject the experiment. Before assigning a source/native writer equivalence, independently tie the native writer to actual ROM operand *consumption*, not just `RomPtr` mapping or matching output bytes.

`tools/qa01_rf054_native_sound_writer_report.py` requires an authentic native D0/63 writer pair from real CPU publication callbacks, retains candidate prior helper/mapping addresses as separately labeled evidence, and chains to RF053's unique 322-instruction true original/native SPC receiver match plus unchanged full RF047 original/native controls. If the native pair is absent or multiple, fail closed and refine observation rather than invent a match.

## Three-project reuse gate

Baldosa's pinned native runtime and existing generated `Snd_UploadBlock` guest functions remain the authority for the native writer path. The original Snes9x USA source is the execution oracle. Malmazuke's separate reconstruction (including conditional address-mode coverage work) can inform a **bounded static access-mode validation only** if the existing Baldosa generated helper/map evidence cannot identify the operand; do not import an independent PAL timing model, invent a second emulator, or alter CPU/APU clocks.

**Next if qualified:** recover true compiled 65816 source guest PC / generated `LDA [$63],Y` effective operand and compare with physical original `11:C774` under independently registered publication ordinals. No RF042 equal-age retime (already rejected), no release admission from a local sound trace.
