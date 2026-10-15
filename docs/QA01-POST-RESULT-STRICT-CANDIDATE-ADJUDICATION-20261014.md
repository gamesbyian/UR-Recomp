# QA-01/07: separate result-onset candidates from original/native post-result lifecycle

**Scope:** independent gameplay-evidence classification. Original/native
timing implementation remains with Opus, and release-quality gate status
remains exclusively with independent release QA. **No accepted USA events
are established here (0/45); 4 partial, 41 officially unverified.**

## The exact uncovered gate

The existing `tools/probe_original_event_complete.py` can report a
`paired_event_candidate` when archived original controller input, source
entry, course residency, sampled in-race semantic state, settled result PPU
text and guest-relative result onset agree. It stops at stable result +6
by default. A *strict candidate* from this comparator has never been a
completed 45-event acceptance: original game execution after the result,
menu restoration, next event and persisted progression are separate required
observations.

The opt-in `--source-followthrough` collector (merged #1596/#1605)
already preserves **six** real post-result capture offsets measured
relative to independently observed result onset, at **+8, +16, +24, +32,
+64, +72**. Its three distinct clocks must remain distinct:

- Reset-anchored **original source SMV frame** (e.g., Zoo 8353 + offset).
- Fresh Snes9x **host frame** = independently measured fresh race entry +
  its own guest-relative result frame + offset.
- Fresh Baldosa **host frame** = independently measured native race entry +
  its own guest-relative result frame + offset.

Both fresh guests supply actual captured, hashed 128 KiB WRAM; the original
source trace supplies the source menu, course ID, in-race byte and frame.
These source/guest rows are bounded samples, **not** full execution traces,
SRAM checkpoint proofs, or guarantees about unobserved intermediate frames.

## New independent scientific disposition

The *existing*, manual-only `tools/qa01_event_campaign.py` classifier
now consumes optional producer follow-through in addition to the strict
result-onset predicate and emits `evidence.post_result_bounded`:

| Disposition | Meaning |
| --- | --- |
| `not_observed` | The producer never requested follow-through. No lifecycle conclusion. |
| `sampled_named_divergence` | At least one sampled original movie/fresh reference/native named-state disagreement. Includes earliest sampled result-relative offset, exact differing field names and source/guest distinctions. |
| `six_sample_triplet_named_agreement` | All six source, fresh original and native sampled semantic named states agree, **not** the intermediate unsampled frames or a complete course. |

The campaign verifies that sample offsets and original movie frames
match the *source event*, that each fresh host receipt is its own actual
entry/result+offset, that observed menu/course/race bytes and gameplay
counters are true integers, and that all producer yes/no equality assertions
follow their own displayed values and full-WRAM fingerprints.
Missing, duplicated, changed or over-promotional evidence is
`producer_error`, never a scientific negative or an accepted event.
The cross-case aggregator also checks that a case receipt has a valid
nonpromotional post-result disposition. Unchanged existing
`strict_candidate` / `strict_divergence` classifications continue to
refer **only** to the original producer's result-onset contract, and
`release_credit` stays exactly zero.

A semantic mismatch is reported even if the primary result comparator
calls the event `strict_candidate`. Conversely, even six matching
samples cannot earn event credit or substitute for real SRAM persistence,
menu navigation, complete guest execution or exact Windows candidate
identity. The mechanism cannot launder a native frame-lag rebase.

## Battery SRAM is now independently sampled, but not yet reload-tested

The same opt-in producer already had genuine full SRAM files available at
each of the six post-result `dump` statements; they were simply ignored.
Source-qualified Snes9x `snesref` writes `<tag>.sram.bin` (independently
used by `tools/probe_track_records_sram.py`). The pinned Baldosa
`snesrecomp/runner/src/state_dump.c`, lines 180–182, writes exactly
the live cartridge `cart->ram` and `cart->ramSize` on the same script
command. Neither subsystem needs a patch or a new runner.

The owning gameplay producer now **requires and reads the authentic full
8,192-byte battery image from each fresh original/native guest** at
`result+8,+16,+24,+32,+64,+72`. It independently hashes the full images
and decodes all **three** Crawler track rank entries from the established
original SRAM Track Records table, without writing or normalizing bytes:

- first table word `0x0422 + 2×(50×rank + track)`;
- corresponding rider-holder byte `0x0550 + 50×rank + track`;
- 150-word table checksum, stored `0x054E` and independently calculated.

`track` is source-qualified course index 0–4, never a transient scratch
course-ID overwritten during the result. A checksum disagreement *during*
a write/update interval is an observation, not permission to repair the
game's battery image. Full image equality is reported independently from
three-rank course-record equality, avoiding incorrect attribution of an
unrelated save byte as a gameplay-result defect.

The case classifier checks real SRAM size, SHA-256 shape, course/rank
identity, numeric ranges, checksum claims and all source/native pairing
booleans; malformed or partially missing six-sample SRAM evidence is
`producer_error`. Historical reports without this new opt-in SRAM material
retain explicit `not_observed`, with **no retroactive evidence promotion**.
The bounded outcome is attached under
`post_result_bounded.fresh_original_native_battery_sram` and provides
the first observed record/full-SRAM disagreement offset, if any.

**Scope limit:** these are *fresh Snes9x/native live battery-backed SRAM
images*, not a third SRAM snapshot from the 2014 original tour at the
same moment. The original archived movie still supplies input/state
identity, but earlier tour events can change its historical SRAM.
Most importantly, a live dump does **not** prove that a desktop process
flushed its save correctly or that a clean second process reloaded the
same bytes. `cold_process_persistence_proven` remains **false** even
when all six 8-KiB image pairs match and the Crawler record table is
well-formed. No official QA-01/QA-07 event gains credit from this alone.

## Immediate consequence for Opus RF-015 research

[PR #1608](https://github.com/gamesbyian/UR-Recomp/pull/1608)
reports that the disposable pinned Baldosa DRAM refresh correction moves
Zoom Zoo result onset from native **+5162** to **+5163**, matching the
original **+5163** with unchanged original/native input and source.
This creates an **investigative strict result candidate**, but its
separate follow-through already reports that at the actual **result +16**
the original movie and fresh Snes9x still have Circuit menu
`0xBC`, while the corrected Baldosa guest has returned to
`0xF6`. The Opus report identifies the fuller boundary as
race-relative **+5180** original versus **+5179** native.
The earliest discrepancy in the *six archived fixed samples* is +16;
**do not misrepresent that as the first divergent execution frame**.
That timing diagnosis is Opus-owned (RF-017), not a gameplay-logic
correction this lane can implement.

The first acceptance-producing replay after the Opus correction is
integrated is therefore the **exact corrected executable** replayed
with `selected=zoom-zoo`,
`baldosa_refresh_beam_rate=true`, and
`source_followthrough=true` on the existing manual QA-01 campaign
(where that optional input exists after #1608 is merged). Its result
should show result-onset candidate and a separately adjudicated source
continuation, both SHA-bound to the single source revision. No hosted
candidate re-execution or valid complete-event pass is claimed by this
document or the synthetic tests.

The shortest remaining causal question is original/native result+1…+2
(source `80:FAC9` / VBlank / `82:8035` NMI) at the exact corrected
code and clocks. Forward source PC, host/beam, guest memory and input
identity to Opus; **do not** shift the original movie, relax the
comparator or alter its runtime/source fix.

**Three-project reuse:** original SMV/Snes9x/native script and full-WRAM
snapshots from UR, source-pinned Baldosa product guest, and malmazuke
replay/finish lead have been checked. This adds neither another emulator
runner nor a new workflow, CI factory, release ledger or 45-case oracle.

## 2026-10-15: close the Zoo postframe observation gap before further theory

The optional original/native `--zoo-terminal-phase` probe previously captured **+5156..+5173** consecutively. It stopped *before* RF-015's observed Zoom Zoo result-screen return difference at **+5179 native / +5180 original**, while the separate source follow-through samples only +8, +16, +24, +32, +64 and +72 from each result onset. The first mismatch among those six observations (+16) cannot be promoted to the actual first divergent guest frame.

The owned producer now extends the existing **independent fixed guest race-entry-relative postframe observer to +5156..+5186** (31 consecutive original and native snapshots; same archived input). No new guest, runner, event acceptance rule or CI workflow is created. In addition to the existing same-relative and same-absolute-host comparisons, it reports a `contiguous_post_result_observation` covering the overlapping post-onset range with separately named **first observed** differences in (a) named fields, (b) gameplay fields, (c) raw `7E:009F` text cursor, and (d) whole-WRAM digests. The last three are *different evidence classes*: cursor/raw WRAM changes alone cannot establish a differing event decision, and no postframe alone locates a divergent source CPU instruction. The report explicitly denies CPU writer proof, cold-process SRAM persistence and release-event credit. Unit fixtures create a corrected-onset (+5163/+5163), return-edge (+5179/+5180) negative example; they are not original-emulator observations.

**Next execution, scoped to one decision:** manually run the *existing* `qa01-event-campaign.yml` with `selected=zoom-zoo`, `baldosa_refresh_beam_rate=true`, `zoo_terminal_phase=true` and `source_followthrough=true` on the reviewed SHA. Preserve exact native ELF and original core/ROM/movie hashes, original and native entry-frame receipts and the fixed-frame `reference.log`/`native.log`. Verify the first differing **source-qualified observed postframe** against the original source movie and distinguish same-guest-relative from same-host comparisons. Only if it identifies a genuine timing/logic difference should Agent 5 receive a bounded CPU/beam/PC handoff. If the original/native first changed field is only `wTextPos` or free-running scratch, locate its live reader and upstream instruction before calling it a gameplay defect. Stop if the next observation cannot change the strict decision; do not run a 45-course breadth sweep.

**Current execution status:** this instrument change carries no new executed original/native receipt and no corrected full-event admission. Pending an actual matching full source/result/return/progression and cold-process persistence witness, the authoritative ledger remains **0/45 complete USA events**. The existing `strict_candidate` is an onset-level investigative label and cannot be expanded by this diagnostic.
