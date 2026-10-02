# 83:EC46 coordinate/window structural island

USA 83:EBE6..ED2E contains a 48-word step table followed by the direct race-frame target at 83:EC46. The code updates mirrored outputs at $0D3F/$0D41 from paired state/selector inputs and returns at 83:ED2E; 83:ED2F begins a separate long-entry wrapper and is excluded.

| Region | Kind | Bytes | PAL prototype | Europe | Legacy beta |
|---|---|---:|---|---|---|
| coordinate_step_table | data | 96 | 83:EC0A..83:EC69 (+36; sim 1.000; op 0; other 96) | 83:EC2E..83:EC8D (+72; sim 1.000; op 0; other 96) | 83:EBE6..83:EC45 (+0; sim 1.000; op 0; other 96) |
| coordinate_window_update | code | 233 | 83:EC6A..83:ED52 (+36; sim 0.983; op 107; other 0) | 83:EC8E..83:ED76 (+72; sim 0.880; op 107; other 0) | 83:EC46..83:ED2E (+0; sim 1.000; op 107; other 0) |

## Accepted-census caller

- 83:CD52 JSR -> 83:EC46 from race-frame-orchestrator / loop_body_after_sep_cleanup

The semantic label is intentionally conservative. The paired outputs behave like coordinate/window positions, but higher-level gameplay meaning is not asserted here.
