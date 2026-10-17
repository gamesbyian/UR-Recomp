# RF-035: bounded IPL final-cycle comparator versus CC publication

**October 16, 2026. Proposed source-qualified falsification, NOT a shipping fix. USA 0/45.**

## Decision and preflight

RF-034 proves a *live* causal consumer: original Snes9x opcode `78 CC F4` at IPL PC `FFCF` reads the old CPU port value before CPU `$2140=$CC` becomes visible; native does so afterward. Its CC echo is read by the native CPU four local SPC cycles after the echo, matching the reference's local delay. A correction must affect the comparator's actual consumed value without inventing a clock-phase equivalence. The first last-cycle compare in native RF-026 is eligible only when `pad[0]==1`, `cpuCyclesLeft==0`, the real CPU CC write's stored target equals `portClock`, the IPL boot ROM and PC are live and old input differs. Otherwise the event order is unchanged.

The mandated three-project reuse selection for this lane favors the existing Baldosa native guest, UR original/native event producer, strict full-WRAM first-difference, original route masks and evidence envelope, and advisory malmazuke replay manifests. No second simulator or PAL oracle. Upstream pinned `baldosa/snesrecomp@075fbe4c8e0d97b0013be541795c39cb644a9709` uses queued CPU writes before SPC dispatch. Existing RF-026 moves SPC bus effects to the opcode's *last* cycle in disposable research guests, not shipping Windows.

## Smallest competing source model

`tools/qa01_rf035_ipl_compare_before_cc.py` modifies **only** that exact live IPL CC-at-last-bus-cycle collision after the original RF-026 stage. In that collision it invokes the original, unmodified `apu_drainPortQueue` directly **after** `spc_runOpcode` instead of directly before it, but before that same `apu_cycle` increments its clock. It does **not** defer to the next SPC cycle, alter any target, insert/delete a tick, move the `CMP $F4` read, rephase inputs or touch generated USA game C. RF-031's global target deferral and RF-029's global read shift are not revived. All other queue traffic follows the original path byte for byte.

This is deliberately IPL-specific and therefore **not a general implementation proposal**. If this counterfactual improves sound-pointer residuals without violating reference endpoints, it supports work on an instruction-phase source rule with no literal `FFCF`/CC special case. If unchanged or regressed, reject immediately; if the condition never fires, the needed RF-035 pad/debt boundary is not observed and the experiment is unadjudicated.

## Exact hosted A/B and stop rules

Compare the authenticated 2014 USA Zoo real ROM/movie/SRAM and exact controller mask script with the RF-034/control composite ZIP (run 38981131474, ZIP SHA256 `6efac6d4d1cf4f5a2b47b4b04c76d2b878a7312bc88641c2ac5e9921cb342052`), separate Snes9x core, native candidate ELF and all raw unmasked snapshot digests. Require full Zoo result **+5163** both, next Bowl active **+267** both, all **11 full earned 8192-byte SRAM pairs**, **78 complete 131072-byte WRAM checkpoints**, **13 adjacent +5034..5046 sound pointer/counter samples**, and the cold ranked-record guest reload. The baseline is 51/78 exact WRAM samples, 92 differing byte occurrences, +5040/+5045 one-byte sound-pointer differences, 13/13 equal transfer counters and eight unwaived Bowl stack bytes at +266/+280. Any missing sample/identity, worse fidelity, absent real comparator log, or regression in result/record/progression means **no correction**, no event credit.

Use one temporary branch-only workflow and retire it, together with temporary shared campaign input plumbing, as soon as the source run is dispatched. Independently review resulting artifact *before* deciding whether to promote a generic, source-correct correction. Do not touch Windows bridge, Modern storage, graphics or RELEASE-QUALITY-LEDGER.json.
