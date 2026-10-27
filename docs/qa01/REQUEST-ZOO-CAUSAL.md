# Authorized original/native Zoo causal experiment request

This file is an intentional **PR-driven trigger marker** for the existing
`.github/workflows/qa01-event-campaign.yml` native/original Zoo diagnostic.
It is **not** a second QA-01 plan, CI gate, release authority or gameplay
acceptance. The approved wrapper (installed separately) must run only on
`main` when *this exact file* is changed by a reviewed one-file request
PR. The marker must advance by **one** and give a new concrete reason.

The canonical campaign and independent QA continue to own source/WRAM/SRAM
semantics. Defaults for this route are precisely `selected=zoom-zoo`,
`zoo_race_mesh=true`, `zoo_dp_window=true`,
`qa01_rf084_native_sound_dp=true`, `baldosa_refresh_beam_rate=true`,
`baldosa_io_clock_order=true`; RF016/018/019/APU and platform publication
remain off. This sequence opts into the already merged RF083/RF084 writer observers
and RF088/RF089 paired echo observers; all are diagnostic only. It must not publish ROM or player data
or claim a USA-event pass.

## Next research request

- Request sequence: **11** (correct-site original FastROM 82:80DB/80DE and native $2140 Zoo echo after merged #2725)
- Requested reason: The sequence-10 original/native Zoo experiment [#40580130876](https://github.com/gamesbyian/UR-Recomp/actions/runs/40580130876) produced **zero RF089 original and zero RF088 native echo rows** and failed its case gate, despite a successful source-bound build. Independent case audit found a definite wrong FastROM bank selector and the wrong Zoo upload routine/port: actual original opcode PCs are `82:80DB/80DE` and compiled native `Snd_UploadBlock_80DB` reads `$2140`, whereas the old observer required the different `$2142` block-list path. The bounded six-file repair [#2725](https://github.com/gamesbyian/UR-Recomp/pull/2725) is now squash-merged at `98a16fe55f49c1fd926600367f3514c7f28f541f`; exact repair-head Python [#40582238039](https://github.com/gamesbyian/UR-Recomp/actions/runs/40582238039) and hygiene [#40582238179](https://github.com/gamesbyian/UR-Recomp/actions/runs/40582238179) passed, and one-shot pinned original/native compile [#40587446155](https://github.com/gamesbyian/UR-Recomp/actions/runs/40587446155) passed original Snes9x, snesref and full native link. The disposable compile-only [#2726](https://github.com/gamesbyian/UR-Recomp/pull/2726) was closed **unmerged**. Request **one** existing guarded `zoom-zoo` paired RF083/RF084/RF086/RF087/RF088/RF089 case with the unchanged controller movie, RF015/RF017 and the merged echo repair, RF016/RF018/RF019/APU off. Require actual nontruncated original `pc=8280DB` **and** `pc=8280DE` rows and native `kind=R addr=2140` rows, exact source/binary receipts and full original/native replay logs. Independently compare actual echo return values, branch/zero-flag retry sequence, writer order and original beam vs native master/capture clocks without pretending the clock axes are already registered; recheck all **13 unmasked WRAM/SRAM pairs** around +5039/+5040. Obtain a **separate same-source observer-off control** before claiming noninterference or any CPU/APU correction. Missing rows, truncation, producer failure or timeout remain experiment failures. This is research only, **0/45 USA events and 0/12 Windows gates**.
- Requested by: Project engineering agent, under owner autonomous engineering direction
- Evidence scope: source-qualified paired original/native SPC echo and first upload transition, 13 raw WRAM/SRAM pairs, separate observer-off control and independent review
- Release gate credit: **0**

Only advance this marker after confirming there is no already executing or
qualifying equivalent source-bound campaign for the same causal question.
The wrapper's preflight must reject an incidental marker edit or an
unrelated source change before the expensive producer runs.
