# QA-01: authentic 2014 Zoo-to-Bowl *next active race* handoff

**Owner:** original/native gameplay verification, QA-01/07. **Status:** RF-015 exact negative and independent merged RF-017 exact positive both executed and source-pinned; release credit remains zero. **Zero USA complete-event credit.**

## Decision-changing gap

The [RF-017 corrected-SRAM original/native Zoo evidence](QA01-RF017-CORRECTED-SOURCE-ZOO-20261015.md) proves matching observed menu/course/race state on all **31 original/native guest-relative +5156..+5186 frames**, plus **six exact full battery SRAM pairs** and a 25.10-second MIKE best lap. But the existing producer stops its genuine 2014 controller-window playback after **result+80** and collects its final SRAM image at +72. This reaches Crawler's next track menu (`0x16`) but **not the next actual course entry**.

The pinned, fully traced 2014 SMV enters the following **Crawler Bowl** race at original movie frame **8620**, 267 frames after genuine Zoo Circuit result frame **8353**. This is already established by the original Bowl source event and must be reconfirmed against the full archived movie, rather than inferred from a menu item.

## Smallest existing-tool continuation

The opt-in `--zoo-next-bowl`, valid only for the pinned native/actual Zoo case with `--source-followthrough`, extends the **same** original movie controller window to at least result +280. No input mask, duration, frame rebase, savestate or game execution change. Its replay script appends exact guest-relative samples at **+259, +263, +264, +265, +266, +267, +268, +269, +272, +276 and +280** after the existing +72 full-SRAM checkpoint. The dense +263..+269 subset can identify a one-frame next-course entry without calling any isolated active snapshot the first frame.

- The actual original reference movie source must independently prove continuous Bowl `track=2, in_race=1` at movie frames **8620..8627**, preceded by a non-Bowl-active frame at **8619**, and retain `menu/track/in_race` at every requested movie offset. Missing or contradictory original source is an error, never a guessed timestamp.
- Fresh **Snes9x** and **Baldosa** must each supply a complete 128 KiB guest WRAM and 8 KiB SRAM image, with every scripted dump host frame equal to **its own calibrated race entry + its own observed Zoo result onset + offset**. Their two host-frame axes and reset-anchored 2014 movie frames remain distinct.
- The observer reports all exact original/source/fresh native named-state triplets, the first **adjacently witnessed** Bowl active entry in each guest, full original/native SRAM hashes, MIKE's earned **2510-centisecond** Zoo ranked record/holder, score checksum and mismatching indices as negative science rather than exceptions.
- Missing guest dumps, wrong frame receipts, invalid SRAM length and fabricated original movie next entry **fail closed**; a genuine gameplay mismatch produces a report with `next_bowl_entry_triple_equal=false`, not admission.

The existing `qa01-event-campaign.yml` remains **manual/reusable only**, with an opt-in `zoo_next_bowl` input requiring `selected=zoom-zoo` and `source_followthrough=true`. It reuses the exact Snes9x/Baldosa binaries and baseline source-input producer, adding no second runner, automatic research factory or 45-course census. Synthetic tests defend masks, source/handoff guest clocks, actual 8KiB files, negative native course phase and release credit.

## Interpretation, stop, ownership

A positive observed next entry can support the first *complete post-result gameplay handoff* from Zoom Zoo into Bowl on this candidate. It does **not** by itself prove exact full WRAM or CPU instruction equivalence, whole movie, live two-player, actual Windows executable source identity, Windows filesystem autosave/hard kill or physical release readiness. Any imperfect new-race entry is a targeted original/native gameplay discrepancy; never change original controller timing merely to produce equality. CPU/APU clock implementation belongs to Agent 5. Independent Windows release QA alone may award the 12 release-quality gates, and the official complete-USA-event counter remains **0/45** until all independently required witnesses are accepted.

Stop after one successful source-qualified three-axis next Bowl entry under the corrected RF-017 candidate; only expand event families after the single strict complete event is independently admitted.

## First real RF-015 result, including preserved uncertainty

The source-only [run 38792983013](https://github.com/gamesbyian/UR-Recomp/actions/runs/38792983013) completed all original/native guest builds and replay jobs. Its actual case ZIP 12001491618 SHA-256 **a987ec94c1882e8ab734ff0916a7cad45a247ed1fd8c9638822b45ca61119f5e** matches GitHub's published artifact digest. The same canonical original movie confirms Bowl active at source movie frame 8620, Zoo-result relative **+267**, while the fresh Snes9x original likewise enters at **+267**. The RF-015-only native is still inactive at **+263**, but already active at **+265**. Because +264 was not in the first capture, the exact first native active frame is **bounded to +264 or +265**, not known as either one. The old observer correctly reported `fresh_native_next_bowl_entry_offset=null` rather than inventing an entry from nonconsecutive frames, but did not preserve that bracket transparently.

This new source/test commit adds the missing +264 sample and reports the `last_observed_inactive`, `first_observed_active` and `exact_observed_entry` frame separately for the original movie, Snes9x and native, never guessing when a sample is omitted. The first executed case also found unequal full 8KiB battery hashes on all ten samples +259..+280, despite the source-earned 2510-centisecond Zoo result, holder and score checksum remaining correct and equal. The first artifact did **not** archive the underlying full battery snapshots, so the actual count/offsets of differing bytes cannot be inferred from unequal hashes. The repeat adds exact byte count and the first eight differing offsets and byte values to the same bounded JSON receipt, with no new second runner.

**Scientific disposition:** under RF-015 alone the gameplay transition is early relative to the original next-course frame, not a strictly complete USA event. This is a genuine negative acceptance result, not a failed process. It does not predict whether Agent 5's RF-017 emitter correction will fix the +264/+265 discrepancy. The CPU code is not modified here and zero ledger/event credit is awarded.

## Executed RF-015 exact-frame and full-SRAM-byte adjudication

The follow-up [Actions run 38808439635](https://github.com/gamesbyian/UR-Recomp/actions/runs/38808439635) succeeded in all four original/native campaign jobs, actual case artifact **12008576657**, independently recomputed ZIP SHA-256 **`fe787e844236b956878f3048855e344f0eee9be304314f050eae293d859b1419`** (identical to GitHub digest). Source checkout `74c21398d9e8d4983d5b51c2abf86ad3d879e6a9`, real ROM `859ec99f…`, original 2014 movie `06dce29e…`, seed SRAM `a6af0ddf…`, original binary `cde6a6f…`, RF-015-only Baldosa binary `527015f…`; original and native race guest entries 1017/1019, Zoo result +5163/+5163, no input alteration.

The added **+264** sample closes the bracket from the first run. The actual original movie and fresh Snes9x each remain outside Bowl at result +266 and enter sustained Crawler Bowl at **+267** (original movie host 8620). RF-015 native remains outside Bowl at +264, but is **already active at +265**. Its first active frame is therefore proven to be **exactly +265**, **two original-relative frames early**. Its actual process host clock is separately recorded; do not shift its input stream or conflate guest-relative timing with simultaneous wall-clock presentation.

All **eleven** captured full SRAM pairs (+259, +263, +264, +265, +266, +267, +268, +269, +272, +276, +280) differ in **exactly three bytes**, with unchanged byte values across all checkpoints:

| Battery offset | Original Snes9x | RF-015 native |
|---|---|---|
| `0x0F31` | `0x1A` | `0x1B` |
| `0x0F33` | `0x02` | `0x04` |
| `0x10A7` | `0x0C` | `0x0D` |

The imported Baldosa mapping calls 77:10A7 `sCutsceneTimer2`, but **none of these bytes have source-original executed writer/reader semantics proven at this transition**. Do not interpret every non-record byte as a scoring failure or excuse a genuine two-frame active-entry discrepancy as cosmetic. MIKE's earned Zoo rank 2510, holder zero and recomputed/stored record checksum 64622 stay equal and valid throughout. These are *newly captured* game-authored battery images, not host disk-file persistence.

The permanent machine-readable original/native receipt is [analysis/data/qa01-zoo-next-bowl-rf015-exact-negative-20261015.json](../analysis/data/qa01-zoo-next-bowl-rf015-exact-negative-20261015.json). The exact-source patched RF-017 repeat uses a distinct disposable research branch based on merged CPU implementation, with no source ROM, controller, 45-course acceptance or shipping Windows changes.

**Do not award complete USA event credit:** still **0/45**. The next result must be read from the separately executed **RF-017** case, not inferred from the success of RF-017 at the earlier result-return transition.

### Independent-clock reconciliation: same host-entry frame, unequal result-relative interval

**Do not interpret the RF-015 native +265 versus reference +267 as a two-frame lead in absolute process time.** The native guest begins Zoo at host 1019 and reaches its result at host **6182**; the original Snes9x starts at host 1017 and reaches its result at host **6180**. Their genuine next Bowl active-entry captures are both at **absolute host frame 6447**:

- Fresh reference: `1017 + 5163 + 267 = 6447`.
- Fresh native: `1019 + 5163 + 265 = 6447`.

The original archived movie's absolute frame **8620** is a separate third clock axis and cannot be compared to fresh host 6447 as the same process. Hence the *strict source movie and fresh Snes9x Zoo-result-to-Bowl interval* is **267**, while the native interval is **265**, but the next Bowl first appears on exactly the same fresh host frame. The new observer and synthetic tests retain both the true absolute host entrance and separate per-Zoo-result interval, rather than calling one a universally early presentation. The three genuinely unequal SRAM bytes at aligned result-relative observations are a separate source-state question. This nuance does not waive the strict relative-event contract, nor give a complete-event credit.

## RF-017 integrated CPU correction: authentic next Bowl handoff passes on all observed axes

A separate disposable research branch from **actual merged RF-017 main `11501a15dea38fa912335cfc63103ce3a7208001`** reapplied exactly this gameplay-owned next-course observer to the existing source-pinned manual QA campaign, without modifying the integrated CPU patch or the original 2014 movie/button stream. [Actions run 38812512249](https://github.com/gamesbyian/UR-Recomp/actions/runs/38812512249) completed genuine original/native case replay with patched emitter verified as 89 generated files/15,484 in-order charge statements, unchanged total per basic block.

I downloaded actual case artifact **12008879784** and recomputed ZIP SHA-256 **`3fff228252d52a56843b7001aa3f65783757f0cf235ed1bafcb7c5dae91c345a`**, equal to its published GitHub digest. Actual workflow source checkout is `2e5fa490f423eb7866024dcf3d0d3429d080b49a`; source movie `06dce29e…`, source SRAM `a6af0ddf…`, corrected-native ELF `869df40f…`, reference Snes9x core `9949807d…`, and original 2014 input window `7b03f40e…`. Native original-SRAM loading uses the independently corrected `cwd/saves/save.srm` path, not the pre-#1654 wrong-root transport.

**All eleven actual source and fresh original/native named menu/course/racing-state triplets from +259 through +280 match.** Actual **Bowl active race begins at result-relative +267 on the original movie, fresh Snes9x and corrected Baldosa**, preceded by inactive Bowl at +266 on all three. This closes the RF-015-only native relative +265 timing discrepancy. Independently recorded absolute host Bowl entries are **6447** reference and **6449** native; they are not artificially shifted onto the same host frame. The source movie next Bowl active original frame remains **8620**, a distinct third absolute movie clock.

Even more decisively, **every byte of all eleven paired original/native 8,192-byte SRAM images matches**, from +259 through +280. The three former stable RF-015-only battery differences at `0x0F31`, `0x0F33`, `0x10A7` are **all absent**, while genuine earned MIKE Zoo record **2510**, holder zero, and stored/calculated checksum **64622** survive the actual next race start. The separately verified 31-frame RF-017 result-return window (+5156..+5186) likewise had matching named state, with 6 full SRAM pairs equal through +72.

**Scientific decision:** the *observed original/native Zoo result-return → actual following active Bowl entry* now matches on a source-correct, integrated RF-017 research guest in both event-relative state and complete sampled battery SRAM. The long CPU runtime fix is already owned and integrated; this PR only preserves original movie handoff evidence. **Do not label this entire 5,163-frame race and the next 280 frames instruction-exact, full-WRAM-exact, or an accepted complete USA event**. The 128KiB WRAM digests still differ in the result-return window, actual shipping Windows binary provenance and host-file durability/hard-kill recovery are not checked by this Linux research ELF, and physical/complete-source-gameplay acceptance remains separate. **Still 0/45.**

The full immutable decision is recorded in [analysis/data/qa01-zoo-next-bowl-rf017-integrated-positive-20261015.json](../analysis/data/qa01-zoo-next-bowl-rf017-integrated-positive-20261015.json), including all exact artifact, source and binary hashes. The disposable compute PR #1664 must remain unmerged and its temporary workflow removed; integration may merge this evidence and the manual-only observer without importing a second CPU implementation.

## Read-only complete-WRAM byte attribution for the next RF-017 replay

The already-executed RF-017 original/native handoff has **11/11 byte-exact
8-KiB battery pairs** but does **not** have byte-exact whole 128-KiB
WRAM receipts. Whole-WRAM hashes in the continuous Zoo result-return window
already disagree, starting at reported guest-relative +5163. A digest cannot
show whether disagreement is transient stack content, still-live state,
different CPU phase or a behavioral defect.

The existing `probe_original_event_complete.py` observer now includes
`audit_qa01_wram_pair`: it checks **every byte** of both real 128-KiB
images with **zero exclusions**, retaining the byte count, first 24
original/native address/value differences, complete counts for every
affected 256-byte page, both SHA-256s and first/last differing addresses.
The three existing consumers are: 31 consecutive +5156..+5186 Zoo
race-relative result frames, six original-source result-relative
followthrough samples (+8..+72), and 11 authentic next Bowl samples
(+259..+280). All guest host clocks remain independently checked; sampled
frame equality is not continuous event or instruction-time parity.
No original movie, input, CPU/APU implementation, field-mask contract,
strict comparator classification or release ledger is altered.

**Decision:** Reexecute one source-pinned RF-017 Zoo replay using the
*existing* reusable QA-01 campaign with Zoo terminal, source followthrough
and next Bowl flags, then inspect the first raw difference and the persistence
of its exact address/page across the windows. The small per-frame counts and
first addresses also go to Actions logs; full reports and the original raw
images remain the artifact authority. Do **not** declare stack writes dead
from their address alone. If a specific set of bytes is proven irrelevant,
write a separately reviewed *bounded* logic-frame semantics proposal,
retaining the unmasked first-difference record and falsifying cases.
The unchanged requirement for real Windows executable provenance and
OS-level durable cold-process recovery still blocks USA event admission.
