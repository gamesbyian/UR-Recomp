# RF051: genuine late source SPC700 input (F6/F7), research-only

RF050 (merged #1830) proves actual original USA Zoom Zoo late 11:C774 source LDA at source V159:H992, then true CPU-to-APU port3=D0 at source-SPC age 104485254, beam H1016, and true port2=63 at source-SPC age104485258 H1066. The late source SPC700 input/echo remains unobserved, and an earlier matching D0/63 native CPU pair at host6105 is **not** a justified corresponding transaction.

The RF051 observer in `tools/qa01_rf051_original_late_spc_receiver.py` modifies *only the disposable pinned Snes9x original SPC core*, after RF041's already executed/verified F6/F7 read path. It extends one existing conditional from old early sound windows to original local-SPC ages **104485200..104488000**, logging actual `mmio_read` value, SPC PC, CPU V/H and local SMP clock, with a bounded 8192-row overflow sentinel. It does **not** perform a second bus read, change SPC timing, input, ROM, CPU game code, native queue or shipping Windows.

Use precisely one source-qualified 2014 USA original/native Zoo replay with unchanged RF050, RF049, RF048 and prior source observers and original ROM/movie/inputs. All original/native controls (78 unmasked 128KiB WRAM comparisons, 51 exact, 92 differing occurrences, earned Zoo +5163, Bowl +267, 11 full SRAM pairs and cold ranked record) must remain identical to RF047. Compare the actual real source receiver against two independently witnessed source APU publications, preserving same-source-age ordering. Do **not** infer the native transaction or source/native absolute clock correspondence from matching byte values. If F6/F7 is not observed inside the narrow window, report capture missingness, not no SPC receive. Accepted full USA events remain **0/45**; RF042 failed equal-age retime remains rejected. Never modify RELEASE-QUALITY-LEDGER.json or any other lane.

## Independently qualified genuine RF051 original receiver (V1, 2026-10-18)

Exact one-shot [run 39122314804](https://github.com/gamesbyian/UR-Recomp/actions/runs/39122314804), source `a752f53627729dad2173e4613630d2a0af9ce7f7`, 18-file [case artifact 12134778810](https://github.com/gamesbyian/UR-Recomp/actions/runs/39122314804/artifacts/12134778810), ZIP SHA256 `5784ca13ab78c7545026659f22efc8270806b5a37c443e346858af056e44dfe5`. Actual original SPC instruction reads are captured once in the existing original source read handler: **322 ordered F6/F7 observations**, age104485209..104487998, no truncation. The single authoritative original `reference.log` places the following source-local witnesses in true execution order:

| Genuine source operation | Original source SPC age | V/H | Actual bus byte |
|---|---:|---|---|
| CPU writes port3 via RF050 `S9xAPUWritePort` | 104485254 | 159/1016 | D0 |
| CPU writes port2 via RF050 | 104485258 | 159/1066 | 63 |
| SPC700 genuine F6 read, SPC PC 1521 | **104485261** | 159/1184 | **63** |
| SPC700 genuine F7 read, SPC PC 1525 | **104485266** | 159/1288 | **D0** |
| SPC700 next genuine F6 read, SPC PC 1527 | **104485269** | 159/1340 | **63** |

Thus the *first post-publication original receiver reads* are +3 ticks (F6) and +8 ticks (F7) after the second original publication, with the next F6 at +11, all on the **same original source SPC age axis**. This closes original CPU→APU→SPC700 F6/F7 read observability for this transfer, but **not** SPC700's complete sound-reaction semantics, native corresponding transaction identity or original/native clock registration.

Independently unpacked and rehashed all 18 case files; complete original/native producer `zoo_race_mesh`, `zoo_next_bowl_handoff`, and `source_terminal_followthrough` JSON objects are *exactly equal* to frozen RF047 case SHA256 `1060a98744fb770bbe43fcdddd89b352bdef691e18f1ab24d4ead5f16996bf6b`. **78 whole unmasked WRAM checkpoints (51 exact, 92 differing-byte occurrences), genuine Zoo +5163/Bowl +267, full earned SRAM and cold ranked record are unchanged**. Disposition `strict_candidate`, release credit0; complete USA events **0/45**.

**Independent concurrent lane warning:** separate [draft #1831](https://github.com/gamesbyian/UR-Recomp/pull/1831) uses a different original gate and a native queue observer. Its genuine trial [39121609719](https://github.com/gamesbyian/UR-Recomp/actions/runs/39121609719), case ZIP SHA256 `bae6f1c8b9d91c70b7651d99ee088181f30c9b0925150c35f7315e0fe141d18e`, contains *zero* RF051 original rows and **16,000 RF051 native rows plus TRUNCATED**. That wide observer is **not** a source/native receiver-parity result. Avoid merging overlapping original instrumentation or silently treating its truncated native capture as successful. Any further native work must bound by actually qualified counterpart publication ordinal and use an explicit overflow fail-closed result.
