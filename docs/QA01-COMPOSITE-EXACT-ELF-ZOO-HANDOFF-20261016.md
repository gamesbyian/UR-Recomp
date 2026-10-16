# QA-01: Exact composite ELF, authentic Zoo complete-return and sound-state adjudication

**Executed and independently verified October 16, 2026.** The original/native [three-event exploratory campaign](QA01-EXPLORATORY-SPC-THREE-EVENT-REVIEW-20261016.md) left the source-authentic Zoo **+267 next-Bowl continuation** and **+5040 sound-transfer residual** unobserved. Independent QA reused its **exact same already-built native ELF** with the newer main producer's bounded original/native full-Zoo observers. The genuine [one-shot run 38884542449](https://github.com/gamesbyian/UR-Recomp/actions/runs/38884542449) has a preserved [case artifact 12039022609](https://github.com/gamesbyian/UR-Recomp/actions/runs/38884542449/artifacts/12039022609), SHA-256 `21c28cd711519e150ce10e2753dc2d29b6e3eac1004b03d34683c3e03613c718`. Complete structured original input, executable, reporter and all 78 sampled WRAM first-difference counts are in the [machine-readable source receipt](../analysis/data/qa01-composite-exact-elf-zoo-handoff-20261016.json). This is bounded research, **not 1/45 accepted events**.

## Fixed executable identity, not a recreated patch stack

The source-qualified [original three-event run 38879846733](https://github.com/gamesbyian/UR-Recomp/actions/runs/38879846733) retained separate reference/native binary artifact `12037226466`, ZIP SHA-256 `47bdcf16d3ede604be55ff7b0fbb634628516050e27cb11dcd085f1bf06305f6`. Independent QA downloaded and SHA-256 verified:

- Native research ELF: `9a3bd17afd8377a4c83e76c05cd57dfdae2488e498aa4bea1b90a2baa018bb48`
- Original Snes9x reference core: `ec4ce30d80e0b2c22b5d700aec01d601bd85db452ccb8e2b32fa75e9fe63554a`
- `snesref` executable: `5fb3cca1f51d13762e7b82e736133cdab702aafbca07b9164d568139a3bcc18a`

The current main QA producer and classifier ran the old compiled guest without altering its CPU/APU code. The observer checkout SHA was `047faeb0921ddcfe175a1063f99bf868b800a0b6`. The original USA ROM SHA-256 `859ec99f…`, archived 2014 movie `06dce29e…`, and staged source SRAM `a6af0ddf…` match all prior original/native cases. Both newly executed original and native replay entry hosts were **1017**, with source entry movie frame **3190** and source result movie frame **8353**. No controller rephasing, raw byte masking, or source ROM modification occurred.

## New bounded real-original evidence

| Independently measured property | RF-015+017 baseline | RF-018 alone | **Exact combined ELF** |
| --- | ---: | ---: | ---: |
| Zoo result, fresh original/native | +5163/+5163 | +5163/+5163 | **+5163/+5163** |
| Next Bowl, source/fresh original/native from Zoo result | +267/+267/+267 | +267/+267/**+265** | **+267/+267/+267** |
| Complete 8 KiB original/native SRAM image matches, 11 Bowl samples | 11/11 | 0/11 | **11/11** |
| Complete 128 KiB original/native WRAM image matches, 11 Bowl samples | 8/11 | 0/11 | **9/11** |
| Unmasked WRAM differing-byte occurrences, 11 Bowl samples | 12 | 2,203 | **8** |
| Exact full 128 KiB WRAM checkpoints, 78 across Zoo | 45/78 | 46/78 | **51/78** |
| Aggregate unmasked WRAM-byte difference occurrences, 78 checkpoints | 109 | 105 | **92** |

The full eleven-sample Bowl handoff brackets an independently observed native and original entry at **Zoo result +267**, the same as the 2014 source. All sampled named gameplay fields, full 8 KiB SRAM images, ranked Zoo best lap (`2510` centiseconds) and record checksums agree. Two snapshots **still** have real WRAM stack differences: at **+266** and **+280**, four bytes each in `7E:01ED–01F0`. The +267 WRAM sample is entirely byte-identical, eliminating the previous controls' +267 stack and sound-command-queue `7E:2000/2004` differences *at that observed instant*. This is not proof of safe reader liveness or complete game memory parity.

### Thirteen consecutive sound-transfer samples

Both guests have **all 131,072 WRAM bytes equal at race-relative +5039**. At +5040 and +5045 the `wSndDataPtr` low byte `7E:0063` differs by **one count**:

| Frame | Original $63 | Native $63 | Original/native $69 |
| --- | --- | --- | --- |
| +5040 | `73` | `74` | `BE/BE` |
| +5045 | `B3` | `B4` | `FE/FE` |

At every other adjacent frame +5034..+5046, the original/native `$63` samples agree. The `wSndXferCounter` byte `7E:0069` agrees **in all 13**. Earlier RF-015+017 and RF-018-alone runs diverged at both audio direct-page bytes throughout +5040..+5046. The exact composite candidate therefore genuinely narrows this sampled original/native audio-state discrepancy. **It has not proved the executed writer/reader PC, SPC `$2140..43` handshake, sound output or full CPU/beam phase.** All 78 checkpoints are unmasked: **51 byte-exact, 27 nonexact and 92 cumulative differing-byte occurrences**. Unsampled frames remain unobserved.

## Why the experiment's workflow is red, despite a valid producer verdict

The genuine original/native producer finished successfully (exit **0**), and the current main independent campaign classifier returned **`strict_candidate`**, with matching source/fresh-original/native Zoo result and Bowl entry and explicit remaining WRAM residuals. The **last extra validation command in the temporary workflow** then failed. It incorrectly pinned the short three-event source-controller script hash `04ad1c2d…` as if it applied to the longer Zoo observation window. The actual expanded script SHA-256 is `1eb3e8416b7fa40935d097c78d281ca98537c9a555e23f1906a99912dcdb2c52`, independently verified **identical to both RF-015+017 original/native extended-control runs and the RF-018-only extended treatment**. The original SMV, ROM, SRAM seed and native ELF hashes remained identical. The producer report SHA-256 is `cb8907da0f1eb925912388ebd5b656452709808b7c94e8f8ebcc368d09d96c3d` and the independent case result SHA-256 is `c613c82b359eafe2e10f44e0e4e77bfdb33a9000ec0d61c250f08f79c842287b`.

Thus the **experimentally relevant data are valid**, while the custom workflow's final status is a **false red caused by a non-equivalent generated-script digest check**. This is not a waiver for a raw game-state discrepancy. The temporary workflow was deleted, and [PR #1706](https://github.com/gamesbyian/UR-Recomp/pull/1706) closed without merging it. No lasting CI overhead or duplicate CPU build was added.

## Remaining blockers and next source-owner handoff

The exact composite research ELF has **not** been demonstrated to have continuous original-native CPU, SPC or PPU execution parity, every-frame WRAM equality, authentic audio handshake timing, final Windows product executable identity, or cold OS disk persistence. Full-course strict acceptance remains **0/45**. The next small discriminator for the CPU/APU source owner is the *executed* original/native instruction and `$2142` handshake attribution at the two remaining +5040/+5045 one-count `$63` residuals; separately classify the unwaived `7E:01ED–01F0` stack differences at the +266/+280 Bowl handoff. See source-owner [#1689](https://github.com/gamesbyian/UR-Recomp/issues/1689), opt-in combined timing [#1705](https://github.com/gamesbyian/UR-Recomp/pull/1705), and independently outstanding Windows RF-017 source identity [#1686](https://github.com/gamesbyian/UR-Recomp/issues/1686).

The scientific progress is substantial: **the exact combined binary passes authentic sampled Zoo-to-Bowl progression, retains identical full 8 KiB source-earned SRAM, and approaches audio direct-page byte equality much more closely**. It does not justify product release or waive any unmasked residual.
