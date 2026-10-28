# Authorized original/native Zoo causal experiment request

This file is an intentional **PR-driven trigger marker** for the existing
`.github/workflows/qa01-event-campaign.yml` native/original Zoo diagnostic.
It is **not** a second QA-01 plan, CI gate, release authority or gameplay
acceptance. The approved wrapper (installed separately) must run only on
`main` when *this exact file* is changed by a reviewed one-file request
PR. The marker must advance by **one** and give a new concrete reason.

The canonical campaign and independent QA continue to own source/WRAM/SRAM semantics. This **observer-on** request retains `selected=zoom-zoo`, `zoo_race_mesh=true`, `zoo_dp_window=true`, RF015 (`baldosa_refresh_beam_rate=true`) and RF017 (`baldosa_io_clock_order=true`), and enables both paired original/native observers. Merged RF091 now records actual original CPU-side $2140-$2143 writes **after** Snes9x's committed APU-port call, alongside RF090 returned reads and native RF088 port events. The original USA Zoo ROM/movie/seed are unchanged. The observer-off sequence-13 control already established sampled-state noninterference; do not rerun it. This case is diagnostic only, not a CPU/SPC clock-equivalence, full-event or release verdict.

## Next research request

- Request sequence: **15** (RF092 original SPC executed input-receipt/output-ready clock discriminator)
- Requested reason: Run exactly one guarded original/native Zoo sequence-15 with newly merged RF092 opt-in original SPC $F4 CPU-to-SPC executed input reads and $F4 SPC-to-CPU executed output writes, alongside RF091 committed original CPU $2140 write, RF090 returned original reads and RF088 native port reads/writes. Preserve the original USA Zoo ROM/movie/seed, RF015/RF017, 13 unmasked +5034..+5046 WRAM/SRAM pairs, executable/source hashes and sequence-13 observer-off baseline. Require nontruncated executed RF092 F4 input-read and output-write rows, their original-SPC tick values, RF091 write and RF090 FFFF/FFAA/BBAA reads, plus native first write/read/ready rows. Register original CPU, original SPC and native clock axes separately; do not subtract cross-domain timestamps or infer causality from an unaligned origin. Independently audit raw logs and artifact bytes, and compare the +5039/+5040 first residual without masks. If RF092 rows are absent, truncated, not ordered as expected, or insufficient to identify first receipt/ready, stop at the earliest failed discriminator and do not patch CPU/APU timing or award event credit. No complete USA event or Windows gate admission.
- Observer mode: **on**
- Requested by: Project engineering agent, under owner autonomous engineering direction
- Evidence scope: same original/native Zoo inputs and 13 raw WRAM/SRAM pairs, RF092 executed original SPC F4 receipt/ready plus RF091/RF090 original CPU and RF088 native anchors, sequence-13 observer-off baseline, independent byte audit and separately registered CPU/SPC clock axes
- Release gate credit: **0**

Only advance this marker after confirming there is no already executing or
qualifying equivalent source-bound campaign for the same causal question.
The wrapper's preflight must reject an incidental marker edit or an
unrelated source change before the expensive producer runs.
