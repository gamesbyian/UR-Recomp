# QA-01: authentic 2014 Zoo-to-Bowl *next active race* handoff

**Owner:** original/native gameplay verification, QA-01/07. **Status:** first actual RF-015 replay executed; a two-frame-early native Bowl entry is observed and the follow-up exact-frame discriminator is running. **Zero USA complete-event credit.**

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
