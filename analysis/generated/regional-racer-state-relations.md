# Regional racer-state copy relations

A relation is promoted only when the matched racer-update routine contains both a persistent→working copy and a working→persistent copy for the proposed build-specific addresses.

| Build | Semantic field | Persistent | Working | Copy in | Copy out | Bidirectional |
|---|---|---|---|---:|---:|---|
| usa-retail | Player1_XSpeed | `7E:04B7` | `7E:0F9F` | 1 | 1 | yes |
| usa-retail | Player1_YSpeed | `7E:04BB` | `7E:0FA1` | 1 | 1 | yes |
| usa-retail | Player1_BoostMeter | `7E:11CF` | `7E:11CD` | 1 | 1 | yes |
| pal-prototype-1994-11-29 | Player1_XSpeed | `7E:04B7` | `7E:0FA3` | 1 | 1 | yes |
| pal-prototype-1994-11-29 | Player1_YSpeed | `7E:04BB` | `7E:0FA5` | 1 | 1 | yes |
| pal-prototype-1994-11-29 | Player1_BoostMeter | `7E:11D3` | `7E:11D1` | 1 | 1 | yes |
| europe-retail | Player1_XSpeed | `7E:04BB` | `7E:0FA9` | 1 | 1 | yes |
| europe-retail | Player1_YSpeed | `7E:04BF` | `7E:0FAB` | 1 | 1 | yes |
| europe-retail | Player1_BoostMeter | `7E:11D9` | `7E:11D7` | 1 | 1 | yes |

Exact instruction edges are stronger evidence than same-offset operand projection: they preserve the named field’s role in the marshal→simulate→writeback pipeline.
