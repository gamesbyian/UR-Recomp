# Authorized original/native Zoo causal experiment request

This file is an intentional **PR-driven trigger marker** for the existing
`.github/workflows/qa01-event-campaign.yml` native/original Zoo diagnostic.
It is **not** a second QA-01 plan, CI gate, release authority or gameplay
acceptance. The approved wrapper (installed separately) must run only on
`main` when *this exact file* is changed by a reviewed one-file request
PR. The marker must advance by **one** and give a new concrete reason.

The canonical campaign and independent QA continue to own source/WRAM/SRAM semantics. This **observer-on** request keeps `selected=zoom-zoo`, `zoo_race_mesh=true`, `zoo_dp_window=true`, RF015 (`baldosa_refresh_beam_rate=true`) and RF017 (`baldosa_io_clock_order=true`) while enabling both paired observer inputs `qa01_rf084_native_sound_dp=true` and `qa01_rf088_rf089_echo=true`. The source-qualified original movie and seed are unchanged. RF016/018/019/APU and publication remain off. This is diagnostic only and must not publish ROM/player data or claim a USA-event pass.

## Next research request

- Request sequence: **14** (merged RF091 original committed APU write versus native command/read chronology)
- Requested reason: Following independently reviewed and merged original RF091 CPU-to-APU committed-write instrumentation [#2757](https://github.com/gamesbyian/UR-Recomp/pull/2757) at main `c634e99b80f73f56319743d24698feee2355ab22`, request exactly one guarded source-pinned Zoo original/native observer-ON experiment. Reuse the identical original USA Zoo ROM/movie/SRAM seed, RF015/RF017, 13 unmasked +5034..+5046 WRAM/SRAM pairs, and existing original RF089/RF090 and native RF088 witnesses. Require actual nontruncated `QA01RF091ORIG` committed `$2140` writes with original CPU frame/v/h/PC, `QA01RF090ORIG` returned values and RF089 branch/zero-flag observations; retain native RF088 first command write, `FFFF→FFAA→BBAA` readiness sequence, and source/binary/producer receipts. Compare within each core's own clock axis from CPU command commit to first read/ready and the +5039/+5040 pointer/counter onset; do not equate original v/h and native master clocks without registration, or call the CPU write a proven SPC consumption/ready event. Independently register SPC receipt/ready/CPU consumption clocks in a later bounded discriminator if still absent. The sequence-13 observer-OFF control [#40615839010](https://github.com/gamesbyian/UR-Recomp/actions/runs/40615839010) was on an earlier source, so a new same-source OFF control is required before claiming RF091 observer noninterference. Abort/flag missing rows, truncation, original/native producer failure, or changed controller/source identities. No timing patch or USA/Windows acceptance is authorized by this request.
- Observer mode: **on**
- Requested by: Project engineering agent, under owner autonomous engineering direction
- Evidence scope: same original/native Zoo inputs, 13 raw WRAM/SRAM pairs, original RF091 committed CPU write and RF090 returned-read chronology against native RF088, independent artifact and clock-axis review
- Release gate credit: **0**

Only advance this marker after confirming there is no already executing or
qualifying equivalent source-bound campaign for the same causal question.
The wrapper's preflight must reject an incidental marker edit or an
unrelated source change before the expensive producer runs.
