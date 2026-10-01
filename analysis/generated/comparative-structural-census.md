# Comparative structural census

This census aggregates only accepted comparative structure-recovery islands, so the counts below are a conservative **floor**, not a whole-ROM coverage percentage.

- bounded regions: **38** (35 code, 3 data)
- bounded bytes: **4791** (4583 code-region bytes, 208 explicit data bytes)
- analyzer-classified USA opcode bytes inside code regions: **1923**
- represented USA banks: **81, 82**

| USA range | Kind | Bytes | Source | Region | PAL prototype | Europe retail | Legacy beta |
|---|---|---:|---|---|---|---|---|
| `81:82E2..81:82E5` | code | 4 | object-collision | long_entry_wrapper | 81:82C5..81:82C8 (-29; size 4; sim 0.750) | 81:82B7..81:82BA (-43; size 4; sim 0.750) | 81:82E2..81:82E5 (+0; size 4; sim 1.000) |
| `81:82E6..81:831F` | code | 58 | object-collision | dispatcher_head | 81:82C9..81:8302 (-29; size 58; sim 0.914) | 81:82BB..81:82F4 (-43; size 58; sim 0.862) | 81:82E6..81:831F (+0; size 58; sim 1.000) |
| `81:8320..81:833D` | data | 30 | object-collision | handler_pointer_prefix | 81:8303..81:8320 (-29; size 30; sim 0.500) | 81:82F5..81:8312 (-43; size 30; sim 0.500) | 81:8320..81:833D (+0; size 30; sim 1.000) |
| `81:833E..81:8340` | code | 3 | object-collision | dispatcher_tail | 81:8321..81:8323 (-29; size 3; sim 1.000) | 81:8313..81:8315 (-43; size 3; sim 1.000) | 81:833E..81:8340 (+0; size 3; sim 1.000) |
| `81:8341..81:8371` | code | 49 | object-collision | handler_8341 | 81:8324..81:8354 (-29; size 49; sim 0.898) | 81:831B..81:834B (-38; size 49; sim 0.857) | 81:8341..81:8371 (+0; size 49; sim 1.000) |
| `81:8372..81:83A3` | data | 50 | object-collision | lookup_8372 | 81:8355..81:8386 (-29; size 50; sim 1.000) | 81:834C..81:837D (-38; size 50; sim 1.000) | 81:8372..81:83A3 (+0; size 50; sim 1.000) |
| `81:83A4..81:84D1` | code | 302 | object-collision | handler_83A4 | 81:8387..81:84B4 (-29; size 302; sim 0.871) | 81:837E..81:84AB (-38; size 302; sim 0.828) | 81:83A4..81:84D1 (+0; size 302; sim 1.000) |
| `81:8B95..81:8D13` | code | 383 | course-surface-sampler | Course_SampleRuntimeSurface | 81:8B75..81:8CF3 (-32; size 383; sim 0.971) | 81:8B75..81:8CF3 (-32; size 383; sim 0.971) | 81:8B95..81:8D13 (+0; size 383; sim 1.000) |
| `82:A22B..82:A27B` | code | 81 | racer-update | routine_A22B | 82:A221..82:A271 (-10; size 81; sim 0.852) | 82:A237..82:A287 (+12; size 81; sim 0.852) | 82:A22B..82:A27B (+0; size 81; sim 1.000) |
| `82:A27C..82:A2D3` | code | 88 | racer-update | routine_A27C | 82:A272..82:A2C9 (-10; size 88; sim 0.511) | 82:A288..82:A2DF (+12; size 88; sim 0.511) | 82:A27C..82:A2D3 (+0; size 88; sim 1.000) |
| `82:A2D4..82:A353` | data | 128 | racer-update | table_A2D4 | 82:A2C5..82:A344 (-15; size 128; sim 1.000) | 82:A2DB..82:A35A (+7; size 128; sim 1.000) | 82:A2D4..82:A353 (+0; size 128; sim 1.000) |
| `82:A354..82:A497` | code | 324 | racer-update | routine_A354 | 82:A345..82:A488 (-15; size 324; sim 0.821) | 82:A35B..82:A49E (+7; size 324; sim 0.815) | 82:A354..82:A497 (+0; size 324; sim 1.000) |
| `82:A498..82:A5F2` | code | 347 | racer-update | routine_A498 | 82:A489..82:A5E3 (-15; size 347; sim 0.873) | 82:A49F..82:A5F9 (+7; size 347; sim 0.833) | 82:A498..82:A5F2 (+0; size 347; sim 1.000) |
| `82:A5F3..82:A617` | code | 37 | racer-update | routine_A5F3 | 82:A5E4..82:A608 (-15; size 37; sim 0.892) | 82:A5FA..82:A61E (+7; size 37; sim 0.892) | 82:A5F3..82:A617 (+0; size 37; sim 1.000) |
| `82:A618..82:A6F0` | code | 217 | racer-update | routine_A618 | 82:A609..82:A6E1 (-15; size 217; sim 0.954) | 82:A61F..82:A6F7 (+7; size 217; sim 0.889) | 82:A618..82:A6F0 (+0; size 217; sim 1.000) |
| `82:A6F1..82:A8C1` | code | 465 | racer-update | routine_A6F1 | 82:A6E2..82:A8B2 (-15; size 465; sim 0.888) | 82:A6F8..82:A8C8 (+7; size 465; sim 0.873) | 82:A6F1..82:A8C1 (+0; size 465; sim 1.000) |
| `82:A8C2..82:A967` | code | 166 | racer-update | routine_A8C2 | 82:A8B3..82:A958 (-15; size 166; sim 0.837) | 82:A8C9..82:A96E (+7; size 166; sim 0.831) | 82:A8C2..82:A967 (+0; size 166; sim 1.000) |
| `82:A968..82:A9AB` | code | 68 | racer-update | Player_ApplyVerticalAcceleration | 82:A959..82:A99C (-15; size 68; sim 0.912) | 82:A96F..82:A9B2 (+7; size 68; sim 0.897) | 82:A968..82:A9AB (+0; size 68; sim 1.000) |
| `82:A9AC..82:AA08` | code | 93 | racer-update | routine_A9AC | 82:A99D..82:A9F9 (-15; size 93; sim 0.882) | 82:A9B3..82:AA0F (+7; size 93; sim 0.871) | 82:A9AC..82:AA08 (+0; size 93; sim 1.000) |
| `82:AA09..82:AA69` | code | 97 | racer-update | routine_AA09 | 82:A9FA..82:AA5A (-15; size 97; sim 0.887) | 82:AA10..82:AA70 (+7; size 97; sim 0.876) | 82:AA09..82:AA69 (+0; size 97; sim 1.000) |
| `82:AA6A..82:AA6D` | code | 4 | racer-update | Input_LongEntryWrapper | 82:AA5B..82:AA5E (-15; size 4; sim 0.750) | 82:AA71..82:AA74 (+7; size 4; sim 0.750) | 82:AA6A..82:AA6D (+0; size 4; sim 1.000) |
| `82:ACA5..82:ACF2` | code | 78 | racer-oam | entry_mode_setup | 82:AC96..82:ACE3 (-15; size 78; sim 0.872) | 82:ACAC..82:ACF9 (+7; size 78; sim 0.833) | 82:ACA5..82:ACF2 (+0; size 78; sim 1.000) |
| `82:ACF3..82:ADA6` | code | 180 | racer-oam | p1_projection | 82:ACE4..82:AD97 (-15; size 180; sim 0.933) | 82:ACFA..82:ADAD (+7; size 180; sim 0.856) | 82:ACF3..82:ADA6 (+0; size 180; sim 1.000) |
| `82:ADA7..82:ADC0` | code | 26 | racer-oam | p2_dispatch_setup | 82:AD98..82:ADB1 (-15; size 26; sim 0.846) | 82:ADAE..82:ADC7 (+7; size 26; sim 0.769) | 82:ADA7..82:ADC0 (+0; size 26; sim 1.000) |
| `82:ADC1..82:AE59` | code | 153 | racer-oam | p2_projection_shared_camera | 82:ADB2..82:AE4A (-15; size 153; sim 0.928) | 82:ADC8..82:AE60 (+7; size 153; sim 0.850) | 82:ADC1..82:AE59 (+0; size 153; sim 1.000) |
| `82:AE5A..82:AF30` | code | 215 | racer-oam | p2_projection_alt_camera | 82:AE4B..82:AF21 (-15; size 215; sim 0.930) | 82:AE61..82:AF37 (+7; size 215; sim 0.851) | 82:AE5A..82:AF30 (+0; size 215; sim 1.000) |
| `82:AF31..82:AF4E` | code | 30 | racer-oam | split_mode_setup | 82:AF22..82:AF3F (-15; size 30; sim 0.867) | 82:AF38..82:AF55 (+7; size 30; sim 0.867) | 82:AF31..82:AF4E (+0; size 30; sim 1.000) |
| `82:AF4F..82:AFD4` | code | 134 | racer-oam | split_p2_projection | 82:AF40..82:AFC3 (-15; size 132; sim 0.493) | 82:AF56..82:AFD9 (+7; size 132; sim 0.425) | 82:AF4F..82:AFD4 (+0; size 134; sim 1.000) |
| `82:AFD5..82:B056` | code | 130 | racer-oam | split_p1_projection | 82:AFC4..82:B043 (-17; size 128; sim 0.531) | 82:AFDA..82:B059 (+5; size 128; sim 0.454) | 82:AFD5..82:B056 (+0; size 130; sim 1.000) |
| `82:B057..82:B07A` | code | 36 | racer-oam | post_mode_setup | 82:B044..82:B067 (-19; size 36; sim 0.833) | 82:B05A..82:B07D (+3; size 36; sim 0.778) | 82:B057..82:B07A (+0; size 36; sim 1.000) |
| `82:B07B..82:B0E5` | code | 107 | racer-oam | post_p2_adjust | 82:B068..82:B0D2 (-19; size 107; sim 0.907) | 82:B07E..82:B0E8 (+3; size 107; sim 0.897) | 82:B07B..82:B0E5 (+0; size 107; sim 1.000) |
| `82:B0E6..82:B150` | code | 107 | racer-oam | post_p1_adjust | 82:B0D3..82:B13D (-19; size 107; sim 0.907) | 82:B0E9..82:B153 (+3; size 107; sim 0.897) | 82:B0E6..82:B150 (+0; size 107; sim 1.000) |
| `82:B151..82:B17F` | code | 47 | racer-oam | post_final_flags | 82:B13E..82:B16C (-19; size 47; sim 0.872) | 82:B154..82:B182 (+3; size 47; sim 0.872) | 82:B151..82:B17F (+0; size 47; sim 1.000) |
| `82:E165..82:E1CF` | code | 107 | course-materialization | setup | 82:E101..82:E16B (-100; size 107; sim 0.944) | 82:E12B..82:E195 (-58; size 107; sim 0.944) | 82:E165..82:E1CF (+0; size 107; sim 1.000) |
| `82:E1D1..82:E213` | code | 67 | course-materialization | resource_record_header | 82:E16D..82:E1AF (-100; size 67; sim 0.896) | 82:E197..82:E1D9 (-58; size 67; sim 0.896) | 82:E1D1..82:E213 (+0; size 67; sim 1.000) |
| `82:E216..82:E2FF` | code | 234 | course-materialization | dma_row_loop | 82:E1B2..82:E29B (-100; size 234; sim 0.885) | 82:E1DC..82:E2C5 (-58; size 234; sim 0.885) | 82:E216..82:E2FF (+0; size 234; sim 1.000) |
| `82:E302..82:E385` | code | 132 | course-materialization | resource_materialize_A000_C000 | 82:E29E..82:E321 (-100; size 132; sim 0.955) | 82:E2C8..82:E34B (-58; size 132; sim 0.955) | 82:E302..82:E385 (+0; size 132; sim 1.000) |
| `82:E388..82:E395` | code | 14 | course-materialization | exit | 82:E324..82:E331 (-100; size 14; sim 0.929) | 82:E34E..82:E35B (-58; size 14; sim 0.929) | 82:E388..82:E395 (+0; size 14; sim 1.000) |

## Current growth rule

Choose subsequent islands for implementation leverage, not byte count. The census now spans racer simulation, object/collision dispatch, course materialization, the full racer OAM/viewport builder, and the per-racer course runtime surface sampler. Any sixth island should illuminate another shipping-critical subsystem rather than extending these already-bounded corridors without a concrete need.
