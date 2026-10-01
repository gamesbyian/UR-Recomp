# Comparative structural census

This census aggregates only accepted comparative structure-recovery islands, so the counts below are a conservative **floor**, not a whole-ROM coverage percentage.

- bounded regions: **25** (22 code, 3 data)
- bounded bytes: **3165** (2957 code-region bytes, 208 explicit data bytes)
- analyzer-classified USA opcode bytes inside code regions: **1258**
- represented USA banks: **81, 82**

| USA range | Kind | Bytes | Source | Region | PAL prototype | Europe retail | Legacy beta |
|---|---|---:|---|---|---|---|---|
| `81:82E2..81:82E5` | code | 4 | object-collision | long_entry_wrapper | 81:82C5..81:82C8 (-29; 0.750) | 81:82B7..81:82BA (-43; 0.750) | 81:82E2..81:82E5 (+0; 1.000) |
| `81:82E6..81:831F` | code | 58 | object-collision | dispatcher_head | 81:82C9..81:8302 (-29; 0.914) | 81:82BB..81:82F4 (-43; 0.862) | 81:82E6..81:831F (+0; 1.000) |
| `81:8320..81:833D` | data | 30 | object-collision | handler_pointer_prefix | 81:8303..81:8320 (-29; 0.500) | 81:82F5..81:8312 (-43; 0.500) | 81:8320..81:833D (+0; 1.000) |
| `81:833E..81:8340` | code | 3 | object-collision | dispatcher_tail | 81:8321..81:8323 (-29; 1.000) | 81:8313..81:8315 (-43; 1.000) | 81:833E..81:8340 (+0; 1.000) |
| `81:8341..81:8371` | code | 49 | object-collision | handler_8341 | 81:8324..81:8354 (-29; 0.898) | 81:831B..81:834B (-38; 0.857) | 81:8341..81:8371 (+0; 1.000) |
| `81:8372..81:83A3` | data | 50 | object-collision | lookup_8372 | 81:8355..81:8386 (-29; 1.000) | 81:834C..81:837D (-38; 1.000) | 81:8372..81:83A3 (+0; 1.000) |
| `81:83A4..81:84D1` | code | 302 | object-collision | handler_83A4 | 81:8387..81:84B4 (-29; 0.871) | 81:837E..81:84AB (-38; 0.828) | 81:83A4..81:84D1 (+0; 1.000) |
| `82:A22B..82:A27B` | code | 81 | racer-update | routine_A22B | 82:A221..82:A271 (-10; 0.852) | 82:A237..82:A287 (+12; 0.852) | 82:A22B..82:A27B (+0; 1.000) |
| `82:A27C..82:A2D3` | code | 88 | racer-update | routine_A27C | 82:A272..82:A2C9 (-10; 0.511) | 82:A288..82:A2DF (+12; 0.511) | 82:A27C..82:A2D3 (+0; 1.000) |
| `82:A2D4..82:A353` | data | 128 | racer-update | table_A2D4 | 82:A2C5..82:A344 (-15; 1.000) | 82:A2DB..82:A35A (+7; 1.000) | 82:A2D4..82:A353 (+0; 1.000) |
| `82:A354..82:A497` | code | 324 | racer-update | routine_A354 | 82:A345..82:A488 (-15; 0.821) | 82:A35B..82:A49E (+7; 0.815) | 82:A354..82:A497 (+0; 1.000) |
| `82:A498..82:A5F2` | code | 347 | racer-update | routine_A498 | 82:A489..82:A5E3 (-15; 0.873) | 82:A49F..82:A5F9 (+7; 0.833) | 82:A498..82:A5F2 (+0; 1.000) |
| `82:A5F3..82:A617` | code | 37 | racer-update | routine_A5F3 | 82:A5E4..82:A608 (-15; 0.892) | 82:A5FA..82:A61E (+7; 0.892) | 82:A5F3..82:A617 (+0; 1.000) |
| `82:A618..82:A6F0` | code | 217 | racer-update | routine_A618 | 82:A609..82:A6E1 (-15; 0.954) | 82:A61F..82:A6F7 (+7; 0.889) | 82:A618..82:A6F0 (+0; 1.000) |
| `82:A6F1..82:A8C1` | code | 465 | racer-update | routine_A6F1 | 82:A6E2..82:A8B2 (-15; 0.888) | 82:A6F8..82:A8C8 (+7; 0.873) | 82:A6F1..82:A8C1 (+0; 1.000) |
| `82:A8C2..82:A967` | code | 166 | racer-update | routine_A8C2 | 82:A8B3..82:A958 (-15; 0.837) | 82:A8C9..82:A96E (+7; 0.831) | 82:A8C2..82:A967 (+0; 1.000) |
| `82:A968..82:A9AB` | code | 68 | racer-update | Player_ApplyVerticalAcceleration | 82:A959..82:A99C (-15; 0.912) | 82:A96F..82:A9B2 (+7; 0.897) | 82:A968..82:A9AB (+0; 1.000) |
| `82:A9AC..82:AA08` | code | 93 | racer-update | routine_A9AC | 82:A99D..82:A9F9 (-15; 0.882) | 82:A9B3..82:AA0F (+7; 0.871) | 82:A9AC..82:AA08 (+0; 1.000) |
| `82:AA09..82:AA69` | code | 97 | racer-update | routine_AA09 | 82:A9FA..82:AA5A (-15; 0.887) | 82:AA10..82:AA70 (+7; 0.876) | 82:AA09..82:AA69 (+0; 1.000) |
| `82:AA6A..82:AA6D` | code | 4 | racer-update | Input_LongEntryWrapper | 82:AA5B..82:AA5E (-15; 0.750) | 82:AA71..82:AA74 (+7; 0.750) | 82:AA6A..82:AA6D (+0; 1.000) |
| `82:E165..82:E1CF` | code | 107 | course-materialization | setup | 82:E101..82:E16B (-100; 0.944) | 82:E12B..82:E195 (-58; 0.944) | 82:E165..82:E1CF (+0; 1.000) |
| `82:E1D1..82:E213` | code | 67 | course-materialization | resource_record_header | 82:E16D..82:E1AF (-100; 0.896) | 82:E197..82:E1D9 (-58; 0.896) | 82:E1D1..82:E213 (+0; 1.000) |
| `82:E216..82:E2FF` | code | 234 | course-materialization | dma_row_loop | 82:E1B2..82:E29B (-100; 0.885) | 82:E1DC..82:E2C5 (-58; 0.885) | 82:E216..82:E2FF (+0; 1.000) |
| `82:E302..82:E385` | code | 132 | course-materialization | resource_materialize_A000_C000 | 82:E29E..82:E321 (-100; 0.955) | 82:E2C8..82:E34B (-58; 0.955) | 82:E302..82:E385 (+0; 1.000) |
| `82:E388..82:E395` | code | 14 | course-materialization | exit | 82:E324..82:E331 (-100; 0.929) | 82:E34E..82:E35B (-58; 0.929) | 82:E388..82:E395 (+0; 1.000) |

## Current growth rule

Choose the next island for information gain and shipping leverage, not byte count. The current census now spans racer simulation, object/collision dispatch, and course materialization. A fourth island should therefore come from a different high-value subsystem, with rendering/OAM or camera/viewport structure preferred if one pass can recover multiple boundaries or tables.
