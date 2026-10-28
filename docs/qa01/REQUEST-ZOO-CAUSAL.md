# Authorized original/native Zoo causal experiment request

This file is an intentional **PR-driven trigger marker** for the existing
`.github/workflows/qa01-event-campaign.yml` native/original Zoo diagnostic.
It is **not** a second QA-01 plan, CI gate, release authority or gameplay
acceptance. The approved wrapper (installed separately) must run only on
`main` when *this exact file* is changed by a reviewed one-file request
PR. The marker must advance by **one** and give a new concrete reason.

The canonical campaign and independent QA continue to own source/WRAM/SRAM semantics. This **observer-on** request retains `selected=zoom-zoo`, `zoo_race_mesh=true`, `zoo_dp_window=true`, RF015 (`baldosa_refresh_beam_rate=true`) and RF017 (`baldosa_io_clock_order=true`), and enables both paired original/native observers. Merged RF091 now records actual original CPU-side $2140-$2143 writes **after** Snes9x's committed APU-port call, alongside RF090 returned reads and native RF088 port events. The original USA Zoo ROM/movie/seed are unchanged. The observer-off sequence-13 control already established sampled-state noninterference; do not rerun it. This case is diagnostic only, not a CPU/SPC clock-equivalence, full-event or release verdict.

## Next research request

- Request sequence: **20** (source-owned RF094 SPC/DSP and F7 Bowl-consumer follow-through)
- Requested reason: Run exactly one source-qualified sequence-20 original/native Zoo RF094 post-DSP/F7 consumer experiment after merged #2805 and separately qualified one-shot guard #2810. Sequence-19 actual CPU/SPC rows already proved both cores dispatch command opcode 01 argument 02 as bus port2=41/port3=02, but at original Bowl-entry−1 versus native Bowl-entry+0; both SPCs echoed in 50/49 within-core ticks. The existing SPC-to-CPU F7 response stream is displaced at entry+2 and then stops, with no actual downstream DSP F3 register write witness. This experiment must stage the newly merged real post-commit DSP F3 original/native observer only via RF094 explicit opt-in, capture source-owned register/value/write ordering at original frames 6445..6451 and native frames 6447..6453, and retain real SPC F7 port writes through each core's entry+4 to distinguish delayed-but-convergent handling from lasting downstream state effects. Keep own-clock SPC ticks and separate original/native CPU frames; do not subtract absolute clocks or infer PCM equivalence from equal register values. Retain the unchanged USA Zoo ROM/movie/seed, real original and native executables and source SHA, original stock controller movie input, RF015/017 baseline, original/native 2P independent replay inputs, raw unmasked full WRAM/SRAM result+265..269, genuine result→next Bowl progress, and four fresh-guest 8192-byte ranked record cold SRAM images. Preserve observer-on sequence-19 and observer-off sequence-13 receipts as historical different-source comparisons, not same-binary controls. Explicitly classify any strict original/native divergence, missing/truncated rows or absent DSP writes without bypass, fabricated output, suppression, or full-event/release gate credit.
- Observer mode: **on**
- RF094 DSP/F7 witness: **on**
- Requested by: Project engineering agent, under owner autonomous engineering direction
- Evidence scope: one guarded sequence-20 source-pinned original/native Zoo campaign with executed real RF094 post-commit DSP F3 register/value/own-tick evidence and unmasked original RF092/native RF093 SPC F7 port writes through own Bowl entry+4; strict no-truncation/empty/clock-axis report, unchanged CPU→SPC command publisher, original 2014 and native executable hashes, source ROM/movie/seed identity, genuine result→next Bowl follow-through, raw independent WRAM/SRAM and four fresh-guest 8192-byte ranked Zoo SRAM files. No interpreted audible PCM equivalence, cross-SPC master-clock registration, full USA event, physical Windows storage or release gate credit.
- Release gate credit: **0**

Only advance this marker after confirming there is no already executing or
qualifying equivalent source-bound campaign for the same causal question.
The wrapper's preflight must reject an incidental marker edit or an
unrelated source change before the expensive producer runs.
