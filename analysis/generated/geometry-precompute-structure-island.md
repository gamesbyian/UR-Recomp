# Geometry precompute structural island

USA `81:99D6..9E29` contains a long-entry wrapper, two adjacent 64-byte lookup tables, and the geometry-precompute body before the next independent entry at `81:9E2A`. The wrapper and body are fully analyzer-reached; both lookup tables are byte-identical across all four preserved ROMs.

| Region | Kind | USA bytes | PAL prototype | Europe | Legacy beta |
|---|---|---:|---|---|---|
| long_entry_wrapper | code | 4 | 81:99B6..81:99B9 (-32; sim 0.750; op 2; other 0) | 81:99C7..81:99CA (-15; sim 0.750; op 2; other 0) | 81:99D6..81:99D9 (+0; sim 1.000; op 2; other 0) |
| geometry_lookup_a | data | 64 | 81:99BA..81:99F9 (-32; sim 1.000; op 0; other 64) | 81:99CB..81:9A0A (-15; sim 1.000; op 0; other 64) | 81:99DA..81:9A19 (+0; sim 1.000; op 0; other 64) |
| geometry_lookup_b | data | 64 | 81:99FA..81:9A39 (-32; sim 1.000; op 0; other 64) | 81:9A0B..81:9A4A (-15; sim 1.000; op 0; other 64) | 81:9A1A..81:9A59 (+0; sim 1.000; op 0; other 64) |
| geometry_precompute_body | code | 976 | 81:9A3A..81:9E09 (-32; sim 0.982; op 452; other 0) | 81:9A4B..81:9E1A (-15; sim 0.947; op 452; other 0) | 81:9A5A..81:9E29 (+0; sim 1.000; op 452; other 0) |

## Lookup-table identity

- europe-retail: byte-identical to USA
- legacy-beta: byte-identical to USA
- pal-prototype-1994-11-29: byte-identical to USA
- usa-retail: byte-identical to USA

Across the two code regions, PAL prototype and Europe preserve every aligned opcode position and analyzer code/operand role. Their byte differences are therefore operand/layout differences rather than executable-architecture changes.
