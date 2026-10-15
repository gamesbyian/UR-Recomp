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
