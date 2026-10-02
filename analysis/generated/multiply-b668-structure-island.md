# 81:B668 multiply helper structural island

USA 81:B664..B68A is a compact generic arithmetic island: a long-entry wrapper followed by a shift-and-add multiply helper. The helper is called from the recovered camera-control subsystem and is bounded before the distinct B68B helper.

| Region | Bytes | PAL prototype | Europe | Legacy beta |
|---|---:|---|---|---|
| long_entry_wrapper | 4 | 81:B644..81:B647 (-32; sim 0.750; op 2; other 0) | 81:B655..81:B658 (-15; sim 0.750; op 2; other 0) | 81:B664..81:B667 (+0; sim 1.000; op 2; other 0) |
| multiply_x_by_y | 35 | 81:B648..81:B66A (-32; sim 1.000; op 19; other 0) | 81:B659..81:B67B (-15; sim 1.000; op 19; other 0) | 81:B668..81:B68A (+0; sim 1.000; op 19; other 0) |

## Accepted-census callers

- 81:A511 JSR -> 81:B668 from camera-control / camera_scale_config

Semantics are unusually strong here: the routine orders X/Y so the smaller operand drives the bit loop, accumulates shifted copies of the larger operand, and returns the product in X.
