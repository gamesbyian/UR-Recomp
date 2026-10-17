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

This draft intentionally has **no hosted replay results or production patch**. Its only current claims are source anchor tests and the already executed RF038/RF039 provenance.
