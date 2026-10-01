# Per-racer contact-geometry structural island

USA `81:9E2A..9FBE` is called independently for P1 and P2 from the persistent-state marshal, before the course-surface sampler and collision resolver. It derives orientation-dependent contact geometry and writes the active-player collision anchor at `125B,Y`. Camera control begins immediately at `81:9FBF`.

All 405 USA bytes are executable. USA and legacy beta are byte-identical. PAL prototype preserves the routine at constant shift -32; Europe preserves it at constant shift -15. Both regional builds match all 246 aligned opcode positions with zero code/operand-role disagreements.

| Region | USA bytes | PAL prototype | Europe | Legacy beta |
|---|---:|---|---|---|
| angle_and_source_record_setup | 83 | 81:9E0A..81:9E5C (-32; sim 0.988; op 48; other 0) | 81:9E1B..81:9E6D (-15; sim 0.988; op 48; other 0) | 81:9E2A..81:9E7C (+0; sim 1.000; op 48; other 0) |
| vertex_expansion_and_orientation | 160 | 81:9E5D..81:9EFC (-32; sim 1.000; op 107; other 0) | 81:9E6E..81:9F0D (-15; sim 1.000; op 107; other 0) | 81:9E7D..81:9F1C (+0; sim 1.000; op 107; other 0) |
| mirror_offset_and_collision_anchor_finalize | 162 | 81:9EFD..81:9F9E (-32; sim 0.981; op 91; other 0) | 81:9F0E..81:9FAF (-15; sim 0.981; op 91; other 0) | 81:9F1D..81:9FBE (+0; sim 1.000; op 91; other 0) |

The routine is the structural bridge from shared current-player orientation/state to the course-surface sampler and collision resolver. Regional collision lineage edits therefore occur downstream of this constructor, not in contact-geometry generation.
