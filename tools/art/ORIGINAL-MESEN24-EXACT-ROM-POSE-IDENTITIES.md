# ART-4K: 48 authentic racer frames recovered from the original ROM's 24×64 pose grid

**Original-source verification, November 3–4, 2026.** The original SNES game contains a ROM-indexed primary racer presentation frame grid with **24 phase states × 64 angle-index states = 1,536 distinct packed primary records**. By matching exact **raw 32-byte SNES 4bpp tiles** from that ROM to the previously preserved MesenCE original source VRAM, **all 24 consecutive executed original PPU ticks for both racers have one uniquely exact 30-of-30 tile frame identity**. An independently implemented 4bpp tile decoder then recreates each observed **complete 64×64 index-plane** with **zero differing index pixels across 48/48 frames = 196,608 original source pixels**. This is an important *2D sprite-asset and indexed source-state* recovery, **not yet a 1994 3D mesh, rig, camera or calibrated physical joint-angle recovery**.

## Evidence boundaries

- **Original ROM:** exact USA retail `reference/roms/retail/Uniracers_USA.sfc`, SHA-256 `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`. The tool refuses a ROM of the wrong size or content. No ROM bytes are included in the generated numerical report.
- **Independent original execution:** already-merged [#3103](https://github.com/gamesbyian/UR-Recomp/pull/3103) Mesen no-frame-skip 24 truly consecutive source ticks **1601–1624**, exact 97-member source archive SHA-256 `28dda3647fecb382fdbf824da7383a8116080df6ec8c98da0b3357a018986cf6`. The existing auditor authenticates the original PPU OAM/VRAM/CGRAM member hashes before any matching. No emulator rerun is required.
- **Original code chain:** authenticated 65816 byte windows in this ROM show `83:EE53..EE6F` advancing/wrapping working phase `$0F83` modulo **24**; `83:EED9..EEEA` combines `phase × 64 + $0F77`; `83:EF06..EF0F` may override the presentation ID with `$0F4F`; `83:F086` masks the working angle index to **six bits**, with facing-dependent correction afterward; `83:F296..F2BA` resolves each frame ID through the three-byte `20:8000` table into banks starting at `23:8000`. `83:F0BB..F295` stages the selected packed-frame 5×6 tile data, and `82:B8AB` consumes it through NMI DMA. These are bounded static original-code byte witnesses; frame-name semantics beyond the tested path remain qualified.
- **Packing reuse:** `tools/extract_racer_presentation_family.py` already recovered the original 30-bit occupancy header, packed 16-bit words and exact original per-piece ROM DMA source address, including low-two-bit source-page offsets. This analysis reuses that library, **does not invent another renderer format**, and verifies a complete distinct 1,536-pointer table. The first 1,080 primary frame records lie in ROM bank `23`; the remaining 456 are in bank `24`. The bank crossing has the original four-byte `FF FF FF 00` padding at ID 1079; every other adjacent primary record has an exact self-describing length matching the next pointer.

## Recovered exact original source frame identities

The original held source OBJ sprite slots use fixed OAM tile numbers **blue OAM96 = 136** and **red OAM97 = 0**. The selected primary renderer footprint has **five rows of six original 8×8 tiles**, in source 64×64 tile columns **1..6** and rows **0..4**, leaving 34 other 8×8 sprite cells. Each of the 30 tiles is a raw **32-byte** source 4bpp payload, thus **960 independently compared original bytes per source sprite and tick**. The candidate identity is selected by exhaustive comparison against all 1,536 original ROM records; exactly **one** candidate matches all 30 tiles in **every** tested original observation. The runner-up always matches fewer than 30.

Independent SNES planar 4bpp bitplane decoding and placement of the winning ROM record reproduce the **full** 64×64 PPU source sprite's original **palette index values** at all 4,096 positions for each of 48 observations. No 2026 GLB, raster-image registration, per-frame flip, camera, manual classification, RGB threshold, model pose fit, silhouette overlap objective or source palette-index→physical-part guess participates in this determination. The unfilled 34 sprite tile cells have index zero in all 48 verified PPU observations; this does not require their unused raw VRAM bytes to be zero.

| Executed Mesen tick | Blue exact frame ID (phase, angle index) | Red exact frame ID (phase, angle index) |
|---:|---|---|
| 1601 | `0x00FD` (3, 61) | `0x0439` (16, 57) |
| 1602 | `0x017D` (5, 61) | `0x0579` (21, 57) |
| 1603 | `0x023C` (8, 60) | `0x0079` (1, 57) |
| 1605 | `0x03BC` (14, 60) | `0x02F9` (11, 57) |
| 1606 | `0x043C` (16, 60) | `0x03FA` (15, 58) |
| 1624 | `0x04FC` (19, 60) | `0x007A` (1, 58) |

The complete 48-row machine-readable timeline includes each original tick, recovered integer ID, ROM phase and angle-index coordinates, independently verified exact 30-tile matching score, next-best candidate score and the SHA of both reconstructed and emulator-observed full 64×64 source planes.

Across these 23 **actual adjacent executed** frame intervals:

- Blue ROM-defined phase advances only **+2 (five times)** or **+3 (18 times)** modulo 24. Its angle index is **61** at two observed ticks, then **60** at 22.
- Red phase advances only **+4 (ten times)** or **+5 (13 times)** modulo 24. Its angle index is **57** for five ticks, then **58** for 19.
- Blue's upper change event 1602→1603 coincides with angle-index **61→60**. Red's 1605→1606 event coincides with angle-index **57→58**. The different observed phase cadence is an authentic source-state difference and directly falsifies treating both racers as having a shared fixed *per-tick 3D angle step* in this window.

**Modeling implications:** This is the first exact source-state pairing between an actually executed 24-tick original racer sequence and the original 1,536-entry presentation family. It enables controlled original-ROM **counterfactuals**: hold phase fixed while changing the angle index, or hold angle index fixed across the 24 phases. The ROM's authored 2D frames were likely generated from high-detail original source modeling and animation, but this exact ROM table alone does not reveal original authoring geometry, camera, lighting, wheel degrees per phase, or continuous interpolation. A simple `360° / 24` wheel interpretation is a *future hypothesis to test*, **not independently calibrated physical truth**.

## Reproduce on any authorized host

The authoritative tool is `tools/art/recover_original_mesen24_rom_pose_ids.py`. It uses only the Python standard library and existing repository ROM/source parsers, validates exact ROM instructions and archive identity, and uses the existing atomic exclusive no-overwrite result writer:

```sh
python3 -m unittest tests.unit.test_art4k_mesen24_rom_pose_ids
python3 -m tools.art.recover_original_mesen24_rom_pose_ids \
  --rom reference/roms/retail/Uniracers_USA.sfc \
  --original-source-zip analysis/data/racer-original-mesen-consecutive-1601-1624-20261103.zip \
  --out /new/location/exact-original-pose-grid-identities.json
```

Retained receipt: `analysis/data/racer-original-mesen24-exact-ROM-pose-IDs-20261103.json`, SHA-256 `6286aedcda6080acf832ecece9fcdb879354db008e870bc00ada02db3ff3aa20`. Six cheap ROM/GLB-free unit tests passed, including exact source-identity/pixel-sum accounting, 24-tick phase and angle histories, 4bpp planar bits 0..15, synthetic exact-match/tie/corrupt-source failure controls and explicit refusal to claim 3D source assets. The full real USA ROM plus original Mesen archive run on the HP also passed.

**Next discriminators, not duplicated work:** (1) take the two original angle transition events and use the **ROM-exact** 24×64 pose grid to separately measure phase-only versus angle-only silhouette/index changes, including interaction; (2) feed the **actual recovered phase timeline**, with declared uncalibrated interpretation, into the existing #3101 2026 articulated five-parent GLB and score original 2D change support under its frozen camera; (3) compare the resulting controlled source-axis change regions against independent model joints/geometry and period detailed visual references. Keep current canonical #2832 rig unapproved, no release/owner likeness milestone.
