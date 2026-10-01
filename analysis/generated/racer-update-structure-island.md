# Racer-update structural island: A22B..A497

This report recovers structure, not semantic names. Boundaries are anchored by direct calls from the racer-frame update hub and explicit RTS instructions.

| Region | Kind | Size | USA | PAL prototype | Europe | Legacy beta |
|---|---|---:|---|---|---|---|
| routine_A22B | code | 81 | 82:A22B..82:A27B (+0, sim 1.000; op 31, data/unreached 0) | 82:A221..82:A271 (-10, sim 0.852; op 31, data/unreached 0) | 82:A237..82:A287 (+12, sim 0.852; op 31, data/unreached 0) | 82:A22B..82:A27B (+0, sim 1.000; op 31, data/unreached 0) |
| routine_A27C | code | 88 | 82:A27C..82:A2D3 (+0, sim 1.000; op 38, data/unreached 0) | 82:A272..82:A2C9 (-10, sim 0.511; op 33, data/unreached 5) | 82:A288..82:A2DF (+12, sim 0.511; op 33, data/unreached 5) | 82:A27C..82:A2D3 (+0, sim 1.000; op 38, data/unreached 0) |
| table_A2D4 | data | 128 | 82:A2D4..82:A353 (+0, sim 1.000; op 0, data/unreached 128) | 82:A2C5..82:A344 (-15, sim 1.000; op 0, data/unreached 128) | 82:A2DB..82:A35A (+7, sim 1.000; op 0, data/unreached 128) | 82:A2D4..82:A353 (+0, sim 1.000; op 0, data/unreached 128) |
| routine_A354 | code | 324 | 82:A354..82:A497 (+0, sim 1.000; op 120, data/unreached 13) | 82:A345..82:A488 (-15, sim 0.821; op 120, data/unreached 13) | 82:A35B..82:A49E (+7, sim 0.815; op 120, data/unreached 13) | 82:A354..82:A497 (+0, sim 1.000; op 120, data/unreached 13) |

## Inline table

- Exact size: **128 bytes / 64 little-endian words**.
- It begins immediately after the A27C routine RTS and ends immediately before the independently called A354 entry.
- The following routine performs a long indexed load from USA 82:A2D4,X, independently proving this block is lookup data rather than executable code.
- USA words: 0000 0000 0010 0010 0020 0020 0030 0030 0040 0040 0050 0050 0060 0060 0070 0070 0080 0080 0090 0090 00A0 00A0 00B0 00B0 00C0 00C0 00D0 00D0 00E0 00E0 00F0 00F0 0100 0100 0110 0110 0120 0120 0130 0130 0140 0140 0160 0160 0170 0170 0180 0180 0190 0190 01A0 01A0 01B0 01B0 01C0 01C0 01D0 01D0 01E0 01E0 01F0 01F0 0000 0000
