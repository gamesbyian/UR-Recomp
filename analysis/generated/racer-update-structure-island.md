# Racer-update structural island: A22B..A497

This report recovers structure, not semantic names. Boundaries are anchored by direct calls from the racer-frame update hub and explicit RTS instructions.

| Region | Kind | Size | USA | PAL prototype | Europe | Legacy beta |
|---|---|---:|---|---|---|---|
| routine_A22B | code | 81 | 82:A22B..82:A27B (+0, sim 1.000; op 31, data/unreached 0) | 82:A221..82:A271 (-10, sim 0.852; op 31, data/unreached 0) | 82:A237..82:A287 (+12, sim 0.852; op 31, data/unreached 0) | 82:A22B..82:A27B (+0, sim 1.000; op 31, data/unreached 0) |
| routine_A27C | code | 88 | 82:A27C..82:A2D3 (+0, sim 1.000; op 38, data/unreached 0) | 82:A272..82:A2C9 (-10, sim 0.511; op 33, data/unreached 5) | 82:A288..82:A2DF (+12, sim 0.511; op 33, data/unreached 5) | 82:A27C..82:A2D3 (+0, sim 1.000; op 38, data/unreached 0) |
| table_A2D4 | data | 128 | 82:A2D4..82:A353 (+0, sim 1.000; op 0, data/unreached 128) | 82:A2C5..82:A344 (-15, sim 1.000; op 0, data/unreached 128) | 82:A2DB..82:A35A (+7, sim 1.000; op 0, data/unreached 128) | 82:A2D4..82:A353 (+0, sim 1.000; op 0, data/unreached 128) |
| routine_A354 | code | 324 | 82:A354..82:A497 (+0, sim 1.000; op 120, data/unreached 13) | 82:A345..82:A488 (-15, sim 0.821; op 120, data/unreached 13) | 82:A35B..82:A49E (+7, sim 0.815; op 120, data/unreached 13) | 82:A354..82:A497 (+0, sim 1.000; op 120, data/unreached 13) |
| routine_A498 | code | 347 | 82:A498..82:A5F2 (+0, sim 1.000; op 128, data/unreached 0) | 82:A489..82:A5E3 (-15, sim 0.873; op 128, data/unreached 0) | 82:A49F..82:A5F9 (+7, sim 0.833; op 128, data/unreached 0) | 82:A498..82:A5F2 (+0, sim 1.000; op 128, data/unreached 0) |
| routine_A5F3 | code | 37 | 82:A5F3..82:A617 (+0, sim 1.000; op 17, data/unreached 0) | 82:A5E4..82:A608 (-15, sim 0.892; op 17, data/unreached 0) | 82:A5FA..82:A61E (+7, sim 0.892; op 17, data/unreached 0) | 82:A5F3..82:A617 (+0, sim 1.000; op 17, data/unreached 0) |
| routine_A618 | code | 217 | 82:A618..82:A6F0 (+0, sim 1.000; op 114, data/unreached 0) | 82:A609..82:A6E1 (-15, sim 0.954; op 114, data/unreached 0) | 82:A61F..82:A6F7 (+7, sim 0.889; op 114, data/unreached 0) | 82:A618..82:A6F0 (+0, sim 1.000; op 114, data/unreached 0) |
| routine_A6F1 | code | 465 | 82:A6F1..82:A8C1 (+0, sim 1.000; op 193, data/unreached 18) | 82:A6E2..82:A8B2 (-15, sim 0.888; op 193, data/unreached 18) | 82:A6F8..82:A8C8 (+7, sim 0.873; op 193, data/unreached 18) | 82:A6F1..82:A8C1 (+0, sim 1.000; op 193, data/unreached 18) |
| routine_A8C2 | code | 166 | 82:A8C2..82:A967 (+0, sim 1.000; op 67, data/unreached 0) | 82:A8B3..82:A958 (-15, sim 0.837; op 67, data/unreached 0) | 82:A8C9..82:A96E (+7, sim 0.831; op 67, data/unreached 0) | 82:A8C2..82:A967 (+0, sim 1.000; op 67, data/unreached 0) |
| Player_ApplyVerticalAcceleration | code | 68 | 82:A968..82:A9AB (+0, sim 1.000; op 34, data/unreached 0) | 82:A959..82:A99C (-15, sim 0.912; op 34, data/unreached 0) | 82:A96F..82:A9B2 (+7, sim 0.897; op 34, data/unreached 0) | 82:A968..82:A9AB (+0, sim 1.000; op 34, data/unreached 0) |
| routine_A9AC | code | 93 | 82:A9AC..82:AA08 (+0, sim 1.000; op 42, data/unreached 0) | 82:A99D..82:A9F9 (-15, sim 0.882; op 42, data/unreached 0) | 82:A9B3..82:AA0F (+7, sim 0.871; op 42, data/unreached 0) | 82:A9AC..82:AA08 (+0, sim 1.000; op 42, data/unreached 0) |
| routine_AA09 | code | 97 | 82:AA09..82:AA69 (+0, sim 1.000; op 44, data/unreached 0) | 82:A9FA..82:AA5A (-15, sim 0.887; op 44, data/unreached 0) | 82:AA10..82:AA70 (+7, sim 0.876; op 44, data/unreached 0) | 82:AA09..82:AA69 (+0, sim 1.000; op 44, data/unreached 0) |
| Input_LongEntryWrapper | code | 4 | 82:AA6A..82:AA6D (+0, sim 1.000; op 2, data/unreached 0) | 82:AA5B..82:AA5E (-15, sim 0.750; op 2, data/unreached 0) | 82:AA71..82:AA74 (+7, sim 0.750; op 2, data/unreached 0) | 82:AA6A..82:AA6D (+0, sim 1.000; op 2, data/unreached 0) |

## Inline table

- Exact size: **128 bytes / 64 little-endian words**.
- It begins immediately after the A27C routine RTS and ends immediately before the independently called A354 entry.
- The following routine performs a long indexed load from USA 82:A2D4,X, independently proving this block is lookup data rather than executable code.
- USA words: 0000 0000 0010 0010 0020 0020 0030 0030 0040 0040 0050 0050 0060 0060 0070 0070 0080 0080 0090 0090 00A0 00A0 00B0 00B0 00C0 00C0 00D0 00D0 00E0 00E0 00F0 00F0 0100 0100 0110 0110 0120 0120 0130 0130 0140 0140 0160 0160 0170 0170 0180 0180 0190 0190 01A0 01A0 01B0 01B0 01C0 01C0 01D0 01D0 01E0 01E0 01F0 01F0 0000 0000
