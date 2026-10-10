# QA-01: original Snes9x versus Baldosa terminal timing, three real events

**Evidence class:** executed original 2014 movie and pinned Baldosa results for the real USA **Circuit, Stunt and Race B** families. These are original/native *investigative candidates*, **not** independently accepted complete-course release passes. USA ledger stays **0/45**.

| Course/event | Original entry host | Baldosa entry host | Original result, relative | Baldosa result, relative | Original result host | Baldosa result host |
|---|---:|---:|---:|---:|---:|---:|
| Zoo Circuit, MIKE 1:16.46 | 1604 | 1606 | +5163 | +5162 | 6767 | 6768 |
| Bowl Stunt, MIKE 764 | 984 | 985 | +3365 | +3364 | 4349 | 4349 |
| Switcher Race B, MIKE 1:08.81 | 1079 | 1081 | +4704 | +4702 | 5783 | 5783 |

The table is fully source-backed and unit-tested against **three different real artifacts**, not estimated as a uniform phase correction. Machine-readable source records: [three-event timing matrix](../analysis/data/qa01-three-event-original-baldosa-timing-matrix-20261010.json), [Zoo observed terminal boundary](../analysis/data/zoo-original-baldosa-fixed-result-boundary.json), [Bowl tally host witness](../analysis/data/bowl-tally-full-guest-same-host-eight-frame-20261009.json) and [Switcher full paired-result witness](../analysis/data/switcher-original-baldosa-paired-race-b-result-20261010.json).

**Invariant:** For each guest, **terminal absolute host frame = independently observed entry absolute host frame + result guest-relative frame**. The observed native-minus-original entry lag is **+2, +1, +2**, whereas the result guest-relative phase lead is **−1, −1, −2** respectively. Therefore the terminal host deltas are **+1, 0, 0**, not a universal single phase shift. All three cases reach authentic, identical settled PPU result text on both guests, but that does **not** show parity of every underlying guest instruction, course timer, NMI or progress update. The original and Baldosa guest entry states can agree even though entry itself is two host frames later on Baldosa.

## Source-visible implications for future agents

An absolute host-result match is **not** guest-relative result parity, and a guest-relative frame offset is **not** proof of physics acceleration. Do not silently time-shift controller masks, which already failed Zoom Zoo source-event completion at offsets ±1. Distinguish at least three independent axes in follow-up diagnostics: (1) original movie source to freshly calibrated original entry, (2) original reference to native guest-relative progression, and (3) reference/native same-absolute-host effects, especially during race and menu result handoffs.

**Switcher is currently the narrowest actual discriminator.** The first 43 observed native/reference guest-relative captures (real [run 38072910224](https://github.com/gamesbyian/UR-Recomp/actions/runs/38072910224)) agree on all sampled non-menu/course fields, with menu/course differences only at source-relative **+4664** and **+4697/+4698**. At +4664 original remains track 3/menu `0x00` while native has track 0/menu `0x84`. Later at +4697/+4698 original is still track 0/menu `0x84` and native has restored track 3/menu `0x16`. Original course-0 stage starts by reference +4665/absolute host 5744; native by +4664/host 5745. Native has restored track 3 by absolute host 5778; original was still track 0 at host 5777. An independent narrow probe is now configured for missing reference-relative **+4699..+4701**; do not assume the result.

**Zoo:** exact fixed-source-relative terminal sample shows native race flag leaving active one relative frame earlier and raw DP `C6/C8` one-step displaced; saved contact differences eventually converge. This is *not* a proven physics rule error or release pass. **Bowl:** both guests hit the same absolute 0x2F tally and 0x18 result frames and MIKE 764, but several post-tally same-host WRAM/VRAM bytes differ transiently. Neither isolated menu scratch nor constant artifact byte counts may be promoted into a gameplay defect without owner/phase evidence.

The cheapest next acceptance-producing experiments are therefore **source-anchored boundary capture and instruction/phase attribution**, not a fourth large generic emulator harness. The full original/native event acceptance still requires deterministic evidence of course identity, genuine P1 finish/score, P2/result behaviour, progression, terminal frame authority, and no undocumented controller input modifications. Keep **USA release acceptance 0/45** until independent parity is established.
