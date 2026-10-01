# Cross-build semantic symbol correspondence

This surface joins named USA semantics to the strongest currently available PAL prototype and Europe retail structural correspondences. It is intended for debugging, decompilation, runtime probes, and future regional fidelity work.

A mapped address means the structurally corresponding build-specific location supported by current evidence, not that the builds behave identically.

## Trusted function anchors

| Symbol | USA | Build | Candidate | Similarity | Score | Semantic recall | Tier | Independent edge |
|---|---|---|---|---:|---:|---:|---|---|
| Collision_BuildContactShape | `81:9E2A` | Europe retail | `81:9E1B` | 0.969 | 0.634 | 0.000 | strong |  |
| Collision_TransformVelocity | `81:9546` | Europe retail | `81:952C` | 0.911 | 0.839 | 0.667 | strong |  |
| Course_LoadAndMaterialize | `82:E165` | Europe retail | `82:E12B` | 0.906 | 0.766 | 0.467 | strong |  |
| HUD_QueueMessage | `81:C5B3` | Europe retail | `81:C59C` | 0.635 | 0.468 | 0.000 | strong | two coherent direct JSR references, including checkpoint/finish caller 81:81BA |
| Race_BuildRacerOAMState | `82:ACA5` | Europe retail | `82:ACAC` | 0.710 | 0.668 | 0.467 | supported |  |
| Race_HandleCheckpointFinish | `81:8050` | Europe retail | `81:8050` | 0.504 | 0.402 | 0.000 | strong | relocated object-dispatch table maps object code 0x14 directly to 81:8050 |
| Race_UpdateRacersFrame | `82:89B9` | Europe retail | `82:89CC` | 0.679 | 0.712 | 0.636 | supported |  |
| Stunt_FinalizeAndScoreAirTricks | `82:9A42` | Europe retail | `82:9A53` | 0.706 | 0.591 | 0.250 | supported |  |
| Collision_BuildContactShape | `81:9E2A` | PAL prototype | `81:9E0A` | 0.991 | 0.645 | 0.000 | strong |  |
| Collision_TransformVelocity | `81:9546` | PAL prototype | `81:9526` | 0.946 | 0.857 | 0.667 | strong |  |
| Course_LoadAndMaterialize | `82:E165` | PAL prototype | `82:E101` | 0.917 | 0.842 | 0.667 | strong |  |
| HUD_QueueMessage | `81:C5B3` | PAL prototype | `81:C590` | 0.969 | 0.984 | 1.000 | strong |  |
| Race_BuildRacerOAMState | `82:ACA5` | PAL prototype | `82:AC96` | 0.773 | 0.840 | 0.867 | strong |  |
| Race_HandleCheckpointFinish | `81:8050` | PAL prototype | `81:8050` | 0.871 | 0.585 | 0.000 | supported |  |
| Race_UpdateRacersFrame | `82:89B9` | PAL prototype | `82:89B6` | 0.779 | 0.826 | 0.818 | strong |  |
| Stunt_FinalizeAndScoreAirTricks | `82:9A42` | PAL prototype | `82:9A3D` | 0.724 | 0.775 | 0.750 | strong |  |

## Named RAM fields with repeated cross-anchor support

| Symbol | USA | Build | Candidate | Delta | Anchors | Independent edge |
|---|---|---|---|---:|---:|---|
| CurrentPlayer_XVelocityWorking | `7E:0F9F` | Europe retail | `7E:0FA9` | +10 | 2 |  |
| CurrentPlayer_YVelocityWorking | `7E:0FA1` | Europe retail | `7E:0FAB` | +10 | 2 |  |
| Player1_BoostMeter | `7E:11CF` | Europe retail | `7E:11D9` | +10 | 1 | bidirectional copy relation with 7E:11D7 in Race_UpdateRacersFrame |
| Player1_XPosition | `7E:0411` | Europe retail | `7E:0415` | +4 | 2 |  |
| Player1_XSpeed | `7E:04B7` | Europe retail | `7E:04BB` | +4 | 1 | bidirectional copy relation with 7E:0FA9 in Race_UpdateRacersFrame |
| Player1_YPosition | `7E:0415` | Europe retail | `7E:0419` | +4 | 2 |  |
| Player1_YSpeed | `7E:04BB` | Europe retail | `7E:04BF` | +4 | 1 | bidirectional copy relation with 7E:0FAB in Race_UpdateRacersFrame |
| Player2_BoostMeter | `7E:11D1` | Europe retail | `7E:11DB` | +10 | 1 | unique second bidirectional slot paired with 7E:11D7 in Race_UpdateRacersFrame |
| Player2_XPosition | `7E:0413` | Europe retail | `7E:0417` | +4 | 1 | unique second bidirectional slot paired through racer-update DP X-position workspace |
| Player2_XSpeed | `7E:04B9` | Europe retail | `7E:04BD` | +4 | 0 | unique second bidirectional slot paired with 7E:0FA9 in Race_UpdateRacersFrame |
| Player2_YPosition | `7E:0417` | Europe retail | `7E:041B` | +4 | 1 | unique second bidirectional slot paired through racer-update DP Y-position workspace |
| Player2_YSpeed | `7E:04BD` | Europe retail | `7E:04C1` | +4 | 0 | unique second bidirectional slot paired with 7E:0FAB in Race_UpdateRacersFrame |
| CurrentPlayer_XVelocityWorking | `7E:0F9F` | PAL prototype | `7E:0FA3` | +4 | 2 |  |
| CurrentPlayer_YVelocityWorking | `7E:0FA1` | PAL prototype | `7E:0FA5` | +4 | 2 |  |
| Player1_BoostMeter | `7E:11CF` | PAL prototype | `7E:11D3` | +4 | 1 | bidirectional copy relation with 7E:11D1 in Race_UpdateRacersFrame |
| Player1_XPosition | `7E:0411` | PAL prototype | `7E:0411` | +0 | 2 |  |
| Player1_XSpeed | `7E:04B7` | PAL prototype | `7E:04B7` | +0 | 1 | bidirectional copy relation with 7E:0FA3 in Race_UpdateRacersFrame |
| Player1_YPosition | `7E:0415` | PAL prototype | `7E:0415` | +0 | 2 |  |
| Player1_YSpeed | `7E:04BB` | PAL prototype | `7E:04BB` | +0 | 1 | bidirectional copy relation with 7E:0FA5 in Race_UpdateRacersFrame |
| Player2_BoostMeter | `7E:11D1` | PAL prototype | `7E:11D5` | +4 | 1 | unique second bidirectional slot paired with 7E:11D1 in Race_UpdateRacersFrame |
| Player2_XPosition | `7E:0413` | PAL prototype | `7E:0413` | +0 | 1 | unique second bidirectional slot paired through racer-update DP X-position workspace |
| Player2_XSpeed | `7E:04B9` | PAL prototype | `7E:04B9` | +0 | 0 | unique second bidirectional slot paired with 7E:0FA3 in Race_UpdateRacersFrame |
| Player2_YPosition | `7E:0417` | PAL prototype | `7E:0417` | +0 | 1 | unique second bidirectional slot paired through racer-update DP Y-position workspace |
| Player2_YSpeed | `7E:04BD` | PAL prototype | `7E:04BD` | +0 | 0 | unique second bidirectional slot paired with 7E:0FA5 in Race_UpdateRacersFrame |

## Single-anchor named RAM candidates

These are useful search/probe targets, but should not be copied into authoritative build-specific symbol maps without another discriminator.

| Symbol | USA | Build | Candidate | Delta | Source anchor |
|---|---|---|---|---:|---|
| Camera_ScreenXPosition | `7E:1509` | Europe retail | `7E:1513` | +10 | Race_BuildRacerOAMState |
| CurrentPlayer_BoostMeterWorking | `7E:11CD` | Europe retail | `7E:11D7` | +10 | Race_UpdateRacersFrame |
| CurrentPlayer_HalfTwistCount | `7E:0F61` | Europe retail | `7E:0F6B` | +10 | Stunt_FinalizeAndScoreAirTricks |
| CurrentPlayer_Index | `7E:0FEF` | Europe retail | `7E:0FF9` | +10 | Race_UpdateRacersFrame |
| CurrentPlayer_PitchScratch | `7E:0F49` | Europe retail | `7E:0F53` | +10 | Race_UpdateRacersFrame |
| Player1_FacedDirection | `7E:0BA1` | Europe retail | `7E:0BA7` | +6 | Race_BuildRacerOAMState |
| Player1_FlipCount | `7E:11FD` | Europe retail | `7E:1207` | +10 | Stunt_FinalizeAndScoreAirTricks |
| Player1_FlipQuarterProgress | `7E:1205` | Europe retail | `7E:120F` | +10 | Stunt_FinalizeAndScoreAirTricks |
| Player1_RollCount | `7E:11F9` | Europe retail | `7E:1203` | +10 | Stunt_FinalizeAndScoreAirTricks |
| Player1_RollQuarterProgress | `7E:1201` | Europe retail | `7E:120B` | +10 | Stunt_FinalizeAndScoreAirTricks |
| Player1_StuntAirLatch | `7E:1361` | Europe retail | `7E:136B` | +10 | Stunt_FinalizeAndScoreAirTricks |
| Player1_TabletopDuration | `7E:042F` | Europe retail | `7E:0433` | +4 | Stunt_FinalizeAndScoreAirTricks |
| Player1_ZFlipCount | `7E:042B` | Europe retail | `7E:042F` | +4 | Stunt_FinalizeAndScoreAirTricks |
| Player2_FacedDirection | `7E:0BA3` | Europe retail | `7E:0BA9` | +6 | Race_BuildRacerOAMState |
| Camera_ScreenXPosition | `7E:1509` | PAL prototype | `7E:150D` | +4 | Race_BuildRacerOAMState |
| CurrentPlayer_BoostMeterWorking | `7E:11CD` | PAL prototype | `7E:11D1` | +4 | Race_UpdateRacersFrame |
| CurrentPlayer_HalfTwistCount | `7E:0F61` | PAL prototype | `7E:0F65` | +4 | Stunt_FinalizeAndScoreAirTricks |
| CurrentPlayer_Index | `7E:0FEF` | PAL prototype | `7E:0FF3` | +4 | Race_UpdateRacersFrame |
| CurrentPlayer_PitchScratch | `7E:0F49` | PAL prototype | `7E:0F4D` | +4 | Race_UpdateRacersFrame |
| Player1_FacedDirection | `7E:0BA1` | PAL prototype | `7E:0BA1` | +0 | Race_BuildRacerOAMState |
| Player1_FinishGateState | `7E:119D` | PAL prototype | `7E:11A1` | +4 | Race_HandleCheckpointFinish |
| Player1_FlipCount | `7E:11FD` | PAL prototype | `7E:1201` | +4 | Stunt_FinalizeAndScoreAirTricks |
| Player1_FlipQuarterProgress | `7E:1205` | PAL prototype | `7E:1209` | +4 | Stunt_FinalizeAndScoreAirTricks |
| Player1_LapsRemaining | `7E:0EF1` | PAL prototype | `7E:0EF5` | +4 | Race_HandleCheckpointFinish |
| Player1_RollCount | `7E:11F9` | PAL prototype | `7E:11FD` | +4 | Stunt_FinalizeAndScoreAirTricks |
| Player1_RollQuarterProgress | `7E:1201` | PAL prototype | `7E:1205` | +4 | Stunt_FinalizeAndScoreAirTricks |
| Player1_StuntAirLatch | `7E:1361` | PAL prototype | `7E:1365` | +4 | Stunt_FinalizeAndScoreAirTricks |
| Player1_TabletopDuration | `7E:042F` | PAL prototype | `7E:042F` | +0 | Stunt_FinalizeAndScoreAirTricks |
| Player1_ZFlipCount | `7E:042B` | PAL prototype | `7E:042B` | +0 | Stunt_FinalizeAndScoreAirTricks |
| Player2_FacedDirection | `7E:0BA3` | PAL prototype | `7E:0BA3` | +0 | Race_BuildRacerOAMState |

## Operational rule

Use repeated-support mappings directly for build-specific watch/probe configuration. Use single-anchor candidates to target the cheapest independent check before semantic promotion.
