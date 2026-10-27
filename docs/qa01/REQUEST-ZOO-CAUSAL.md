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

- Request sequence: **8** (re-run one bounded Zoo case only after native bus-log artifact retention fix #2715)
- Requested reason: The first genuine native bus-writer Zoo run [#40506380143](https://github.com/gamesbyian/UR-Recomp/actions/runs/40506380143) completed successfully on `2039a8576adc5badbb13d7f7d474ae8a588ad47d`, but its 333-file case artifact omitted the only new `qa01-native-dp-bus-writes.log` even though the producer verified a nonempty, uncapped file. Reviewed and merged [#2715](https://github.com/gamesbyian/UR-Recomp/pull/2715) as `2d7891d6c12ff1dcabb59160e7f9ce7607b11d0f` to retain that exact native replay path in the existing always-uploaded case artifact, with an exact-path regression and passing 5,836 Python tests (48 skipped) plus hygiene. Run **one** existing source-bound original/native Zoo case after independent review of this one-file marker. Independently download, CRC-check, hash and parse the *actual retained* bus-writer log; determine whether native `$0063/$0069` writes occur at host 6058/6059, compare with original 6056/6057 and 15 complete early heartbeats, rehash all 13 full unmasked WRAM/SRAM pairs, and inspect observer-off controls. The native recorder is pre-commit: do not infer committed-write timing, guest CPU/SPC clock parity or complete USA event admission. If the log still has no early writes, investigate the direct-write bridge/capture boundary rather than adding guessed generated-site hooks. Do not dispatch an equivalent concurrent campaign; zero Windows or USA release credit.
- Requested by: Project engineering agent, under owner autonomous engineering direction
- Evidence scope: source-bound Zoo writer-entry, 13 raw DP/WRAM pairs, original/native divergence; independent review required
- Release gate credit: **0**

Only advance this marker after confirming there is no already executing or
qualifying equivalent source-bound campaign for the same causal question.
The wrapper's preflight must reject an incidental marker edit or an
unrelated source change before the expensive producer runs.
