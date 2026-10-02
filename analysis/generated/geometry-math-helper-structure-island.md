# Geometry hardware-multiply helper structural island

USA `81:B6C0..B712` is a long-entry wrapper plus the shared geometry math body called eight times by the recovered geometry-precompute island. The body uses the SNES hardware multiply registers `$211B/$211C` and reads `$2135/$2136`; `81:B713` begins a separate routine.

| Region | USA bytes | PAL prototype | Europe | Legacy beta |
|---|---:|---|---|---|
| long_entry_wrapper | 4 | 81:B6A0..81:B6A3 (-32; sim 0.750; op 2; other 0) | 81:B6B1..81:B6B4 (-15; sim 0.750; op 2; other 0) | 81:B6C0..81:B6C3 (+0; sim 1.000; op 2; other 0) |
| hardware_multiply_geometry_body | 79 | 81:B6A4..81:B6F2 (-32; sim 1.000; op 35; other 0) | 81:B6B5..81:B703 (-15; sim 1.000; op 35; other 0) | 81:B6C4..81:B712 (+0; sim 1.000; op 35; other 0) |

## Accepted callers

- 81:9C92 from geometry-precompute
- 81:9CAE from geometry-precompute
- 81:9CDC from geometry-precompute
- 81:9CF8 from geometry-precompute
- 81:9D33 from geometry-precompute
- 81:9D43 from geometry-precompute
- 81:9D71 from geometry-precompute
- 81:9D81 from geometry-precompute

The 79-byte body is byte-identical across all four preserved ROMs. Only the 4-byte long-entry wrapper call operand relocates with the surrounding bank-81 layout.
