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

- Request sequence: **10** (first paired RF088 native / RF089 original echo witness after qualified #2723)
- Requested reason: Independent Agent 3 source review of [#2723](https://github.com/gamesbyian/UR-Recomp/pull/2723) at exact head `89a3aeb6be5e247e41d74c2b0e9ebed24a3c58ab` found the three-file opt-in wiring qualified; exact-head [Python #40576242684](https://github.com/gamesbyian/UR-Recomp/actions/runs/40576242684) passed **5,859 tests (48 skipped)** and [hygiene/actionlint #40576242723](https://github.com/gamesbyian/UR-Recomp/actions/runs/40576242723) passed. The qualified squash merge is `1c28db890aaa0728cc6ca89bf9120cab718af230`. Separately, native RF088 pinned compilation [#40569255104](https://github.com/gamesbyian/UR-Recomp/actions/runs/40569255104) and original RF089 pinned compilation [#40571594518](https://github.com/gamesbyian/UR-Recomp/actions/runs/40571594518) passed, but their **combined execution has never been observed**. Prior genuine Zoo observations established exact original/native WRAM equality at +5039 and sound pointer/counter divergence at +5040, with **all 51 sound-data seeks agreeing** and a roughly **29,452-unit native post-seek delay** before the first upload increment. Run **one** existing guarded `zoom-zoo` paired RF083/RF084/RF086/RF087/RF088/RF089 case on merged main with RF015/RF017, race mesh and DP on, RF016/RF018/RF019/APU off. Require nonzero original RF089 opcode rows at `028301` and `028304`, native RF088 actual `kind=R addr=2142` rows, no producer truncation, exact source/binary receipts and retained raw reference/native logs. Independently examine echo retry counts, branch outcomes and clocks at the first upload transition; original Snes9x v/h and native master cycles remain **unregistered**. Perform a **separate same-source observer-off control** before asserting noninterference or changing timing. Missing rows, failed producer, timeout or truncated output are experiment failures, **not** parity. No USA-event, physical Windows or release credit.
- Requested by: Project engineering agent, under owner autonomous engineering direction
- Evidence scope: source-qualified paired original/native SPC echo and first upload transition, 13 raw WRAM/SRAM pairs, separate observer-off control and independent review
- Release gate credit: **0**

Only advance this marker after confirming there is no already executing or
qualifying equivalent source-bound campaign for the same causal question.
The wrapper's preflight must reject an incidental marker edit or an
unrelated source change before the expensive producer runs.
