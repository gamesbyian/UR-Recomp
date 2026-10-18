# RF040: actual CPU $2142 return and SPC port2 echo at Zoo frame6091

**Source-only executable next discriminator, not yet replayed. No timing correction and 0/45 complete USA events admitted.**

[Executed RF039 #1781](https://github.com/gamesbyian/UR-Recomp/pull/1781) captures true original and native SPC F6/F7 read PCs/values for the RF038 source-matched port2 `24` / port3 `02` transfer. Source original F6 reads old `23` at its own age103919450 *before* same-age CPU publication of `24`, then first reads `24` at age103919457; native applies `24` at its independently measured target103919434 *before* same-local-age F6 PC154F receives it. Native schedule happens at SPC age103919298, stored target103919434, not as a late queue consumer. Ordered receiver values and PCs closely agree with a 22–23 tick offset between separately maintained clocks, **not proof of one global phase discrepancy**. CPU writes span 530 original versus 374 native master clocks, with six versus three CPU polling instructions/read helpers.

The smallest missing causal datum is what the original CPU actually returned on each of its six `82:8301 CMP $2142` instructions compared with the three native reads, and when each genuine SPC output-port2 echo store became CPU-visible. The *new source observer* `tools/qa01_rf040_cpu_echo_transport_observer.py` stages after RF030/RF032 and existing RF034–039 observers into **disposable, pinned Snes9x and Baldosa checkouts**. It preserves the exact existing `S9xAPUReadPort` post-`S9xAPUExecute` return, `SMP::op_write F6` actual `mmio_write`, native `snes_read` post-SPC-sync/post-interceptor returned byte, and native SPC F6 `apu->outPorts[2]` store. No second bus read/write or cycle scheduling change occurs.

Original CPU gate: real source V116 H440..880, source SPC age103919410..103919510, port2 only. Original SPC output: source age103919410..103919550, F6 only. Native CPU gate: real host6091, native SPC age103919280..103919480, port2 only. Native SPC output: host6091, age103919280..103919550, F6 only. All emitted `QA01RF040...` rows are independently capped at 128 and have **explicit truncation sentinels**; absent, duplicated or truncated target witnesses must fail closed and cannot be called a timing fix. Native CPU records **raw and post-interceptor returned byte**, protecting against source-versus-filter confusion. CPU master clocks remain in RF038's untouched paced-read rows; source CPU beam and SPC ages are measured separately.

Stage only in the exact RF039 research composite (after RF030 and RF032):

```bash
python3 tools/qa01_rf040_cpu_echo_transport_observer.py original --root .tools/src/snes9x-libretro
python3 tools/qa01_rf040_cpu_echo_transport_observer.py native --root baldosa
```

Set `UR_QA01_RF040_ZOO_CPU_ECHO=1` for one genuine USA Zoo replay. Keep RF038 opcode/native paced and RF039 receiver recorders enabled. Replay the existing original ROM/SMV and identical exact controller script, with full 78 unmasked WRAM samples, 13 adjacent +5034..+5046 DP frames, original+native Zoo result +5163, actual next Bowl +267, eleven complete earned SRAM pairs, fresh guest cold record reload and source-vs-native strict comparator. Add no new permanent scheduled Actions workflow. Only a real crossed echo-return or write visibility first divergence authorizes a *narrow, source-qualified* A/B runtime edit. Reject RF029/031/036's already falsified global tick shifts, and do not grant Windows/release/USA event credit from a single bus handshake. Separately retain Zoo 01ED–01F1 last-writer/reader/NMI provenance as an unsolved required gate.

## Executed RF040: CPU-return/echo source evidence

[Real original/native Zoo one-shot 39066224227](https://github.com/gamesbyian/UR-Recomp/actions/runs/39066224227) passed plan/build/case/aggregate on immutable temporary source f28fa3168fae39fb160910fd647050b7fa62d0cf. Its 18-file [case artifact 12113836860](https://github.com/gamesbyian/UR-Recomp/actions/runs/39066224227/artifacts/12113836860), independently downloaded/rehashed ZIP SHA-256 c7fd279d985d189ddb86d9e52aa02b99696b750aeb0bcffae08c1ee3dbe80947, contains actual CPU and SPC source logs. Original Snes9x core SHA-256 bb7a6cb4f9c0bcde773d3a4aabb55f661c1af5a4f55f95da4d6516ab665fd1f7, native guest ELF SHA-256 69cfb9fae06ce3992124858fe919561537e3f3a76dc72f0e04d92b58bf3475b0. Original USA ROM, archived 2014 movie, 8-KiB seed SRAM and expanded original controller inputs are unchanged. Detailed [machine receipt](../analysis/data/rf040-executed-cpu-echo-20261017.json) pins all source identities and raw log positions.

**Original source executed CPU CMP $2142 returns** (all actual 82:8301 source opcodes, frame6091 V116):

| Source CPU H | Original SPC age | CPU return |
| ---: | ---: | ---: |
| 508 | 103919454 | 23 |
| 600 | 103919457 | 23 |
| 652 | 103919461 | 23 |
| 704 | 103919462 | 23 |
| 756 | 103919465 | 23 |
| 808 | 103919468 | 24 |

Original SPC output F6 echo 24 is genuinely published at local source SPC age **103919466**, PC1555, after fifth old-byte CPU read and before sixth new-byte CPU read. All six CPU return events directly pair with the real following 82:8301 executed-opcode records, H-post = read H+6.

**Native exact three AOT CPU paced-read returns**, each read8 bank80:2142 in Snd_UploadBlockList_82B4_M1X0:

| Native master at real paced read | Native SPC age at completed CPU return | Raw / returned |
| ---: | ---: | --- |
| 2176886940 | 103919439 | 23 / 23 |
| 2176886992 | 103919442 | 23 / 23 |
| 2176887044 | 103919444 | 24 / 24 |

Native SPC output-port2 F6 echo 24 is genuinely published at local native SPC age **103919443**, PC1555, after second old-byte return and before third new-byte return. The post-sync native CPU read interceptor leaves all three values unchanged. Seventeen-plus other native host6091 reads outside the actual three paced helpers are excluded through in-order correlation, not conflated with target polling. **530 original versus 374 native master clocks = +156** across the same original/native CPU port2 24 → port3 02 pair.

**Narrow explanatory mechanism:** RF039 proved the original SPC PC154F reads incoming old port2 23 at source age103919450 *before* the same-age source CPU publication of new 24; native applies 24 at its own stored queue target103919434 *before* the same-age PC154F F6 read. From the first actual incoming-new-24 receiver read to subsequent output echo24, **both executions take nine local SPC cycles**: source 103919457→103919466; native 103919434→103919443. Source-local CPU-port publication→output echo = 16 cycles versus native-local queue apply→output echo = 9. The independently maintained original and native absolute SPC ages are not equated, and their CPU/port observation boundaries are not identical. This establishes real differing local bus order and returned bytes, **not** an independently demonstrated globally correct seven-cycle delay or safe runtime fix. The source's unusual 40-master-clock first polling branch increment further prevents blind constant-loop cycle insertion.

**Controls:** RF040 versus independent RF039 original and native guest receipts have *exactly identical* recorded values for all **78 raw full 128-KiB unmasked WRAM sample pairs**, all 13 dense +5034..+5046 direct-page samples, sampled Zoo→Bowl progression and post-result followthrough. Exactly **51/78 original/native full-WRAM pairs equal**, with **92 unmasked differing byte-occurrences**, 90 on actual Zoo stack 01ED..01F1 and two on live sound pointer $63. Authentic Zoo result +5163, next Bowl active +267, 11/11 complete earned SRAM pairs, separate-process source-earned cold original/native ranked record (2510 centiseconds) remain unchanged. No Windows host disk-hardkill acceptance, all-frame instruction/state parity or shipping Windows complete event is thereby proven; research classifier is strict_candidate, complete USA admission **0/45**.

**Next decision:** observe source SMP opcode/debt before and after its real PC154F F6 read and original CPU publication at source age103919450, versus native stored-target/queue-apply/instruction cycle boundary at native age103919434. Distinguish CPU↔SMP atomic instruction advancement from AOT target calculation. Any correction requires independent untouched original/native A/B, all 78 unmasked WRAM/13 DP, authentic event/result/progression, full SRAM/cold and exact Windows compatibility, with 2P/attract negatives. Never guess a global phase shift, insert three artificial polls, waive stack differences or grant event acceptance. Separately trace Zoo 01ED..01F1 actual last-writers/next-readers and interrupt/NMI provenance.

Temporary one-shot workflow removed after launch and shared QA campaign restored byte-for-byte to main blob 5f5dda6b20aaa6bbde61f5420ef3bd6dd6977cdb. No production gameplay, Modern, graphics, independent QA ledger or release-package changes.

