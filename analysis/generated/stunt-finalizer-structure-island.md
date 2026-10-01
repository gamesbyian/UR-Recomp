# Stunt finalization/scoring structural island

USA code begins at 82:9A42 and returns at 82:9D8B. Three compact score-weight tables and the 625-byte trick/praise lookup continue through 82:A01A; the next USA code begins at 82:A01B.

| Region | Kind | USA bytes | PAL prototype | Europe | Legacy beta |
|---|---|---:|---|---|---|
| air_state_and_rotation_progress | code | 278 | 82:9A3D..82:9B52 (-5; sim 0.856; op 117; other 0) | 82:9A53..82:9B68 (+17; sim 0.842; op 117; other 0) | 82:9A42..82:9B57 (+0; sim 1.000; op 117; other 0) |
| landing_trick_classification | code | 320 | 82:9B53..82:9C92 (-5; sim 0.919; op 134; other 0) | 82:9B69..82:9CA8 (+17; sim 0.881; op 134; other 0) | 82:9B58..82:9C97 (+0; sim 1.000; op 134; other 0) |
| score_index_and_message_prefix | code | 113 | 82:9C93..82:9D03 (-5; sim 0.903; op 44; other 0) | 82:9CA9..82:9D19 (+17; sim 0.903; op 44; other 0) | 82:9C98..82:9D08 (+0; sim 1.000; op 44; other 0) |
| pal_line_removed_nops | code | 5 | none | none | 82:9D09..82:9D0D (+0; sim 1.000; op 5; other 0) |
| praise_select_emit | code | 90 | 82:9D04..82:9D5D (-10; sim 0.922; op 37; other 0) | 82:9D1A..82:9D73 (+12; sim 0.922; op 37; other 0) | 82:9D0E..82:9D67 (+0; sim 1.000; op 37; other 0) |
| state_clear_and_exit | code | 36 | 82:9D5E..82:9D81 (-10; sim 0.750; op 13; other 0) | 82:9D74..82:9D97 (+12; sim 0.667; op 13; other 0) | 82:9D68..82:9D8B (+0; sim 1.000; op 13; other 0) |
| flip_score_weights | data | 10 | 82:9D82..82:9D8B (-10; sim 1.000; op 0; other 10) | 82:9D98..82:9DA1 (+12; sim 1.000; op 0; other 10) | 82:9D8C..82:9D95 (+0; sim 1.000; op 0; other 10) |
| roll_score_weights | data | 10 | 82:9D8C..82:9D95 (-10; sim 1.000; op 0; other 10) | 82:9DA2..82:9DAB (+12; sim 1.000; op 0; other 10) | 82:9D96..82:9D9F (+0; sim 1.000; op 0; other 10) |
| twist_score_weights | data | 10 | 82:9D96..82:9D9F (-10; sim 1.000; op 0; other 10) | 82:9DAC..82:9DB5 (+12; sim 1.000; op 0; other 10) | 82:9DA0..82:9DA9 (+0; sim 1.000; op 0; other 10) |
| trick_praise_table | data | 625 | 82:9DA0..82:A010 (-10; sim 1.000; op 0; other 625) | 82:9DB6..82:A026 (+12; sim 1.000; op 0; other 625) | 82:9DAA..82:A01A (+0; sim 1.000; op 0; other 625) |

## Lineage edit

- 82:9D09..9D0D (5 bytes): NOP; NOP; NOP; NOP; NOP.
- USA/beta retain the five NOPs. PAL prototype and Europe omit them, changing the prototype shift -5 to -10 and Europe +17 to +12.
- All three score-weight tables and the 625-byte trick/praise table are byte-identical across all four builds after this shift.
