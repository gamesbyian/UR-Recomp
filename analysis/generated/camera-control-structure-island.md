# Race camera-control structural island

USA `81:9FBF..A59D` covers the camera target-velocity/follow solver, shared smoothing helper, zoom/scale configuration, and the per-frame camera update wrapper at `81:A52B/A52F`.

All 1,503 USA bytes are executable. USA and legacy beta are byte-identical. PAL prototype remains at shift -32 and Europe at -15 across the full cluster. Across all four regions, both regional builds preserve 659/659 aligned opcode positions with zero role disagreements; lower raw similarity is operand/data relocation rather than changed camera control flow.

| Region | USA bytes | PAL prototype | Europe | Legacy beta |
|---|---:|---|---|---|
| camera_velocity_follow_solver | 806 | 81:9F9F..81:A2C4 (-32; sim 0.996; op 390; other 0) | 81:9FB0..81:A2D5 (-15; sim 0.935; op 390; other 0) | 81:9FBF..81:A2E4 (+0; sim 1.000; op 390; other 0) |
| camera_smoothing_helper | 42 | 81:A2C5..81:A2EE (-32; sim 1.000; op 28; other 0) | 81:A2D6..81:A2FF (-15; sim 1.000; op 28; other 0) | 81:A2E5..81:A30E (+0; sim 1.000; op 28; other 0) |
| camera_scale_config | 540 | 81:A2EF..81:A50A (-32; sim 0.963; op 188; other 0) | 81:A300..81:A51B (-15; sim 0.841; op 188; other 0) | 81:A30F..81:A52A (+0; sim 1.000; op 188; other 0) |
| camera_update_wrapper | 115 | 81:A50B..81:A57D (-32; sim 0.965; op 53; other 0) | 81:A51C..81:A58E (-15; sim 0.800; op 53; other 0) | 81:A52B..81:A59D (+0; sim 1.000; op 53; other 0) |

The old Nitrodon listing's apparent BRK/COP clutter inside the velocity solver is width/context drift: trusted-entry tracing reaches the entire region as ordinary executable code.
