# QA06 independent regression baseline across four compiled Windows builds

**2026-10-19 | Exact original archive bytes, not release acceptance.** The companion [machine-readable four-build matrix](../analysis/evidence/qa06-four-win32-recovery-builds-exact-regression-matrix-20261019.json) preserves each independently measured source, portable inner ZIP, embedded AMD64 PE, original Actions wrapper artifact IDs and SHA256s, and original-archive QA witness counts. No ROM, native PE, or player save bytes are committed.

## Four builds, four identities, one bounded gameplay/storage invariant

| Original green Windows run | Actual GitHub synthetic PR-merge source | Actual ROM-free inner ZIP SHA256 prefix | Actual embedded PE SHA256 prefix |
| --- | --- | --- | --- |
| [39337845469](https://github.com/gamesbyian/UR-Recomp/actions/runs/39337845469) | `f7db1b92fbe347f1315cfe8de8ea3451857cb5fc` | `2b0ed905047a` | `d418b2e9bb81` |
| [39340984124](https://github.com/gamesbyian/UR-Recomp/actions/runs/39340984124) | `f639277f2c0410d85f773b77835c9a526dd2e65d` | `87c0e5221b20` | `5201916cee64` |
| [39342967638](https://github.com/gamesbyian/UR-Recomp/actions/runs/39342967638) | `6179a312c50d304116dfe3f16e32d0641c1ba24e` | `4b01a28f1f42` | `2488ad4f3f6f` |
| [39344781583](https://github.com/gamesbyian/UR-Recomp/actions/runs/39344781583) | `1952ba34c6bbfe522dc572be4340818f8ce2c960` | `45f51978ca97` | `d7a95a9d367c` |

The original Windows candidates have **four different sources, different actual inner ROM-free ZIPs, and four different actual AMD64 executables**. The GitHub parents for each *tested checkout* are pinned in the machine receipt; none is a subsequently integrated `main` build. Neither these sources nor the previous 2026-10-15 nominated owner package may be silently substituted for one another.

**Identical bounded source-storage result across all four:** on a genuine isolated hosted Windows NTFS W: VHDX, original-native guest save returns **8** on actual Win32 disk-full **112**; before durable intent, all 16 pre-intent original raw/typed/selector/catalog stage bytes preserve the old state. At the fault after native raw save and before typed metadata, exactly **74** SRAM byte positions change while old typed/selector/catalog remain intact. Recovery on a new actual original Windows CMD process advances typed generation **1 → 2** and matches the full 8,192-byte raw SRAM, while the next cold boot has no second reconciliation. Independent raw-byte FNV-1a32 agrees with original first-frame guest logs: **`63568e07` before** and **`255e468b` after**. Every build's 22 original postraw binary members was SHA/length checked against its original source report. These are genuine hosted source-process runs followed by independent *offline original byte review*, not four executions on a QA-controlled physical computer.

**Identical bounded saved player-journey result across all four:** the original hosted native-game 2P route uses frontend-created MIKE and MARTIN; MARTIN P2 wins **27.57** and MIKE P1 loses **27.61**. For each candidate, the archived pair files are byte-identical before and after fresh Windows Records viewing, both actual FNV-1a64 trailers verify, and both players' separate 8,192-byte raw SRAM equals its decoded typed `stock_sram`. The deterministic canonical run SHA256 **`d54ade82fdeb213db2c48bd7e4338c5bcae0f2af981fd70c27a467366acbc487`** and match SHA256 **`d16eb5d8ce868c8df6ef59169cd5b83ff5b1ed93235c4ad58624de30f8050749`** match in all four played-source archives. A single scored 2P guest outcome is *not* a complete independently accepted original Snes9x/native event; controller input was hosted semantic and SDL reported **zero actual joysticks** with dummy audio.

## Exact independent reproduction of the latest distinct build

The existing merged `tools/check_qa06_ntfs_original_archives.py` accepts **four external pins**, rather than trusting producer metadata inside either ZIP. Its actual original fourth-run successful replay:

```bash
python3 tools/check_qa06_ntfs_original_archives.py \
  --pre downloaded-actions-12231376913.zip \
  --post downloaded-actions-12230254428.zip \
  --expected-pre-sha256 d3265ac9e008bed02802a453e5b687874dec770e7d037a0cbc9154f7d69b0192 \
  --expected-post-sha256 2dc653e6a506b717127e392086a6835ad94242e0d9316b4704354772dac83b7d \
  --source-sha 1952ba34c6bbfe522dc572be4340818f8ce2c960 \
  --cmd-sha256 2f2a6cdbe9d4c37e331b82577ed3c947342e545a19bd0c022d0b940fa7cac8e0
```

Original fourth-run Actions package artifact ID **12231302106**, executable-binding artifact **12230549159**, pre-intent **12231376913**, postraw **12230254428**, scored 2P **12230589114**, pre-Records pair **12230244677**. All externally measured Actions outer SHA digests are in the JSON matrix. All four original package manifests and real embedded executable bytes were rehashed offline. The fourth source paired archive had 52 CRC-clean original members and nine actual saved state file members whose sizes/hashes were independently verified. Its two saved replay checksum trailers matched actual FNV-1a64 over each saved payload.

## How to use this baseline without conflating sources

Reproduce the same exact *source-qualified* checks on **one future integrated merged-main Windows ZIP**, record source SHA, original Actions artifact ID and outer SHA, inner playable ZIP SHA, PE SHA, and original saved before/after raw stage member hashes. If the complete before/post-raw stage and actual first-frame FNV change, investigate product/save semantics rather than adjusting these pinned historical source results. Replay the real created MIKE/MARTIN pair and independently compare canonical run/match bytes, fresh Records and distinct raw/typed profiles. The first unarchived *one-player earned `.urrun`* still needs original saved bytes in future CI evidence before independent 1P file certification.

**HOLD:** four hosted Windows source tests do **not** establish electrical power cut/true physically torn writes, an adversarial noncooperating same-profile writer, an end-user clean machine with real physical dual controllers, actual audio/UHD/7:6, or full Snes9x/native USA event fidelity. Original nominated 2026-10-15 ZIP stays unchanged; **QA02 in progress, 0/12 Windows gates, 0/45 complete USA events, zero witnesses promoted.** Primary original third-build audit is [QA06 third-source review](QA06-THIRD-WINDOWS-SOURCE-INDEPENDENT-REVIEW-20261019.md); original earlier deep NTFS audit is [QA06 first and second recovery source review](QA06-INDEPENDENT-ORIGINAL-WINDOWS-NTFS-PR1990-20261019.md).
