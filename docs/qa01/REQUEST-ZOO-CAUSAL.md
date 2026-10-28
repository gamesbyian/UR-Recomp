# Authorized original/native Zoo causal experiment request

This file is an intentional **PR-driven trigger marker** for the existing
`.github/workflows/qa01-event-campaign.yml` native/original Zoo diagnostic.
It is **not** a second QA-01 plan, CI gate, release authority or gameplay
acceptance. The approved wrapper (installed separately) must run only on
`main` when *this exact file* is changed by a reviewed one-file request
PR. The marker must advance by **one** and give a new concrete reason.

The canonical campaign and independent QA continue to own source/WRAM/SRAM semantics. This **observer-on** request retains `selected=zoom-zoo`, `zoo_race_mesh=true`, `zoo_dp_window=true`, RF015 (`baldosa_refresh_beam_rate=true`) and RF017 (`baldosa_io_clock_order=true`), and enables both paired original/native observers. Merged RF091 now records actual original CPU-side $2140-$2143 writes **after** Snes9x's committed APU-port call, alongside RF090 returned reads and native RF088 port events. The original USA Zoo ROM/movie/seed are unchanged. The observer-off sequence-13 control already established sampled-state noninterference; do not rerun it. This case is diagnostic only, not a CPU/SPC clock-equivalence, full-event or release verdict.

## Next research request

- Request sequence: **18** (execute the merged result-boundary CPU/SPC port observers)
- Requested reason: Run one source-bound sequence-18 original/native Zoo campaign to execute the already merged #2782 RF088/RF092/RF093 bounded port-edge observers at the real next-Bowl queue boundary: original frames 6445..6449 and native frames 6447..6451, alongside the retained earlier 6054..6060 sound-upload windows. The sequence-17 raw result+267 queue payloads are byte-identical but original has read/write/toggle 04/04/40 while native has 03/04/80, reconverging at +268; this experiment must distinguish executed CPU-to-SPC command delivery, SPC echo/ack and scheduling on each core's own clock. Preserve the same original USA ROM/movie/seed, RF015/017 baseline, paired observer-ON mode and prior sequence-13 observer-OFF sampled-state control. Retain unmasked WRAM/SRAM at result+265..+269, actual result and next-Bowl follow-through, original/native binaries, and all four fresh-guest 8192-byte SRAM cold-reload witnesses enabled by #2778. Classify any strict divergence without waiver or event credit. Do not infer Windows host-disk cold-save durability or 1/45 event acceptance.
- Observer mode: **on**
- Requested by: Project engineering agent, under owner autonomous engineering direction
- Evidence scope: one bounded paired original/native Zoo source-run including newly merged real result-boundary CPU/SPC port edges, result onset/followthrough, next Bowl, fresh guest earned ranked-record reload and four raw cold SRAM files where source-qualified, full source/ROM/movie/binary identity, unmasked WRAM/SRAM, RF088-093 diagnostics and independently reviewed artifacts; 0 event and Windows gate credit pending separate admission
- Release gate credit: **0**

Only advance this marker after confirming there is no already executing or
qualifying equivalent source-bound campaign for the same causal question.
The wrapper's preflight must reject an incidental marker edit or an
unrelated source change before the expensive producer runs.
