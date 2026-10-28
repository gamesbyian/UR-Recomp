# Authorized original/native Zoo causal experiment request

This file is an intentional **PR-driven trigger marker** for the existing
`.github/workflows/qa01-event-campaign.yml` native/original Zoo diagnostic.
It is **not** a second QA-01 plan, CI gate, release authority or gameplay
acceptance. The approved wrapper (installed separately) must run only on
`main` when *this exact file* is changed by a reviewed one-file request
PR. The marker must advance by **one** and give a new concrete reason.

The canonical campaign and independent QA continue to own source/WRAM/SRAM semantics. This **observer-on** request retains `selected=zoom-zoo`, `zoo_race_mesh=true`, `zoo_dp_window=true`, RF015 (`baldosa_refresh_beam_rate=true`) and RF017 (`baldosa_io_clock_order=true`), and enables both paired original/native observers. Merged RF091 now records actual original CPU-side $2140-$2143 writes **after** Snes9x's committed APU-port call, alongside RF090 returned reads and native RF088 port events. The original USA Zoo ROM/movie/seed are unchanged. The observer-off sequence-13 control already established sampled-state noninterference; do not rerun it. This case is diagnostic only, not a CPU/SPC clock-equivalence, full-event or release verdict.

## Next research request

- Request sequence: **19** (pair newly compiled original CPU port edges with native SPC at next Bowl)
- Requested reason: After independently qualifying and merging #2786, execute a single original/native Zoo sequence-19 observer-ON campaign with the now clean-compiled original RF083/RF090/RF091 CPU observer active at original frames 6445..6449 (result+265..269). Capture actually returned original $2140..$2143 CPU reads and post-commit original writes, alongside native RF088 CPU writes at native frames 6447..6451, executed RF092/RF093 SPC reads/echoes and the known command order 08FF, 077F, 0102. The sequence-18 independently audited original/native SPC already read F6 48→87→41 and echoed 40→80→40 with nearly equal within-SPC acknowledgment latency (50 vs 49 ticks), but CPU-to-SPC spacing differs; this new paired witness must isolate whether original/native upstream CPU command/queue scheduling or inter-core phase explains the one sampled-frame result+267 read-index/toggle residual. Reuse unchanged USA Zoo ROM/movie/seed, stock source controller inputs, RF015/RF017, both distinct clock axes and preexisting observer-OFF sequence-13 as historical control; do not reinterpret that older epoch as a same-binary OFF pair. Retain unmasked complete WRAM/SRAM at each result+265..269 anchor, full result→Next Bowl guest behavior, actual source/executable provenance, and all four 8192-byte original/native fresh-guest ranked-record SRAM witnesses. Compare prior sequence-18 raw samples for observational noninterference and source-drift explicitly; do not mask APU/stack bytes or award a USA event/release gate from a diagnostic row.
- Observer mode: **on**
- Requested by: Project engineering agent, under owner autonomous engineering direction
- Evidence scope: one source-pinned, unchanged-input original/native Zoo sequence-19 run with actual returned/committed original RF090/RF091 CPU port rows at 6445..6449, native RF088 CPU rows at 6447..6451, genuine RF092/RF093 SPC receipt/echo, result-to-Next-Bowl follow-through, four new raw fresh-guest cold SRAM images, full unmasked WRAM/SRAM snapshots, source/ROM/movie/original and native binary identity; no claimed calibrated inter-core clocks, PCM parity, host Windows cold-save or QA admission
- Release gate credit: **0**

Only advance this marker after confirming there is no already executing or
qualifying equivalent source-bound campaign for the same causal question.
The wrapper's preflight must reject an incidental marker edit or an
unrelated source change before the expensive producer runs.
