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

- Request sequence: **9** (one RF086 postcommit / RF087 native snapshot-cut Zoo discriminator after qualified #2717)
- Requested reason: Independently reviewed and merged [#2717](https://github.com/gamesbyian/UR-Recomp/pull/2717) as `8439d17c7a9142888b1cf015c68efbaaa1b30722`. The source-exact [Python #40551413388](https://github.com/gamesbyian/UR-Recomp/actions/runs/40551413388) passed 5,850 tests (48 skipped), [hygiene #40551413421](https://github.com/gamesbyian/UR-Recomp/actions/runs/40551413421) passed, and the previously missing full **pinned RF084→RF086 native compile/link** independently passed [#40550736676](https://github.com/gamesbyian/UR-Recomp/actions/runs/40550736676), producing ELF SHA-256 `4fc4a7e4962723fb26705fc1ebbf808b3b04a2d59b06f90f8b7c4d1096432033`. The actual original/native [Zoo #40512015017](https://github.com/gamesbyian/UR-Recomp/actions/runs/40512015017) showed full WRAM equality at +5039 and first sound-pointer/counter divergence at +5040, while the original opcode stream reaches the original snapshot values at scanline 224. **Run exactly one** existing guarded Zoo case with RF015/RF017/RF084/RF086/RF087 on, RF016/RF018/RF019/APU off. Require actual native RF086 postcommit rows at host 6058 (both widths), RF087 successful `scene-05039/05040` dump metadata/128-KiB WRAM, original RF085 v/h observations, complete 13 raw WRAM/SRAM pairs, and an independent observer-off control. Independently compare actual post-write native master cycles to native snapshot master/v/h, then correlate original frame/scanline without assuming cross-core clock equivalence. If a producer fails, classify producer failure; if the first causal mismatch remains unresolved, stop before guessing CPU timing changes. **No USA-event, physical Windows or release credit.**
- Requested by: Project engineering agent, under owner autonomous engineering direction
- Evidence scope: source-bound Zoo writer-entry, 13 raw DP/WRAM pairs, original/native divergence; independent review required
- Release gate credit: **0**

Only advance this marker after confirming there is no already executing or
qualifying equivalent source-bound campaign for the same causal question.
The wrapper's preflight must reject an incidental marker edit or an
unrelated source change before the expensive producer runs.
