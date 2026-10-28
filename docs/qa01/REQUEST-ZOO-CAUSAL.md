# Authorized original/native Zoo causal experiment request

This file is an intentional **PR-driven trigger marker** for the existing
`.github/workflows/qa01-event-campaign.yml` native/original Zoo diagnostic.
It is **not** a second QA-01 plan, CI gate, release authority or gameplay
acceptance. The approved wrapper (installed separately) must run only on
`main` when *this exact file* is changed by a reviewed one-file request
PR. The marker must advance by **one** and give a new concrete reason.

The canonical campaign and independent QA continue to own source/WRAM/SRAM semantics. This **observer-on** request retains `selected=zoom-zoo`, `zoo_race_mesh=true`, `zoo_dp_window=true`, RF015 (`baldosa_refresh_beam_rate=true`) and RF017 (`baldosa_io_clock_order=true`), and enables both paired original/native observers. Merged RF091 now records actual original CPU-side $2140-$2143 writes **after** Snes9x's committed APU-port call, alongside RF090 returned reads and native RF088 port events. The original USA Zoo ROM/movie/seed are unchanged. The observer-off sequence-13 control already established sampled-state noninterference; do not rerun it. This case is diagnostic only, not a CPU/SPC clock-equivalence, full-event or release verdict.

## Next research request

- Request sequence: **16** (RF093 native SPC executed input-receipt/output-ready and queue-timing discriminator)
- Requested reason: Run exactly one guarded original/native Zoo sequence-16 with merged RF093 opt-in native SPC F4 CPU-to-SPC executed reads, F4/F5 SPC-to-CPU ready writes, CPU-to-SPC queue schedule/apply and actual input-port mutation, alongside RF092 original SPC receipt/ready, RF091 original committed CPU $2140 write, RF090 original CPU reads and RF088 native CPU-side events. Preserve original USA Zoo ROM/movie/seed, RF015/RF017, the 13 unmasked +5034..+5046 WRAM/SRAM pairs, full source/binary hashes and sequence-13 observer-off baseline. Require nontruncated native RF093 F4 input-read and output-write rows plus queue schedule/apply; retain actual original RF092 F4=FF receipt, F4=AA/F5=BB ready and RF090 FFFF/FFAA/BBAA CPU observations. Register native CPU master, native SPC portClock, original CPU v/h and original SPC ticks separately, never subtract uncalibrated clock origins. Compare ordered edges and intervals within each clock domain, identify whether the known native +29,412-master-unit readiness lag originates before native SPC receipt, during SPC work, or after ready publication, only where calibration permits. Independently audit raw logs, ZIP hashes and unmasked +5039/+5040 snapshots. If RF093 rows are missing/truncated, build/link fails or edges are ambiguous, stop without speculative CPU/APU timing patch or event credit. No complete USA event or Windows gate admission.
- Observer mode: **on**
- Requested by: Project engineering agent, under owner autonomous engineering direction
- Evidence scope: one source-bound paired original/native Zoo run; RF093 native executed F4 receipt/ready and queue schedule/application; RF092 original SPC and RF091/RF090 original CPU clocks; RF088 native CPU ports; 13 raw WRAM/SRAM pairs, observer-off baseline, independently verified actual bytes and uncalibrated clock domains kept separate
- Release gate credit: **0**

Only advance this marker after confirming there is no already executing or
qualifying equivalent source-bound campaign for the same causal question.
The wrapper's preflight must reject an incidental marker edit or an
unrelated source change before the expensive producer runs.
