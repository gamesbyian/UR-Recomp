# RF053: source/native genuine late SPC700 receiver sequence alignment

**Scope:** original/native USA Zoom Zoo audio/source research only. Not a shipping CPU/APU change and not independent QA-01 event admission. **Accepted complete USA events remain 0/45.**

## Recovered independent authentic witnesses

RF050 merged #1830 proves the original 82:82F0 `LDA [$63],Y` at physical source operand `11:C774`, followed within actual original 65816 82:82F2/82F6 instructions by genuine CPU port3 D0 / port2 63 publications at source SPC ages **104485254/104485258**. RF051 original merged #1832 independently proves actual source SPC F6 port2=63 at original local age104485261, F7 port3=D0 at104485266, then F6 port2=63 at104485269. Do not equate original `11:C774` with the older native `13:C774` first helper; their physical source addresses differ.

Two **complete authentic original/native 2014 USA** RF052 cases, source identities below, independently capture 1,959 real native SPC700 `spc-read` events and the exact same 322 original source SPC700 reads, both with no truncation. The original source segment has one and only one contiguous matching position in the captured native real SPC receiver stream when each executed instruction is identified by **(SPC program counter, F6/F7 port, returned byte)**, not by the transfer's two payload bytes alone.

| Genuine witness | RF052 V1 | RF052 V2 |
| --- | --- | --- |
| GitHub Actions run | [39127686106](https://github.com/gamesbyian/UR-Recomp/actions/runs/39127686106) | [39127883367](https://github.com/gamesbyian/UR-Recomp/actions/runs/39127883367) |
| Exact trial source commit | `1a3e5b54e41c7a042ee4316fcabefc681f216e64` | `f127074dce686b5caffbfbf68c5cff9c64cff606` |
| 18-file genuine case artifact | 12136344183 | 12137208430 |
| ZIP SHA256 | `f641cc39af5d63ac9d01c47cfd35ced5162d5c789d2be3444e47bfd50db92bbb` | `ec8cffa84d742656c77dea1e27e13fd8bacaf316c10ff15160235df5883f8e50` |
| Native entire window events | 4,571 | 4,571 |
| Native actual SPC read events | 1,959 | 1,959 |
| Original actual SPC read events | 322 | 322 |
| Exactly matching ordered SPC read PC+port+value triples | **322/322** | **322/322** |
| Unique matched zero-based index among 1,959 native reads | **828** | **828** |
| Original ages first/last | 104485209..104487998 | 104485209..104487998 |
| Matched native SPC portClocks first/last | 104485186..104487975 | 104485186..104487975 |
| Observed original age minus paired native clock | **23 ticks in 215 samples; 22 ticks in 107 samples** | Same |

The native debug cumulative per-kind counters differ across RF052 V1/V2 because their trace instrumentation differs, but the true 1,959 native read PC/port/value outcomes, the matched 322-event ordering, local clocks and all producer parity controls are unchanged. **These are two instrumented replay variants, not independent game inputs or a new accepted game event.**

## Genuine native scheduling and receiver chain in the matching window

In the V2 run the native APU's existing real queue callback records:

| Native operation (host frame6124) | Native local SPC portClock | Actual native value |
| --- | ---: | --- |
| Schedule port3 | 104485222, target104485230 | D0 |
| Schedule port2 | 104485222, target104485233 | 63 |
| Apply port3 | 104485230 | D0 |
| Apply port2 | 104485233 | 63 |
| Real SPC F6 read, PC1521 | 104485238 | 63 |
| Real SPC F7 read, PC1525 | 104485243 | D0 |
| Real SPC F6 read, PC1527 | 104485247 | 63 |

Original actual read PC/port/value sequence at source ages104485261/266/269 matches this recipient sequence *and 319 more consecutive real source SPC reads*. Native target queues are genuine native-local causal witnesses of delivery in the matched interval, not CPU writer instruction identities. The true original CPU port writes are observed at source ages104485254/258, while native scheduling of D0/63 occurs at native portClock104485222/222 and native apply at104485230/233. **Do not conflate these CPU scheduling events or claim a simple common fixed clock offset across the two systems.** The 22–23 tick interval pertains *only to the paired executed SPC read sequence*. Correct source/native CPU execution and port queue publication equivalence requires its own clock/ordinal registration.

## Audit and stop rules

`tools/qa01_rf053_real_spc_receiver_sequence_parity.py` independently reopens one or two unchanged genuine RF052 ZIP archives, verifies the RF050 original within-instruction publication order, RF051 actual executed original F6/F7 read count and exact source ages, uniquely aligns the full original SPC read sequence within the untruncated native real queue/read trace, preserves actual native cumulative read order and separate source/native clocks, and checks the whole original/native RF047 `zoo_race_mesh`, `zoo_next_bowl_handoff`, `source_terminal_followthrough`, ROM/movie/input/source-SRAM identity and zero release credit. The reporter refuses duplicate candidate alignment, dropped/malformed/spoofed rows, incomplete final native counts and changed strict whole-WRAM controls. The recorded sample histogram is derived from actual local SPC ages, never imposed by guessed retiming.

All original/native control objects for both trials are **byte-for-byte equal** to immutable RF047 ZIP SHA256 `1060a98744fb770bbe43fcdddd89b352bdef691e18f1ab24d4ead5f16996bf6b`: 78 unmasked whole 128KiB WRAM paired checkpoints, 51 exactly equal, 92 differing byte occurrences, real Zoo +5163 and following Bowl +267, 11 earned entire SRAM pairs and fresh cold ranked reload. The acceptance remains `strict_candidate` and 0/45 USA events.

**Remaining technical research:** independently align actual 65816 CPU-to-APU source/native publications around the already receiver-aligned 322-event segment, including 82F0 source operand `11:C774` vs the native AOT actual full memory operand, and identify any real sound correctness defect before considering a minimal source-supported production patch. Do not revive already rejected RF042 equal-age retime, mask existing WRAM differences, infer a universal 22/23 offset outside this precise SPC receiver window or call the 322 matching read sequence a complete verified 45-course event.
