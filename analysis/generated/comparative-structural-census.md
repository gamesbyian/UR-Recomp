# Comparative structural census

This is the first machine-queryable census for the comparative structure-recovery phase. It aggregates only already-supported boundaries, so the counts below are a **floor**, not a whole-ROM coverage percentage.

- bounded regions: **129** (117 code, 12 data)
- bounded bytes: **20789** (19356 code-region bytes, 1433 data bytes)
- analyzer-classified USA opcode bytes inside code regions: **8151**
- represented USA banks: **81, 82, 83**

| USA range | Kind | Bytes | Source | Region | PAL prototype | Europe retail | Legacy beta |
|---|---|---:|---|---|---|---|---|
| `81:8050..81:8101` | code | 178 | checkpoint-finish | entry_time_prefix | 81:8050..81:8101 (+0; size 178; sim 0.904) | 81:8050..81:8101 (+0; size 178; sim 0.904) | 81:8050..81:8101 (+0; size 178; sim 1.000) |
| `81:8102..81:8117` | code | 22 | checkpoint-finish | frame_normalization_usa_shape | 81:8102..81:8117 (+0; size 22; sim 0.955) | — | 81:8102..81:8117 (+0; size 22; sim 1.000) |
| `81:8118..81:8194` | code | 125 | checkpoint-finish | post_normalization | 81:8118..81:8194 (+0; size 125; sim 0.976) | 81:810A..81:8186 (-14; size 125; sim 0.944) | 81:8118..81:8194 (+0; size 125; sim 1.000) |
| `81:8195..81:81D3` | code | 63 | checkpoint-finish | lap_hud | 81:8195..81:81D3 (+0; size 63; sim 0.857) | 81:8187..81:81C5 (-14; size 63; sim 0.825) | 81:8195..81:81D3 (+0; size 63; sim 1.000) |
| `81:81D4..81:820F` | code | 60 | checkpoint-finish | late_pre_contractions | 81:81D4..81:820F (+0; size 60; sim 0.983) | 81:81C6..81:8201 (-14; size 60; sim 0.983) | 81:81D4..81:820F (+0; size 60; sim 1.000) |
| `81:8210..81:8215` | code | 6 | checkpoint-finish | pal_delete_1 | — | — | 81:8210..81:8215 (+0; size 6; sim 1.000) |
| `81:8216..81:8226` | code | 17 | checkpoint-finish | late_after_delete_1 | 81:8210..81:8220 (-6; size 17; sim 1.000) | 81:8202..81:8212 (-20; size 17; sim 1.000) | 81:8216..81:8226 (+0; size 17; sim 1.000) |
| `81:8227..81:822C` | code | 6 | checkpoint-finish | pal_delete_2 | — | — | 81:8227..81:822C (+0; size 6; sim 1.000) |
| `81:822D..81:823D` | code | 17 | checkpoint-finish | late_after_delete_2 | 81:8221..81:8231 (-12; size 17; sim 1.000) | 81:8213..81:8223 (-26; size 17; sim 1.000) | 81:822D..81:823D (+0; size 17; sim 1.000) |
| `81:823E..81:8243` | code | 6 | checkpoint-finish | pal_delete_3 | — | — | 81:823E..81:8243 (+0; size 6; sim 1.000) |
| `81:8244..81:8252` | code | 15 | checkpoint-finish | late_after_delete_3 | 81:8232..81:8240 (-18; size 15; sim 1.000) | 81:8224..81:8232 (-32; size 15; sim 1.000) | 81:8244..81:8252 (+0; size 15; sim 1.000) |
| `81:8253..81:8259` | code | 7 | checkpoint-finish | pal_delete_4 | — | — | 81:8253..81:8259 (+0; size 7; sim 1.000) |
| `81:825A..81:8277` | code | 30 | checkpoint-finish | late_after_delete_4 | 81:8241..81:825E (-25; size 30; sim 0.933) | 81:8233..81:8250 (-39; size 30; sim 0.867) | 81:825A..81:8277 (+0; size 30; sim 1.000) |
| `81:8278..81:827B` | code | 4 | checkpoint-finish | pal_delete_5 | — | — | 81:8278..81:827B (+0; size 4; sim 1.000) |
| `81:827C..81:82E0` | code | 101 | checkpoint-finish | late_after_delete_5 | 81:825F..81:82C3 (-29; size 101; sim 0.901) | 81:8251..81:82B5 (-43; size 101; sim 0.891) | 81:827C..81:82E0 (+0; size 101; sim 1.000) |
| `81:82E2..81:82E5` | code | 4 | object-collision | long_entry_wrapper | 81:82C5..81:82C8 (-29; size 4; sim 0.750) | 81:82B7..81:82BA (-43; size 4; sim 0.750) | 81:82E2..81:82E5 (+0; size 4; sim 1.000) |
| `81:82E6..81:831F` | code | 58 | object-collision | dispatcher_head | 81:82C9..81:8302 (-29; size 58; sim 0.914) | 81:82BB..81:82F4 (-43; size 58; sim 0.862) | 81:82E6..81:831F (+0; size 58; sim 1.000) |
| `81:8320..81:833D` | data | 30 | object-collision | handler_pointer_prefix | 81:8303..81:8320 (-29; size 30; sim 0.500) | 81:82F5..81:8312 (-43; size 30; sim 0.500) | 81:8320..81:833D (+0; size 30; sim 1.000) |
| `81:833E..81:8340` | code | 3 | object-collision | dispatcher_tail | 81:8321..81:8323 (-29; size 3; sim 1.000) | 81:8313..81:8315 (-43; size 3; sim 1.000) | 81:833E..81:8340 (+0; size 3; sim 1.000) |
| `81:8341..81:8371` | code | 49 | object-collision | handler_8341 | 81:8324..81:8354 (-29; size 49; sim 0.898) | 81:831B..81:834B (-38; size 49; sim 0.857) | 81:8341..81:8371 (+0; size 49; sim 1.000) |
| `81:8372..81:83A3` | data | 50 | object-collision | lookup_8372 | 81:8355..81:8386 (-29; size 50; sim 1.000) | 81:834C..81:837D (-38; size 50; sim 1.000) | 81:8372..81:83A3 (+0; size 50; sim 1.000) |
| `81:83A4..81:84D1` | code | 302 | object-collision | handler_83A4 | 81:8387..81:84B4 (-29; size 302; sim 0.871) | 81:837E..81:84AB (-38; size 302; sim 0.828) | 81:83A4..81:84D1 (+0; size 302; sim 1.000) |
| `81:8A4A..81:8B94` | code | 331 | course-sector-gather | sector_neighborhood_gather | 81:8A2A..81:8B74 (-32; size 331; sim 0.994) | 81:8A2A..81:8B74 (-32; size 331; sim 0.961) | 81:8A4A..81:8B94 (+0; size 331; sim 1.000) |
| `81:8B95..81:8D13` | code | 383 | course-surface-sampler | Course_SampleRuntimeSurface | 81:8B75..81:8CF3 (-32; size 383; sim 0.971) | 81:8B75..81:8CF3 (-32; size 383; sim 0.971) | 81:8B95..81:8D13 (+0; size 383; sim 1.000) |
| `81:8D14..81:8D17` | code | 4 | player-state-marshal | long_entry_wrapper | 81:8CF4..81:8CF7 (-32; size 4; sim 0.500) | 81:8CF4..81:8CF7 (-32; size 4; sim 0.500) | 81:8D14..81:8D17 (+0; size 4; sim 1.000) |
| `81:8D18..81:8E62` | code | 331 | player-state-marshal | player1_marshal_and_sim_bridge | 81:8CF8..81:8E42 (-32; size 331; sim 0.822) | 81:8CF8..81:8E42 (-32; size 331; sim 0.692) | 81:8D18..81:8E62 (+0; size 331; sim 1.000) |
| `81:8E63..81:8FB7` | code | 341 | player-state-marshal | player2_marshal_and_sim_bridge | 81:8E43..81:8F97 (-32; size 341; sim 0.824) | 81:8E43..81:8F97 (-32; size 341; sim 0.692) | 81:8E63..81:8FB7 (+0; size 341; sim 1.000) |
| `81:8FB8..81:9303` | code | 844 | collision-resolution | resolver_prefix_before_europe_nops | 81:8F98..81:92E3 (-32; size 844; sim 0.922) | 81:8F98..81:92E3 (-32; size 844; sim 0.910) | 81:8FB8..81:9303 (+0; size 844; sim 1.000) |
| `81:9304..81:9483` | code | 384 | collision-resolution | resolver_live_a | 81:92E4..81:9463 (-32; size 384; sim 0.917) | 81:92EA..81:9469 (-26; size 384; sim 0.914) | 81:9304..81:9483 (+0; size 384; sim 1.000) |
| `81:9484..81:948A` | code | 7 | collision-resolution | resolver_usa_dormant_a | 81:9464..81:946A (-32; size 7; sim 1.000) | 81:946A..81:9470 (-26; size 7; sim 0.857) | 81:9484..81:948A (+0; size 7; sim 1.000) |
| `81:948B..81:9645` | code | 443 | collision-resolution | resolver_live_b | 81:946B..81:9625 (-32; size 443; sim 0.935) | 81:9471..81:962B (-26; size 443; sim 0.912) | 81:948B..81:9645 (+0; size 443; sim 1.000) |
| `81:9646..81:9669` | code | 36 | collision-resolution | resolver_usa_dormant_b | 81:9626..81:9649 (-32; size 36; sim 0.889) | 81:962C..81:964F (-26; size 36; sim 0.889) | 81:9646..81:9669 (+0; size 36; sim 1.000) |
| `81:966A..81:96AC` | code | 67 | collision-resolution | resolver_live_c | 81:964A..81:968C (-32; size 67; sim 0.821) | 81:9650..81:9692 (-26; size 67; sim 0.821) | 81:966A..81:96AC (+0; size 67; sim 1.000) |
| `81:96AD..81:96AF` | code | 3 | collision-resolution | resolver_usa_dormant_c | 81:968D..81:968F (-32; size 3; sim 0.667) | 81:9693..81:9695 (-26; size 3; sim 0.667) | 81:96AD..81:96AF (+0; size 3; sim 1.000) |
| `81:96B0..81:97FF` | code | 336 | collision-resolution | resolver_live_d | 81:9690..81:97DF (-32; size 336; sim 0.952) | 81:9696..81:97E5 (-26; size 336; sim 0.949) | 81:96B0..81:97FF (+0; size 336; sim 1.000) |
| `81:9800..81:983A` | code | 59 | collision-resolution | resolver_tail_after_europe_gate | 81:97E0..81:981A (-32; size 59; sim 0.966) | 81:97F1..81:982B (-15; size 59; sim 0.966) | 81:9800..81:983A (+0; size 59; sim 1.000) |
| `81:983B..81:9971` | code | 311 | collision-resolution | geometry_helper_live_prefix | 81:981B..81:9951 (-32; size 311; sim 0.987) | 81:982C..81:9962 (-15; size 311; sim 0.977) | 81:983B..81:9971 (+0; size 311; sim 1.000) |
| `81:9972..81:9978` | code | 7 | collision-resolution | geometry_helper_usa_dormant | 81:9952..81:9958 (-32; size 7; sim 1.000) | 81:9963..81:9969 (-15; size 7; sim 0.857) | 81:9972..81:9978 (+0; size 7; sim 1.000) |
| `81:9979..81:99D5` | code | 93 | collision-resolution | geometry_helper_live_tail | 81:9959..81:99B5 (-32; size 93; sim 0.968) | 81:996A..81:99C6 (-15; size 93; sim 0.968) | 81:9979..81:99D5 (+0; size 93; sim 1.000) |
| `81:99D6..81:99D9` | code | 4 | geometry-precompute | long_entry_wrapper | 81:99B6..81:99B9 (-32; size 4; sim 0.750) | 81:99C7..81:99CA (-15; size 4; sim 0.750) | 81:99D6..81:99D9 (+0; size 4; sim 1.000) |
| `81:99DA..81:9A19` | data | 64 | geometry-precompute | geometry_lookup_a | 81:99BA..81:99F9 (-32; size 64; sim 1.000) | 81:99CB..81:9A0A (-15; size 64; sim 1.000) | 81:99DA..81:9A19 (+0; size 64; sim 1.000) |
| `81:9A1A..81:9A59` | data | 64 | geometry-precompute | geometry_lookup_b | 81:99FA..81:9A39 (-32; size 64; sim 1.000) | 81:9A0B..81:9A4A (-15; size 64; sim 1.000) | 81:9A1A..81:9A59 (+0; size 64; sim 1.000) |
| `81:9A5A..81:9E29` | code | 976 | geometry-precompute | geometry_precompute_body | 81:9A3A..81:9E09 (-32; size 976; sim 0.982) | 81:9A4B..81:9E1A (-15; size 976; sim 0.947) | 81:9A5A..81:9E29 (+0; size 976; sim 1.000) |
| `81:9E2A..81:9E7C` | code | 83 | contact-geometry | angle_and_source_record_setup | 81:9E0A..81:9E5C (-32; size 83; sim 0.988) | 81:9E1B..81:9E6D (-15; size 83; sim 0.988) | 81:9E2A..81:9E7C (+0; size 83; sim 1.000) |
| `81:9E7D..81:9F1C` | code | 160 | contact-geometry | vertex_expansion_and_orientation | 81:9E5D..81:9EFC (-32; size 160; sim 1.000) | 81:9E6E..81:9F0D (-15; size 160; sim 1.000) | 81:9E7D..81:9F1C (+0; size 160; sim 1.000) |
| `81:9F1D..81:9FBE` | code | 162 | contact-geometry | mirror_offset_and_collision_anchor_finalize | 81:9EFD..81:9F9E (-32; size 162; sim 0.981) | 81:9F0E..81:9FAF (-15; size 162; sim 0.981) | 81:9F1D..81:9FBE (+0; size 162; sim 1.000) |
| `81:9FBF..81:A2E4` | code | 806 | camera-control | camera_velocity_follow_solver | 81:9F9F..81:A2C4 (-32; size 806; sim 0.996) | 81:9FB0..81:A2D5 (-15; size 806; sim 0.935) | 81:9FBF..81:A2E4 (+0; size 806; sim 1.000) |
| `81:A2E5..81:A30E` | code | 42 | camera-control | camera_smoothing_helper | 81:A2C5..81:A2EE (-32; size 42; sim 1.000) | 81:A2D6..81:A2FF (-15; size 42; sim 1.000) | 81:A2E5..81:A30E (+0; size 42; sim 1.000) |
| `81:A30F..81:A52A` | code | 540 | camera-control | camera_scale_config | 81:A2EF..81:A50A (-32; size 540; sim 0.963) | 81:A300..81:A51B (-15; size 540; sim 0.841) | 81:A30F..81:A52A (+0; size 540; sim 1.000) |
| `81:A52B..81:A59D` | code | 115 | camera-control | camera_update_wrapper | 81:A50B..81:A57D (-32; size 115; sim 0.965) | 81:A51C..81:A58E (-15; size 115; sim 0.800) | 81:A52B..81:A59D (+0; size 115; sim 1.000) |
| `81:B664..81:B667` | code | 4 | multiply-b668 | long_entry_wrapper | 81:B644..81:B647 (-32; size 4; sim 0.750) | 81:B655..81:B658 (-15; size 4; sim 0.750) | 81:B664..81:B667 (+0; size 4; sim 1.000) |
| `81:B668..81:B68A` | code | 35 | multiply-b668 | multiply_x_by_y | 81:B648..81:B66A (-32; size 35; sim 1.000) | 81:B659..81:B67B (-15; size 35; sim 1.000) | 81:B668..81:B68A (+0; size 35; sim 1.000) |
| `81:B6C0..81:B6C3` | code | 4 | geometry-math-helper | long_entry_wrapper | 81:B6A0..81:B6A3 (-32; size 4; sim 0.750) | 81:B6B1..81:B6B4 (-15; size 4; sim 0.750) | 81:B6C0..81:B6C3 (+0; size 4; sim 1.000) |
| `81:B6C4..81:B712` | code | 79 | geometry-math-helper | hardware_multiply_geometry_body | 81:B6A4..81:B6F2 (-32; size 79; sim 1.000) | 81:B6B5..81:B703 (-15; size 79; sim 1.000) | 81:B6C4..81:B712 (+0; size 79; sim 1.000) |
| `81:BEB3..81:BEB6` | code | 4 | race-message-bridge | long_entry_wrapper | 81:BE93..81:BE96 (-32; size 4; sim 0.750) | 81:BEA4..81:BEA7 (-15; size 4; sim 0.750) | 81:BEB3..81:BEB6 (+0; size 4; sim 1.000) |
| `81:BEB7..81:BF40` | code | 138 | race-message-bridge | race_message_dispatch | 81:BE97..81:BF20 (-32; size 138; sim 0.942) | 81:BEA8..81:BF31 (-15; size 138; sim 0.877) | 81:BEB7..81:BF40 (+0; size 138; sim 1.000) |
| `81:BF41..81:BFE2` | code | 162 | race-message-bridge | mirrored_commit_helper | 81:BF21..81:BFC2 (-32; size 162; sim 0.907) | 81:BF32..81:BFD3 (-15; size 162; sim 0.907) | 81:BF41..81:BFE2 (+0; size 162; sim 1.000) |
| `81:BFE3..81:C0DC` | code | 250 | race-message-bridge | mirrored_materialize_helper | 81:BFC3..81:C0BC (-32; size 250; sim 0.968) | 81:BFD4..81:C0CD (-15; size 250; sim 0.952) | 81:BFE3..81:C0DC (+0; size 250; sim 1.000) |
| `81:C0DD..81:C24A` | code | 366 | stunt-message-pipeline | message_consume_pre_cleanup | 81:C0BD..81:C22A (-32; size 366; sim 0.940) | 81:C0CE..81:C23B (-15; size 366; sim 0.915) | 81:C0DD..81:C24A (+0; size 366; sim 1.000) |
| `81:C24B..81:C24D` | code | 3 | stunt-message-pipeline | pal_line_removed_nops | — | — | 81:C24B..81:C24D (+0; size 3; sim 1.000) |
| `81:C24E..81:C368` | code | 283 | stunt-message-pipeline | message_consume_post_cleanup | 81:C22B..81:C345 (-35; size 283; sim 0.940) | 81:C23C..81:C356 (-18; size 283; sim 0.943) | 81:C24E..81:C368 (+0; size 283; sim 1.000) |
| `81:C369..81:C371` | code | 9 | stunt-message-pipeline | score_display_prefix | 81:C346..81:C34E (-35; size 9; sim 1.000) | 81:C357..81:C35F (-18; size 9; sim 1.000) | 81:C369..81:C371 (+0; size 9; sim 1.000) |
| `81:C372..81:C37E` | code | 13 | stunt-message-pipeline | score_display_usa_gate | 81:C34F..81:C35B (-35; size 13; sim 0.846) | — | 81:C372..81:C37E (+0; size 13; sim 1.000) |
| `81:C37F..81:C457` | code | 217 | stunt-message-pipeline | score_display_suffix | 81:C35C..81:C434 (-35; size 217; sim 0.871) | 81:C368..81:C440 (-23; size 217; sim 0.871) | 81:C37F..81:C457 (+0; size 217; sim 1.000) |
| `81:C458..81:C571` | data | 282 | stunt-message-pipeline | message_reward_lookup_block | 81:C435..81:C54E (-35; size 282; sim 1.000) | 81:C441..81:C55A (-23; size 282; sim 1.000) | 81:C458..81:C571 (+0; size 282; sim 1.000) |
| `81:C572..81:C604` | code | 147 | stunt-message-pipeline | queue_long_entry_and_helpers | 81:C54F..81:C5E1 (-35; size 147; sim 0.959) | 81:C55B..81:C5ED (-23; size 147; sim 0.810) | 81:C572..81:C604 (+0; size 147; sim 1.000) |
| `81:C697..81:C6A3` | code | 13 | race-timer | long_entry_and_dispatch_live | 81:C674..81:C680 (-35; size 13; sim 0.769) | 81:C684..81:C690 (-19; size 13; sim 0.769) | 81:C697..81:C6A3 (+0; size 13; sim 1.000) |
| `81:C6A4..81:C6A6` | code | 3 | race-timer | dormant_cb37_call | 81:C681..81:C683 (-35; size 3; sim 0.667) | 81:C691..81:C693 (-19; size 3; sim 0.667) | 81:C6A4..81:C6A6 (+0; size 3; sim 1.000) |
| `81:C6A7..81:C6D2` | code | 44 | race-timer | mode_dispatch_tail | 81:C684..81:C6AF (-35; size 44; sim 0.795) | 81:C694..81:C6BF (-19; size 44; sim 0.773) | 81:C6A7..81:C6D2 (+0; size 44; sim 1.000) |
| `81:C6D3..81:C7E0` | code | 270 | race-timer | count_up_timer | 81:C6B0..81:C7BD (-35; size 270; sim 0.844) | 81:C6C0..81:C7CD (-19; size 270; sim 0.815) | 81:C6D3..81:C7E0 (+0; size 270; sim 1.000) |
| `81:C7E1..81:C906` | code | 294 | race-timer | stunt_countdown_timer | 81:C7BE..81:C8E3 (-35; size 294; sim 0.850) | 81:C7CE..81:C8F3 (-19; size 294; sim 0.806) | 81:C7E1..81:C906 (+0; size 294; sim 1.000) |
| `82:980D..82:9810` | code | 4 | race-state-980d | long_entry_wrapper | 82:9808..82:980B (-5; size 4; sim 0.750) | 82:981E..82:9821 (+17; size 4; sim 0.750) | 82:980D..82:9810 (+0; size 4; sim 1.000) |
| `82:9811..82:98BD` | code | 173 | race-state-980d | mirrored_state_bridge | 82:980C..82:98B8 (-5; size 173; sim 0.896) | 82:9822..82:98CE (+17; size 173; sim 0.890) | 82:9811..82:98BD (+0; size 173; sim 1.000) |
| `82:9A42..82:9B57` | code | 278 | stunt-finalizer | air_state_and_rotation_progress | 82:9A3D..82:9B52 (-5; size 278; sim 0.856) | 82:9A53..82:9B68 (+17; size 278; sim 0.842) | 82:9A42..82:9B57 (+0; size 278; sim 1.000) |
| `82:9B58..82:9C97` | code | 320 | stunt-finalizer | landing_trick_classification | 82:9B53..82:9C92 (-5; size 320; sim 0.919) | 82:9B69..82:9CA8 (+17; size 320; sim 0.881) | 82:9B58..82:9C97 (+0; size 320; sim 1.000) |
| `82:9C98..82:9D08` | code | 113 | stunt-finalizer | score_index_and_message_prefix | 82:9C93..82:9D03 (-5; size 113; sim 0.903) | 82:9CA9..82:9D19 (+17; size 113; sim 0.903) | 82:9C98..82:9D08 (+0; size 113; sim 1.000) |
| `82:9D09..82:9D0D` | code | 5 | stunt-finalizer | pal_line_removed_nops | — | — | 82:9D09..82:9D0D (+0; size 5; sim 1.000) |
| `82:9D0E..82:9D67` | code | 90 | stunt-finalizer | praise_select_emit | 82:9D04..82:9D5D (-10; size 90; sim 0.922) | 82:9D1A..82:9D73 (+12; size 90; sim 0.922) | 82:9D0E..82:9D67 (+0; size 90; sim 1.000) |
| `82:9D68..82:9D8B` | code | 36 | stunt-finalizer | state_clear_and_exit | 82:9D5E..82:9D81 (-10; size 36; sim 0.750) | 82:9D74..82:9D97 (+12; size 36; sim 0.667) | 82:9D68..82:9D8B (+0; size 36; sim 1.000) |
| `82:9D8C..82:9D95` | data | 10 | stunt-finalizer | flip_score_weights | 82:9D82..82:9D8B (-10; size 10; sim 1.000) | 82:9D98..82:9DA1 (+12; size 10; sim 1.000) | 82:9D8C..82:9D95 (+0; size 10; sim 1.000) |
| `82:9D96..82:9D9F` | data | 10 | stunt-finalizer | roll_score_weights | 82:9D8C..82:9D95 (-10; size 10; sim 1.000) | 82:9DA2..82:9DAB (+12; size 10; sim 1.000) | 82:9D96..82:9D9F (+0; size 10; sim 1.000) |
| `82:9DA0..82:9DA9` | data | 10 | stunt-finalizer | twist_score_weights | 82:9D96..82:9D9F (-10; size 10; sim 1.000) | 82:9DAC..82:9DB5 (+12; size 10; sim 1.000) | 82:9DA0..82:9DA9 (+0; size 10; sim 1.000) |
| `82:9DAA..82:A01A` | data | 625 | stunt-finalizer | trick_praise_table | 82:9DA0..82:A010 (-10; size 625; sim 1.000) | 82:9DB6..82:A026 (+12; size 625; sim 1.000) | 82:9DAA..82:A01A (+0; size 625; sim 1.000) |
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
| `82:AA6E..82:AB54` | code | 231 | input-normalization | player1_decode_and_fallback | 82:AA5F..82:AB45 (-15; size 231; sim 0.991) | 82:AA75..82:AB5B (+7; size 231; sim 0.848) | 82:AA6E..82:AB54 (+0; size 231; sim 1.000) |
| `82:AB55..82:AC52` | code | 254 | input-normalization | player2_decode_and_activity | 82:AB46..82:AC43 (-15; size 254; sim 0.988) | 82:AB5C..82:AC59 (+7; size 254; sim 0.850) | 82:AB55..82:AC52 (+0; size 254; sim 1.000) |
| `82:AC53..82:ACA0` | code | 78 | input-normalization | reverse_controls_remap | 82:AC44..82:AC91 (-15; size 78; sim 0.987) | 82:AC5A..82:ACA7 (+7; size 78; sim 0.731) | 82:AC53..82:ACA0 (+0; size 78; sim 1.000) |
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
| `82:B293..82:B2A8` | code | 22 | course-resource-descriptor | stream_byte_reader | 82:B280..82:B295 (-19; size 22; sim 1.000) | 82:B296..82:B2AB (+3; size 22; sim 1.000) | 82:B293..82:B2A8 (+0; size 22; sim 1.000) |
| `82:B2A9..82:B2AC` | code | 4 | course-resource-descriptor | descriptor_long_entry | 82:B296..82:B299 (-19; size 4; sim 0.750) | 82:B2AC..82:B2AF (+3; size 4; sim 0.750) | 82:B2A9..82:B2AC (+0; size 4; sim 1.000) |
| `82:B2AD..82:B2D9` | code | 45 | course-resource-descriptor | descriptor_decode | 82:B29A..82:B2C6 (-19; size 45; sim 1.000) | 82:B2B0..82:B2DC (+3; size 45; sim 1.000) | 82:B2AD..82:B2D9 (+0; size 45; sim 1.000) |
| `82:B2DA..82:B32E` | code | 85 | course-resource-descriptor | wram_port_copy | 82:B2C7..82:B31B (-19; size 85; sim 0.965) | 82:B2DD..82:B331 (+3; size 85; sim 0.965) | 82:B2DA..82:B32E (+0; size 85; sim 1.000) |
| `82:E165..82:E1CF` | code | 107 | course-materialization | setup | 82:E101..82:E16B (-100; size 107; sim 0.944) | 82:E12B..82:E195 (-58; size 107; sim 0.944) | 82:E165..82:E1CF (+0; size 107; sim 1.000) |
| `82:E1D1..82:E213` | code | 67 | course-materialization | resource_record_header | 82:E16D..82:E1AF (-100; size 67; sim 0.896) | 82:E197..82:E1D9 (-58; size 67; sim 0.896) | 82:E1D1..82:E213 (+0; size 67; sim 1.000) |
| `82:E216..82:E2FF` | code | 234 | course-materialization | dma_row_loop | 82:E1B2..82:E29B (-100; size 234; sim 0.885) | 82:E1DC..82:E2C5 (-58; size 234; sim 0.885) | 82:E216..82:E2FF (+0; size 234; sim 1.000) |
| `82:E302..82:E385` | code | 132 | course-materialization | resource_materialize_A000_C000 | 82:E29E..82:E321 (-100; size 132; sim 0.955) | 82:E2C8..82:E34B (-58; size 132; sim 0.955) | 82:E302..82:E385 (+0; size 132; sim 1.000) |
| `82:E388..82:E395` | code | 14 | course-materialization | exit | 82:E324..82:E331 (-100; size 14; sim 0.929) | 82:E34E..82:E35B (-58; size 14; sim 0.929) | 82:E388..82:E395 (+0; size 14; sim 1.000) |
| `83:CBCC..83:CC86` | code | 187 | race-frame-orchestrator | setup_loop_prefix | 83:CBCC..83:CC84 (+0; size 185; sim 0.882) | 83:CBF2..83:CCAA (+38; size 185; sim 0.872) | 83:CBCC..83:CC86 (+0; size 187; sim 1.000) |
| `83:CC87..83:CD9F` | code | 281 | race-frame-orchestrator | loop_body_after_sep_cleanup | 83:CC85..83:CD9D (-2; size 281; sim 0.833) | 83:CCAB..83:CDC3 (+36; size 281; sim 0.790) | 83:CC87..83:CD9F (+0; size 281; sim 1.000) |
| `83:E066..83:E237` | code | 466 | race-control-state | race_control_state_primary | 83:E05C..83:E22D (-10; size 466; sim 0.916) | 83:E082..83:E253 (+28; size 466; sim 0.830) | 83:E066..83:E237 (+0; size 466; sim 1.000) |
| `83:E238..83:E53F` | code | 776 | race-control-state | race_control_state_companion | 83:E22E..83:E535 (-10; size 776; sim 0.927) | 83:E254..83:E55B (+28; size 776; sim 0.807) | 83:E238..83:E53F (+0; size 776; sim 1.000) |
| `83:E540..83:E57F` | data | 64 | race-loop-e580-control | race_control_lookup | 83:E536..83:E575 (-10; size 64; sim 1.000) | 83:E55C..83:E59B (+28; size 64; sim 1.000) | 83:E540..83:E57F (+0; size 64; sim 1.000) |
| `83:E580..83:E7A4` | code | 549 | race-loop-e580-control | race_loop_control | 83:E576..83:E79A (-10; size 549; sim 0.869) | 83:E59C..83:E7C0 (+28; size 549; sim 0.836) | 83:E580..83:E7A4 (+0; size 549; sim 1.000) |
| `83:E7A5..83:EBCB` | code | 1063 | race-loop-e7a5 | race_loop_e7a5_body | 83:E79B..83:EBEF (-10->+36; size 1109; sim 0.846) | 83:E7C1..83:EC13 (+28->+72; size 1107; sim 0.786) | 83:E7A5..83:EBCB (+0; size 1063; sim 1.000) |
| `83:EBE6..83:EC45` | data | 96 | ec46-coordinate-window | coordinate_step_table | 83:EC0A..83:EC69 (+36; size 96; sim 1.000) | 83:EC2E..83:EC8D (+72; size 96; sim 1.000) | 83:EBE6..83:EC45 (+0; size 96; sim 1.000) |
| `83:EC46..83:ED2E` | code | 233 | ec46-coordinate-window | coordinate_window_update | 83:EC6A..83:ED52 (+36; size 233; sim 0.983) | 83:EC8E..83:ED76 (+72; size 233; sim 0.880) | 83:EC46..83:ED2E (+0; size 233; sim 1.000) |

## Selection rule for the next island

Grow this census by choosing a different executed/high-connectivity subsystem where comparative evidence can recover multiple boundaries or relationships at once. Prefer a candidate with direct call/table structure and shipping relevance. Do not extend an existing island merely to increase byte totals.

The JSON form is the authoritative query surface: `analysis/generated/comparative-structural-census.json`.
