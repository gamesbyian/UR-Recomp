# Authorized original/native Zoo causal experiment request

This file is an intentional **PR-driven trigger marker** for the existing
`.github/workflows/qa01-event-campaign.yml` native/original Zoo diagnostic.
It is **not** a second QA-01 plan, CI gate, release authority or gameplay
acceptance. The approved wrapper (installed separately) must run only on
`main` when *this exact file* is changed by a reviewed one-file request
PR. The marker must advance by **one** and give a new concrete reason.

The canonical campaign and independent QA continue to own source/WRAM/SRAM semantics. This **observer-on** request retains `selected=zoom-zoo`, `zoo_race_mesh=true`, `zoo_dp_window=true`, RF015 (`baldosa_refresh_beam_rate=true`) and RF017 (`baldosa_io_clock_order=true`), and enables both paired original/native observers. Merged RF091 now records actual original CPU-side $2140-$2143 writes **after** Snes9x's committed APU-port call, alongside RF090 returned reads and native RF088 port events. The original USA Zoo ROM/movie/seed are unchanged. The observer-off sequence-13 control already established sampled-state noninterference; do not rerun it. This case is diagnostic only, not a CPU/SPC clock-equivalence, full-event or release verdict.

## Next research request

- Request sequence: **14** (RF091 original committed APU-port write/read causal anchor)
- Requested reason: Run exactly one guarded original/native Zoo sequence-14 with merged RF091 original committed CPU $2140 write observer enabled alongside RF090 returned original reads and RF088 native port reads/writes. Preserve the original ROM/movie/seed, RF015/RF017, 13 raw +5034..+5046 WRAM/SRAM pairs, source/build hashes and sequence-13 observer-off control. Require real nontruncated original RF091 write rows, original first subsequent FFFF/FFAA/BBAA returned values, and native first write/read/ready rows; register each core's own clock axis and measure write-to-first-read and write-to-ready intervals without assuming cross-core clock alignment. If original write evidence is missing, capped or ambiguous, stop and report first failing discriminator rather than inferring SPC timing or changing CPU code. Retain exact source/log/receipt identities and compare unmasked +5039/+5040 bytes. No complete USA event or Windows gate admission.
- Observer mode: **on**
- Requested by: Project engineering agent, under owner autonomous engineering direction
- Evidence scope: same original/native Zoo inputs and 13 raw WRAM/SRAM pairs, RF091 committed original CPU port-write/read anchor versus RF088 native, sequence-13 observer-off baseline, independent artifact and separate-clock-axis review
- Release gate credit: **0**

Only advance this marker after confirming there is no already executing or
qualifying equivalent source-bound campaign for the same causal question.
The wrapper's preflight must reject an incidental marker edit or an
unrelated source change before the expensive producer runs.
