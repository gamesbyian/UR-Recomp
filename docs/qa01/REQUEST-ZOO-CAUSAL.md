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

- Request sequence: **5** (source-bound RF085 early original Zoo boundary retry after merged #2707 budget repair)
- Requested reason: Re-run exactly one original/native Zoo RF083/RF084 campaign on merged #2707 (squash b504e46e56d4a2d9869aab814e7398e6a1afd12a), with the separate original RF085 early 6051–6065 DP stream raised from 8192 to 16384 rows. Previous source-bound run #40487975108 reached 8192 rows and emitted QA01RF085EARLY_TRUNCATED at original frame 6062 despite all 15 heartbeats; this was a producer budget failure, not CPU parity evidence. Require complete 6051–6065 original early rows with no truncation, first original 6056/6057 writer sequence versus native RF084 6058/6059 with separate clock domains, unchanged 13 raw WRAM/SRAM pairs and observer-off controls, and late RF083 unchanged. Stop if the early stream still truncates or source/build identities disagree; no CPU timing fix, event or release credit.
- Requested by: Project engineering agent, under owner autonomous engineering direction
- Evidence scope: source-bound Zoo writer-entry, 13 raw DP/WRAM pairs, original/native divergence; independent review required
- Release gate credit: **0**

Only advance this marker after confirming there is no already executing or
qualifying equivalent source-bound campaign for the same causal question.
The wrapper's preflight must reject an incidental marker edit or an
unrelated source change before the expensive producer runs.
