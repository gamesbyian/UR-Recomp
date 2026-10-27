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

- Request sequence: **6** (source-bound native M0X0 first-boundary post-commit writer experiment after merged #2709)
- Requested reason: Execute exactly one original/native Zoo RF083/RF084/RF085 causal case after independent review and merge of #2709 (`df8058f4ffd5eb113e70456a56f6bf44a526db55`), which instruments the previously unobserved generated `Snd_IncDataPtr_FastRom_M0X0` real post-commit 16-bit pointer write while preserving M1X0 counter/pointer hooks. The previous successful #40492981231 (source `478c68f6d2f2b81c77f878008ec2c4554b614857`) retained 13,585 original early rows but zero native RF084 writes at host 6058/6059 despite first raw +5040 `$0063/$0069` divergence. Require 15 original early 6051–6065 heartbeats, untruncated original 6056/6057 writer rows, actual native M0X0/M1X0 6058/6059 writer presence/absence with master-cycle ordinals, 13 complete unmasked WRAM/SRAM pairs and observer-off controls; do not infer original/native clock alignment from frame labels. If still no early native writes, stop as unresolved writer-path blind spot rather than applying a speculative CPU timing fix. No next-Bowl/cold-save/event or release acceptance.
- Requested by: Project engineering agent, under owner autonomous engineering direction
- Evidence scope: source-bound Zoo writer-entry, 13 raw DP/WRAM pairs, original/native divergence; independent review required
- Release gate credit: **0**

Only advance this marker after confirming there is no already executing or
qualifying equivalent source-bound campaign for the same causal question.
The wrapper's preflight must reject an incidental marker edit or an
unrelated source change before the expensive producer runs.
