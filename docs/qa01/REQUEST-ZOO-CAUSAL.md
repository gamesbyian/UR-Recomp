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
remain off. This is the already merged RF083 original word-entry and RF084
native byte/word writer experiment. It must not publish ROM or player data
or claim a USA-event pass.

## Next research request

- Request sequence: **7** (first native direct/bus writer-location witness after merged #2712)
- Requested reason: Execute exactly one original/native Zoo causal case after independent review and merge of #2712 (`87b94b7ddd0a6fadd185910a946c39d3e9f66288`), which reuses the pinned Baldosa native `SNESRECOMP_WLOG_ADDR` CPU/direct-WRAM bus recorder for the actual Zoo `complete.script` only, restricted to `$0062..$0069` and capped at 200,000 rows. Independently audited #40499045230 (source `c555da805aaa089ec592ad41bb19c9846b9eed30`) had 13,585 complete original early writer rows and 767 native generated-site post-writes (763 M1X0, four M0X0, all at host 6066/6068), but **zero** generated-site native writes at host 6058/6059 despite unmasked +5040 WRAM differences at `$0063=73/4D` and `$0069=BE/97`. Require actual retained `qa01-native-dp-bus-writes.log`, verify no missing/empty/capped producer, inspect first native 6058/6059 bus-writer function/path and source of each write, correlate original 6056/6057 and 15 early heartbeats, and independently rehash all 13 raw WRAM/SRAM pairs plus observer-off controls. Bus records are **pre-commit**, do not themselves establish post-write master cycles, original/native clock equivalence or a full event. If no early bus write appears, stop and investigate the write bridge or capture boundary, not another guessed generated hook or timing patch. No next-Bowl/cold-save/event or release acceptance.
- Requested by: Project engineering agent, under owner autonomous engineering direction
- Evidence scope: source-bound Zoo writer-entry, 13 raw DP/WRAM pairs, original/native divergence; independent review required
- Release gate credit: **0**

Only advance this marker after confirming there is no already executing or
qualifying equivalent source-bound campaign for the same causal question.
The wrapper's preflight must reject an incidental marker edit or an
unrelated source change before the expensive producer runs.
