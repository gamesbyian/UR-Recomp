# QA01: RF066→RF062 actual source/native memory change without causal attribution

**19 October 2026. Read-only cross-epoch, source-authentic observation.** The new native RF062 evidence is a **genuine executed ROM read** at decoded `82:82F0`, but it is not yet a clean instrumented ON/OFF replay. This independent QA01 lane answers a narrower question: *what actually changed in all original/native physical WRAM and SRAM images retained by two genuine 2014 USA Zoo producer epochs with identical source movie and controller inputs?* **Do not use this comparison to assign the change to RF062 probe overhead, retime either guest or grant a USA release pass.**

The two exact immutable case ZIPs are:
- [RF066 genuine Zoo run 39219862021](https://github.com/gamesbyian/UR-Recomp/actions/runs/39219862021), artifact `12171791431`, 411 members, SHA256 `494737bb6a1c422141c40f7175883f212767c3d774ee63fb0ba82add78cb445f`.
- [RF062 genuine native 82:82F0 run 39308179192](https://github.com/gamesbyian/UR-Recomp/actions/runs/39308179192), artifact `12214214743`, 407 members, SHA256 `b8287234d2fe515ee32b19b3d2a9b0e1bb58104b437de3a5cbe2e32e3af093ff`.

The **original and native replay-input *file bytes*** are identical between these two runs, not just their reported SHA. Both producers report the same retail ROM SHA `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`, original 2014 SMV and controller window, original SRAM seed, real original/native race entries **1017/1017**, result onset +5163 and Zoo→Bowl successor +267. But **both original Snes9x and native Baldosa executable SHA values differ across runs** (different source/instrumentation epochs). That is a mandatory confound: matching input does not give a same-binary-family probe-on/off test or prove the cause of state changes.

## Exact physical raw observation

Independent file-by-file recomputation from the two ZIPs found **388 identically named raw guest memory images** in each (97 checkpoints × original/native × 128KiB WRAM/8KiB SRAM). There are **no omitted bytes, no masks, no digest-only substitutions** in these retained images.

| Same guest across RF066 and RF062 | Identical images | Changed images | Cross-epoch differing byte occurrences |
|---|---:|---:|---:|
| Original full WRAM | 97/97 | 0 | 0 |
| Original full SRAM | 97/97 | 0 | 0 |
| Native full WRAM | 82/97 | **15/97** | **77** |
| Native full SRAM | 97/97 | 0 | 0 |

The native WRAM differences are confined to **15 exact checkpoints**: eight result/after-result stack-page snapshots (result-onset; result-stable; original-follow 08, 16, 24, 32, 64, 72) and **seven dense +5040 through +5046 sound direct-page pointer snapshots**. Of the 77 changed native WRAM byte occurrences, **63 are in result/after-result stack pages**, and **14 are the paired `7E:0063`/`7E:0069` DP bytes** (two bytes × seven frames). The 2014 original WRAM values at all 97 checkpoints did **not** change across these two source epochs, despite different compiled original guest binaries.

The original/native *within-run* unmasked mesh consequently moves from **51/78 byte-exact checkpoint pairs and 92 differing-byte occurrences** (RF066) to **46/78 byte-exact pairs and 104 differing-byte occurrences** (RF062). This difference is empirical and must **not** be "normalized" to obtain a cleaner native claim. Importantly, the separate three-frame full-raw RF062 case's byte-equal +5105..+5107 snapshots do not imply the earlier 78-checkpoint run was a full-course pass, because it was a **different experiment/source epoch**.

The code `tools/qa01_rf066_rf062_full_raw_crosswalk.py` independently pins both immutable GitHub case ZIP SHA256 values, checks all-member ZIP CRC and safe unique member names, reopens all 388 complete original/native physical memory files, compares each same-guest file byte-for-byte, and also recomputes original/native 78-checkpoint mesh totals *within* each run against its archived separate raw-audit and producer reports. It explicitly records changed checkpoint file identities, physical addresses and exact RF066/RF062 native values. No relevant source is available only as a "summary" or imagined byte. A small offline Actions workflow replays the comparison from the **same genuine archived ZIPs**, preserving a compact result and fail-closed adversarial tests. There is no emulator execution or recurring expensive factory.

```bash
python3 tools/qa01_rf066_rf062_full_raw_crosswalk.py \
  --rf066 /authentic/RF066-12171791431.zip \
  --rf062 /authentic/RF062-12214214743.zip \
  --output /new/original-native-rf066-rf062-all-raw.json
```

**Next actual QA discriminator:** for the native RF062 team, run a controlled **probe-on versus probe-off, same native binary family, same scripts, original movie and host dump sample positions** to distinguish an instrumentation observer effect from any preexisting RF018/native AOT timing change. The current cross-epoch difference, even together with one genuine native `82:82F0, 11:C774→D0` read and the RF071 original getter-entry proof, **does not** establish native sound PCM parity, first semantically matched original/native bus divergence, unmodified gameplay or earned Windows recovery. **0/45 original USA events accepted; 0/12 Windows release QA gates.**


## Independent real-archive qualification completed

[Archive-only workflow 39315164934](https://github.com/gamesbyian/UR-Recomp/actions/runs/39315164934) **passed** its adversarial tests and independent re-opening of all **388 full raw members per immutable ZIP**. Its retained verdict ZIP is artifact 12216974394, outer SHA256 3d450d53d0d3339beb81ee40291cb5f10e8032bdc08a574834a6dcca5c3d6fbd, and independently downloaded independent-crosswalk.json SHA256 5ceff5403c38133cc51fb595e8cb582eed72c8ca04b51e5d73af9e02afe58963. The [compact source/byte census receipt](../analysis/data/qa01-rf066-rf062-same-input-388-image-raw-crosswalk-20261019.json) retains the two source ZIP identities, actual 15 changed native WRAM file names and exact within-epoch 51/92 and 46/104 observations beyond the Actions artifact expiry period. The full independent JSON includes the **actual RF066/RF062 original/native values and addresses for all 77 changed native bytes**, not just these totals.

The 15 source-bounded native images distribute as eight result/followthrough stacks and seven late DP frames; their **77** changed-byte occurrences are **63 stack / 14 direct-page**. The observed RF062 82:82F0 → 11:C774 → D0 physical read remains a separate executed single-run proof and does not get promoted by this cross-epoch census. Unchanged 388-member input population and the byte-identical original guest are unusually useful controls, but **two different compiled original executables and two different compiled native executables still make direct probe causality non-identifiable**. Existing strict RF062 same-control reporter's failure and the source whole-race 46/78 count remain authoritative. Full USA event acceptance stays **0/45**, shipping Windows QA **0/12**.
