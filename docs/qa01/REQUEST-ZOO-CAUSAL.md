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

- Request sequence: **9** (first pinned RF086 postcommit and RF087 native snapshot-cut witness after merged #2717)
- Requested reason: [PR #2717](https://github.com/gamesbyian/UR-Recomp/pull/2717) merged as `8439d17c7a9142888b1cf015c68efbaaa1b30722`, adding opt-in RF086 **actual common-WRAM byte/word postcommit** observation and RF087 **existing native dump master/v/h + raw WRAM** receipts. Its final source head `3423dbb4376ab1f3ddf2dd8ae35ca408298d18f7` passed [Python #40551413388](https://github.com/gamesbyian/UR-Recomp/actions/runs/40551413388) and [hygiene #40551413421](https://github.com/gamesbyian/UR-Recomp/actions/runs/40551413421). A [one-shot pinned native build #40550736676](https://github.com/gamesbyian/UR-Recomp/actions/runs/40550736676) successfully compiled/linked 216 objects with RF084 then RF086 staged, ELF SHA-256 `4fc4a7e4962723fb26705fc1ebbf808b3b04a2d59b06f90f8b7c4d1096432033`. The preceding [Zoo #40512015017](https://github.com/gamesbyian/UR-Recomp/actions/runs/40512015017) source `f122ba2c98c8e39d63e24b5f28ab903febf99cd3` showed native precommit bus writes at host 6058/6059 and exact WRAM agreement at +5039, then the original/native sound-pointer/counter discrepancy at +5040, but had **no RF086/RF087 postcommit/cut evidence**. Execute **one** guarded original/native Zoo case on this merged instrumentation, only after independent review and confirmation no equivalent campaign is running. Require nonmissing, nontruncated RF086 postcommit rows at host 6058 for **both** 16-bit pointer `$0063` and 8-bit counter `$0069`; require RF087 successful host 6058/6059 dump rows and retained `scene-05039/05040.info.json` plus exact 128-KiB WRAM, with source-bound hashes, master/v/h and pointer/counter at cut. Reconcile those receipts with RF085 original v/h, native precommit bus log, 15 early original heartbeats and **all 13 full unmasked WRAM/SRAM pairs**; inspect observer-off controls. The `native_master` value is already charged accounting, not an independently registered original clock; a mismatch, absent producer or incomplete observer-off control is a diagnostic blocker, never parity or a release admission. Do not patch gameplay timing from an unregistered clock or dispatch a duplicate campaign. No next-Bowl/cold-save/complete USA event or Windows release credit.
- Requested by: Project engineering agent, under owner autonomous engineering direction
- Evidence scope: source-bound Zoo writer-entry, 13 raw DP/WRAM pairs, original/native divergence; independent review required
- Release gate credit: **0**

Only advance this marker after confirming there is no already executing or
qualifying equivalent source-bound campaign for the same causal question.
The wrapper's preflight must reject an incidental marker edit or an
unrelated source change before the expensive producer runs.
