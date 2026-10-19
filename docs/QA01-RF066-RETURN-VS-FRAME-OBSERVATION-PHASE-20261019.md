# QA01: a same-host-frame WRAM snapshot is not the actual stack-return value

**19 October 2026.** Independent read-only follow-up to merged RF066/RF068 and the genuine historic controller-supply qualifier #1943. This work neither changes original/native gameplay nor awards an event or a release gate. The source 2014 ZIP, guest-specific scripts, compiled source-provenance and actual original/native WRAM images are all mandatory. Existing RF069 original clean-getter and RF062 native sound-reader producer owners remain exclusive; **no new emulator run or factory is requested**.

## Falsify the tempting snapshot-to-consumer equivalence

A whole-WRAM original/native pair at a named **host frame** is an actual byte sample at *script-dump phase*. It is **not** an original 65816 instruction-time bus value. A returned byte from an actual original `PullB`/`PullW` macro, logged *after the genuine getter completes*, is real execution evidence, but a separate semantic observation phase. Even when the two observations use the **same** host frame label, the CPU can read and write stack memory within that frame. **The relative chronological order of post-return instrumentation and the source script-dump is not independently established.** The guest log combines separately buffered script/recorder output, so the physical ordering of its text lines cannot be used to prove which observation happened first.

The genuine RF066 original/native Zoom Zoo case [run 39219862021](https://github.com/gamesbyian/UR-Recomp/actions/runs/39219862021), artifact `12171791431`, exact ZIP SHA-256 `494737bb6a1c422141c40f7175883f212767c3d774ee63fb0ba82add78cb445f`, has everything needed to **test** that warning, without rerunning a guest:

- Actual source-original `reference.log` with 903 RF066 post-real-getter returned stack values, independently RF045/RF064 corroborated. It contains 903 RF063 eligible writes but **zero RF063 getset read-entry rows**. The source original getter observed value is real, but the earlier genuine getset-entry bus sample is absent from **this RF066 compilation epoch** because of RF069's subsequently discovered stale getter object.
- Actual full unmasked original/native `scene-00001`, `scene-00002`, and `scene-00004` 128-KiB WRAM images, and independently parseable success ACKs in each guest log. All four stack addresses `7E:01ED` through `7E:01F0` have unequal original/native dump-phase bytes at each of those three sampled frames.
- The independently reopened source 2014 SMV and both real guest supplied controller files, already qualified by merged #1943. Both guest race-entry hosts happen to be 1017 in this **exact** RF066 epoch; that coincidence establishes no CPU/SPC instruction-time alignment.

The new offline `tools/qa01_rf066_same_host_stack_return_raw.py` first performs the existing `qa01_rf066_source_controller_archive.verify` full archive+movie+input audit, then independently rechecks the original RF066 903-return sequence and all source/local ordinals through `qa01_rf066_original_consumed_report.examine`. It requires *actual successful guest dump ACKs* at both independent host frames, reopens the whole original/native 128-KiB WRAM images **with zero masked bytes**, and for each true post-getter return examines its little-endian byte positions *only if* that physical address differs in the **separately sampled** same-host raw pair.

## Genuine early-race observation

| Race-relative frame | Genuine original returns touching one of the four differing stack addresses | Original-returned byte observations | Return byte equals original **script-dump** value only | Equals native **script-dump** value only | Equals neither script-dump value |
|---|---:|---:|---:|---:|---:|
| +1 | 74 | 104 | 3 | 6 | 95 |
| +2 | 91 | 119 | 3 | 5 | 111 |
| +4 | 97 | 128 | 3 | 5 | 120 |
| **Total** | **262** | **351** | **9** | **16** | **326** |

A `PullW` has **one returned operation** but up to two separately compared byte positions; do not conflate 262 operations with 351 bytes. The 326 neither-matching returned bytes are a genuine empirical demonstration that an independently rehashed same-host original/native memory pair cannot stand in for a genuine original post-getter returned value at an independently unordered source observation phase. The 16 cases matching the native same-host **script-dump** value are **not** native consumer evidence: they are still **original** source CPU macro-return bytes, and they match a different guest's **separately sampled script-dump** value only coincidentally. In particular, do not use them to claim that a native read matched the original stack.

The observed source original returns cover only host frames 1017..1025, or source-relative +0..+8; no RF066 post-return row is present in the late +5034..+5038 stack snapshot window. Source/current RF069 and native RF062 executed-PC and *same semantic phase* writer→reader witnesses are still required to identify the first genuinely consumed divergence. Neither an early real return nor an identical same-host script-dump sample licenses a stack-difference waiver. This exact sample demonstrates why cross-recorder instruction order and 2014 vs fresh-game host clock alignment must not be manufactured.

## Reproduce and scope

```bash
python3 tools/qa01_rf066_same_host_stack_return_raw.py \
  --archive /immutable/actions-rf066-case-12171791431.zip \
  --movie reference/imported/tas-bots/dessyreqt-4250-submission.smv \
  --metadata analysis/generated/historical-2014-smv-metadata.json \
  --output /fresh/rf066-original-return-vs-same-host-dump.json
```

The new `.github/workflows/qa01-rf066-same-host-return-raw.yml` independently downloads *that exact immutable source ZIP*, runs this verifier, confirms the counts for all three physical pairs and retains only a compact JSON receipt. Its ROM-free adversarial unit tests reject missing/short/changed WRAM, source-return scope forgery and absent actual byte overlaps; unit tests do **not** pretend to be a new original execution. The strict source provenance and QA01 preflight remain **HOLD**; **0/45 accepted USA events and 0/12 release gates**.


## Independent archived pilot qualification

[Real archival qualification 39310639780](https://github.com/gamesbyian/UR-Recomp/actions/runs/39310639780) **PASSED** with the immutable original 411-member case ZIP, real original/native log ACKs, all six complete raw WRAM members and genuine RF066 source event data. Independently downloaded the single-member verdict ZIP, artifact `12216140316`, ZIP SHA-256 `d80418e7efaa1d24c4932331bced0a7578e07dc638b281e75af4cffc71610817`; rehashed and checked `temporal-review.json` SHA-256 `0877a43947afc1144fbc73cae77384f965b8b48dd44f829b449536e461fb9ae8`. The compact immutable findings are also retained in [the review ledger](../analysis/data/qa01-rf066-same-host-original-return-raw-temporal-discriminator-20261019.json) so the proof's essential numerical facts survive temporary Actions artifact expiration. The ledger is a **summary** of that real original ZIP-backed verifier, not fabricated independent original CPU read-entry samples.

The first workflow run's negative-fixture assertion expected the wrong **error wording** for an already correctly rejected fake original macro-return population. It failed before checking the real archive. The corrected test now expects the actual fail-closed source error and the real-data workflow passes. No game code, input file, source identity, original/native host clock or memory criterion changed as part of that correction. Actual general project unit tests remain a separate check; no event admission follows from the success of this bounded forensic pipeline.

**Chronology qualification (same source archive):** A further independent inspection of the actual Snes9x log found the script's `scene-00001/00002/00004` acknowledgment lines physically printed before the RF066 recorder-return lines that carry the same 1018/1019/1021 host-frame labels. This reflects combined buffered/logging streams, **not a proven dump-before-return instruction order**. Therefore this machine receipt uses **same-host *different-phase*** terminology throughout. The earlier pre-correction compact Actions verdict used the adjective *later* without this ordering proof; its raw byte counts and source SHA remain valid, but its chronology language is superseded. A new exact-head artifact must be preferred when attributing temporal order. **0/45 USA events; 0/12 release QA gates.**


## Independent corroboration using RF069's *actual* original getter-entry bus values

A **different source execution**, the genuinely rebuilt clean-getter RF069 Zoom Zoo [run 39307624432](https://github.com/gamesbyian/UR-Recomp/actions/runs/39307624432), has now independently qualified 903 source-original `QA01RF063ORIGBUS kind=rb/rw phase=getset_entry` **read-entry** events, not just post-return values. The [RF071 source-read/return verifier PR #1948](https://github.com/gamesbyian/UR-Recomp/pull/1948) separately owns the authenticated 903/903 physical read-entry→post-return join and observed 12 source getters crossing video scanlines. Do not conflate this producer with the older RF066 archive above: the genuine clean RF069 case ZIP is artifact `12215281695`, SHA-256 `90b03d7e035c7a1939b488211b98165615e3fc63226fe57ac718fc7e3e772763`, 412 retained members and a different original Snes9x executable.

I independently downloaded and rehashed that **genuine RF069 ZIP**, parsed **903 actual RF063 original getter-entry read rows** from `reference.log`, and reopened original/native complete unmasked `scene-00001/00002/00004.wram.bin` pairs from the **RF069** ZIP. Comparing the real physical getter-entry sampled little-endian byte values against their same-host, different-phase script-dump WRAM at the four genuinely differing addresses `7E:01ED..01F0` gives the **same independently observed 74/91/97 getter read operations**, **104/119/128 byte observations**, and **95/111/120 neither-matching byte observations** as the older RF066 true-return comparison. Totals again are **262 getter read operations, 351 sampled bytes, 326 neither script-dump, 9 original-dump only, 16 native-dump only**.

This strengthens the **original-side** temporal counterexample: even an *actual compiled and executed source getset read-entry byte* is not generally reproducible from a separately sampled original/native full WRAM image bearing the same host-frame label. **Neither source phase is qualified as chronologically before or after the script dump**, and this addendum is an independent offline numerical reinspection, **not** a second automated RF069 archive verifier or an award of native read matching. RF071 owns original bus-return join qualification; RF062 owns actual native read PC/value/operand; QA01 factory acceptance still needs a single **source/native source-qualified equivalent semantic phase**. No masking, matching clock retime, player-release proof or USA course acceptance follows. **0/45 events, 0/12 QA gates.**
