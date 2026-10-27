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

- Request sequence: **3** (single source-bound RF083/RF084 Zoo campaign after full original-core header-dependent rebuild #2702)
- Requested reason: Re-run exactly one original/native Zoo RF083/RF084 writer case on merged #2702, after source-exact run #40474888477 failed because patched cpumacro.h/getset.h were relinked against stale cpuops.o. The repaired workflow cleans every original core object after staging and rebuilds the instrumented cpuops.cpp; independently verify actual recompilation, real original INC16 post-write rows, native RF084 writer rows, observer-off controls and all 13 raw +5034..+5046 WRAM/SRAM pairs. Stop as producer failure if original observer rows remain absent; do not relax acceptance predicates or claim complete-event parity.
- Requested by: Project engineering agent, under owner autonomous engineering direction
- Evidence scope: source-bound Zoo writer-entry, 13 raw DP/WRAM pairs, original/native divergence; independent review required
- Release gate credit: **0**

Only advance this marker after confirming there is no already executing or
qualifying equivalent source-bound campaign for the same causal question.
The wrapper's preflight must reject an incidental marker edit or an
unrelated source change before the expensive producer runs.
