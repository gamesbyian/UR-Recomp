# Racer OAM / viewport structural island: 82:ACA5..B17F

ROM-backed run `36855218823` validates a gapless, instruction-aligned structural partition of the full named `Race_BuildRacerOAMState` routine across all four preserved builds.

## Result

- USA routine coverage: **1,243 contiguous bytes** in 12 executable regions.
- USA analyzer roles: **498 opcode bytes / 714 operand bytes / 31 statically unreached bytes**.
- Legacy beta is byte-identical to USA across every region.
- Europe follows shift `+7` through the ordinary/shared-camera and first split-camera path, then `+5`, then `+3`.
- PAL prototype follows shift `-15`, then `-17`, then `-19` at the same two boundaries.
- Both shift changes are explained by the same two semantically redundant code contractions already present in the November 1994 PAL prototype.

## PAL-line contractions

- USA `82:AF96..AF97`: `C2 20` / `REP #$20`, immediately followed by another `REP #$20`. PAL prototype and Europe omit the first copy.
- USA `82:B01F..B020`: the same duplicated `REP #$20` pattern in the sibling split-camera projection. PAL prototype and Europe again omit the first copy.
- Each omission removes 2 bytes without changing accumulator state, so these are code-cleanup lineage edits rather than changed viewport behavior.

## Structural regions

| USA range | Region | Bytes | USA op | USA unreached | PAL prototype | Europe |
|---|---|---:|---:|---:|---|---|
| `82:ACA5..82:ACF2` | entry_mode_setup | 78 | 30 | 0 | 82:AC96..82:ACE3 (-15, size 78) | 82:ACAC..82:ACF9 (+7, size 78) |
| `82:ACF3..82:ADA6` | p1_projection | 180 | 75 | 0 | 82:ACE4..82:AD97 (-15, size 180) | 82:ACFA..82:ADAD (+7, size 180) |
| `82:ADA7..82:ADC0` | p2_dispatch_setup | 26 | 10 | 0 | 82:AD98..82:ADB1 (-15, size 26) | 82:ADAE..82:ADC7 (+7, size 26) |
| `82:ADC1..82:AE59` | p2_projection_shared_camera | 153 | 65 | 0 | 82:ADB2..82:AE4A (-15, size 153) | 82:ADC8..82:AE60 (+7, size 153) |
| `82:AE5A..82:AF30` | p2_projection_alt_camera | 215 | 76 | 31 | 82:AE4B..82:AF21 (-15, size 215) | 82:AE61..82:AF37 (+7, size 215) |
| `82:AF31..82:AF4E` | split_mode_setup | 30 | 11 | 0 | 82:AF22..82:AF3F (-15, size 30) | 82:AF38..82:AF55 (+7, size 30) |
| `82:AF4F..82:AFD4` | split_p2_projection | 134 | 58 | 0 | 82:AF40..82:AFC3 (-15, size 132) | 82:AF56..82:AFD9 (+7, size 132) |
| `82:AFD5..82:B056` | split_p1_projection | 130 | 56 | 0 | 82:AFC4..82:B043 (-17, size 128) | 82:AFDA..82:B059 (+5, size 128) |
| `82:B057..82:B07A` | post_mode_setup | 36 | 14 | 0 | 82:B044..82:B067 (-19, size 36) | 82:B05A..82:B07D (+3, size 36) |
| `82:B07B..82:B0E5` | post_p2_adjust | 107 | 42 | 0 | 82:B068..82:B0D2 (-19, size 107) | 82:B07E..82:B0E8 (+3, size 107) |
| `82:B0E6..82:B150` | post_p1_adjust | 107 | 42 | 0 | 82:B0D3..82:B13D (-19, size 107) | 82:B0E9..82:B153 (+3, size 107) |
| `82:B151..82:B17F` | post_final_flags | 47 | 19 | 0 | 82:B13E..82:B16C (-19, size 47) | 82:B154..82:B182 (+3, size 47) |

The routine is a concrete widescreen seam: simulation-space racer coordinates enter here, camera-relative projection/culling policy is applied, and screen/OAM-facing state exits downstream. The present result recovers architecture and lineage; it does not yet prescribe widescreen policy.
