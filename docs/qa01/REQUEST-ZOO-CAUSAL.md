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

- Request sequence: **12** (original RF090 actual $2140 returned-value handshake after merged #2729)
- Requested reason: The completed correct-site sequence-11 [#40590283123](https://github.com/gamesbyian/UR-Recomp/actions/runs/40590283123) independently established executed RF089 original branch/zero-flag observations and RF088 native $2140 readiness polling, with all 13 original/native unmasked SRAM pairs equal but a first WRAM difference at Zoo +5040 (`$0063/$0069`). The original RF089 CMP/BNE observer did **not** capture the returned SPC port value, preventing a causal comparison with native's 5,429 `FFFF`, two `FFAA`, one `BBAA` readiness observations and the 29,406-unit unregistered seek-to-increment interval. The bounded original RF090 return-value observer is now integrated in [#2729](https://github.com/gamesbyian/UR-Recomp/pull/2729), merge `197a2052f4dedcb1d7161f26c0a22b44cf42a203`; final PR head `f797a1f6b7cd74df751c2b1a8c382a2739706fe7` passed exact-head Python [#40601803358](https://github.com/gamesbyian/UR-Recomp/actions/runs/40601803358) and hygiene [#40601803431](https://github.com/gamesbyian/UR-Recomp/actions/runs/40601803431), and immutable RF090 implementation `8edb84aa7e98b71c04a99d54ebd7faa25ecff1d8` compiled/linked actual pinned Snes9x in [#40601625554](https://github.com/gamesbyian/UR-Recomp/actions/runs/40601625554). Independent source/build-log review [#5675864356](https://github.com/gamesbyian/UR-Recomp/pull/2729#pullrequestreview-5675864356) qualified diagnostic integration only. Request **one** existing guarded `zoom-zoo` original/native paired campaign with unchanged ROM, source movie, SRAM seed, RF015/RF017 and RF083/RF084/RF086/RF087/RF088/RF089/RF090 enabled, RF016/RF018/RF019/APU changes off. Require **executed, nontruncated** original `QA01RF090ORIG addr=2140` returned-value rows, RF089 original 82:80DB/80DE CMP/BNE and RF088 native $2140 reads; retain original/native replay logs, exact source/build receipts, and all **13 raw WRAM/SRAM pairs**. Independently compare original actual returned values/branch outcomes against native `FFFF→FFAA→BBAA` at matched semantic seek/increment anchors, without assuming absolute clock registration. A separate **same-source observer-off control** is required before noninterference or timing claims. Missing rows/truncation/producer failure are not parity evidence. This remains diagnostic only: **0/45 USA events, 0/12 Windows gates**.
- Requested by: Project engineering agent, under owner autonomous engineering direction
- Evidence scope: source-qualified paired original/native SPC echo and first upload transition, 13 raw WRAM/SRAM pairs, separate observer-off control and independent review
- Release gate credit: **0**

Only advance this marker after confirming there is no already executing or
qualifying equivalent source-bound campaign for the same causal question.
The wrapper's preflight must reject an incidental marker edit or an
unrelated source change before the expensive producer runs.
