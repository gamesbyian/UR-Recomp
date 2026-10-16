# RF-029: an IPL ready-compare cycle-4 treatment is a strict original/native negative (October 16, 2026)

**Disposition: experimentally rejected as a parity correction.** CPU/APU research lane. No shipping source, default QA runner, gameplay input, release ledger or ROM changed. **0/45 complete USA events admitted.** Source-pinned evidence: [one-shot run 38961077234](https://github.com/gamesbyian/UR-Recomp/actions/runs/38961077234), verified case artifact `12073346907` (ZIP SHA-256 `4202c6f9f328a26a13e936069756609a429879d5309111284f1b660acb333735`), independently recomputed full producer JSON SHA-256 `c5166cf752d75b71a2c9b2adc4a78ece41ace9f893af25750450080dff36f9cb`, and durable [machine-readable baseline/treatment A/B receipt](../analysis/data/rf029-zoo-iplcmp-negative-ab-20261016.json).

## Hypothesis and experiment

The source-confirmed SPC IPL at PC `FFCF` runs `78 CC F4`, `CMP $F4,#$CC` (five SPC cycles). The *actual pinned original Snes9x core source* `snes9xgit/snes9x@1bcc369e89f08243e0a462882fb1f3e42e51de3a` steps the opcode as opcode fetch, immediate fetch, address fetch, `$F4` port read, idle cycle. Thus the source port read happens on **cycle four**, whereas RF-026's existing research-only SPC approximation performs every opcode's reads/writes on the **last** cycle (five here). An original/native [RF-028](RF028-INTERRUPT-ENTRY-COST-20261016.md) local executed-transport trace had already observed first CPU `$2140=$CC` acknowledgement after 8/2 SPC cycles and 9/7 CPU polls (original/native), associated with the Zoo +5040 sound upload. A one-cycle early port read was a plausible but **unproven causal discriminator**.

Temporary RF-029 source on experiment commit `1c59ae63b216d708f25e18361a7ad2b595fada60` first stages exactly the established RF-015..019 + RF-021/023/024/026/028 research corrections on the pinned game `10b864b9d14a7b7416dd909eb7b054c88faef101` / framework `075fbe4c8e0d97b0013be541795c39cb644a9709`. It then applies **only** an IPL-visible, PC-FFCF, page-0 `$F4` read at the previous SPC cycle, using reserved serialized APU padding to consume it once on the fifth-cycle opcode. All other opcodes, opcode duration, CPU controller input, ROM and SRAM seed were unchanged. The compiled C unit A/B demonstrated exactly one earlier port read when the CPU port changed between those cycles; the experiment's exact-head tooling tests passed. This narrowly tests the hypothesis. It does not construct a general hardware per-access SPC model.

The real original USA input identities are unchanged: ROM SHA256 `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`, 2014 movie SHA256 `06dce29e9d36997fc2a1fac4bab72180ab6c8096366cfcf05780c1b2dea4b442`, source SRAM SHA256 `a6af0ddf25ae5feafba301100938f5ef81137ee76dcdc483a04fb6e961347828`, expanded source-original/native input-script SHA256 `1eb3e8416b7fa40935d097c78d281ca98537c9a555e23f1906a99912dcdb2c52`. Both sides independently calibrated race-entry hosts **1017/1017** and native input shift **zero**. Every complete 131,072-byte WRAM checkpoint compared without any byte masking.

## Exact independently reviewed result

I separately downloaded and rehashed the **same original/native composite baseline** [run 38884542449](https://github.com/gamesbyian/UR-Recomp/actions/runs/38884542449), case ZIP `21c28cd711519e150ce10e2753dc2d29b6e3eac1004b03d34683c3e03613c718`, baseline producer JSON `cb8907da0f1eb925912388ebd5b656452709808b7c94e8f8ebcc368d09d96c3d`. Baseline native ELF is `9a3bd17afd8377a4c83e76c05cd57dfdae2488e498aa4bea1b90a2baa018bb48`, Snes9x original core `ec4ce30d80e0b2c22b5d700aec01d601bd85db452ccb8e2b32fa75e9fe63554a`. Treatment rebuilt the CPU/APU native ELF `1f228fc4bbb838379dda4d4d11bad4519e3769782966265fd69681fe608b0ad8` and original reference core `fe8d37b5b3760950fc05ec002a963181ff351a98e19f4447d620577b85d6d396`.

**Crucial original control:** all **78 corresponding original-side 128-KiB WRAM SHA256 values are identical across the separately built experiments**, despite different reference-core binary SHA. The native WRAM hashes change in **exactly seven** checkpoints, +5040 through +5046, and at none of the other 71. Input script/controller-window hashes and all original semantic event anchors likewise match. This isolates the experiment's *sampled* effect without assuming either native binary is identical.

| Genuine original/native observation | Composite baseline | +RF-029 treatment |
| --- | --- | --- |
| Source / fresh-original / native Zoo result | +5163 / +5163 / +5163 | **unchanged** |
| Source / fresh-original / native next Bowl, from result | +267 / +267 / +267 | **unchanged** |
| Next Bowl full 8192-byte SRAM pairs | 11/11 exact | **11/11 exact** |
| Next Bowl 128-KiB WRAM pairs | 9/11 exact; 8 stack-byte occurrences | **unchanged** |
| Zoo 78 full 128-KiB WRAM checkpoints | **51 exact**, 92 differing-byte occurrences | **46 exact**, 104 differing-byte occurrences |
| Zoo +5039 all 128-KiB WRAM bytes | equal | equal |
| +5040 original/native `$63` (hex) | `73/74` | **`73/75`** |
| +5040 original/native `$69` (hex) | `BE/BE` | **`BE/BF`** |
| +5034..5046 original/native `$69` | all 13 equal | **seven divergent frames +5040..5046** |
| `$63` divergent frames | +5040, +5045 only | **all seven +5040..5046** |

The resulting original/native race has **matching settled guest text**, ranked MIKE best lap 2510 centiseconds and complete earned SRAM parity at all eleven Bowl samples. All sampled named states agree; result onset and Bowl race activation are authentic. The two 4-byte low-stack residuals at next-Bowl +266/+280 (`7E:01ED–01F0`) remain unwaived. The original and native whole-WRAM first sampled difference is already +1 at stack `7E:01ED`, separately from RF-029's first treatment-induced difference +5040.

The case producer exited **0**, the independent existing strict classifier emitted **`strict_candidate`** (result-level only), and the manual one-shot and unit/build jobs succeeded. Those are valid experimental results, **not a full original/native event admission**: there are unsampled frames, no proof of all CPU/SPC instruction clocks, live stack consumers or source-bound Windows production/cold disk restart.

## Rejection, cleanup and successor

Because the new one-cycle phase treatment made both original/native sound-transfer fields *less* equal while leaving all other observed guest frames unchanged, **RF-029 is rejected as a standalone gameplay-fidelity correction**. The experiment's temporary push workflow, manually staged patch code, shared campaign input and regression test were removed from the review branch after execution; their exact source and compiled treatment are preserved in the immutable run and PR history. No research-only timing opcode has been added to Windows, and no permanent CI trigger remains.

The next evidence-producing question is the *executed* original/native IPL PC, cycle-4 port read, echo write, CPU `$2140` polls, and CPU/master-beam mapping **at the specific sound-driver restart**. The phase difference may also depend on the sender's queued write and the SPC echo opcode bus cycle, not merely the one reader. Local #1689 transport evidence already shows the same write sequence and 9/7 poll discrepancy; a fully source-correct per-access SPC model should be qualified by executed first difference and an unchanged result/+267/11-SRAM protocol, rather than guessing a clock offset. Independently trace low-stack +266/+280 read liveness. Do not launch a broad 45-case campaign, mask inert bytes, waive semantic differences or count any of the 45 events.

**Disposition:** strict negative for RF-029; positive bounded authentic Zoo result/return unchanged; **USA 0/45**.
