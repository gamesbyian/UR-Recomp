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

## Executed independent full-WRAM byte audit (2026-10-15)

Source-pinned [Actions run 38820550442](https://github.com/gamesbyian/UR-Recomp/actions/runs/38820550442) produced a real **zero-exclusion, full 128-KiB original/native byte comparison**. Original/native producer exit **0**, independent strict event disposition `strict_candidate`, case ZIP artifact **12012881634**, ZIP SHA-256 **`f18765ede448224faea5701d228a9d78e68e591b7f6a8a03196a61d2ea6fa92b`**, effective checkout `32f3370fb3c207cc88cade54c8632ca17476411e`, original movie replay script SHA-256 `414cb0b1...`, RF-017 native ELF SHA-256 `869df40f...`. All provenance and each per-sample count/first address are permanently recorded in [the executed machine receipt](../analysis/data/qa01-zoo-unmasked-wram-20261015.json). The original artifact ZIP was independently downloaded and digest-verified; the resulting raw differences are fully enumerated (at most 15 differences in any snapshot versus 24 preserved first-difference slots).

| Real original/native window | Full 128-KiB pairs | Byte-exact pairs | First observed raw difference | Maximum differing bytes |
| --- | ---: | ---: | --- | ---: |
| 31 adjacent Zoo terminal frames +5156..+5186 | 31 | **1** | +5157: `7E:01F2` original `25` / native `27` | 15 |
| 6 genuine result-relative +8..+72 checkpoints | 6 | **0** | +8: `7E:01DF` | 15 |
| 11 next Bowl +259..+280 checkpoints | 11 | **8** | +266: `7E:01ED` | 4 |

Across all **48** complete-WRAM pairs only **27 unique WRAM addresses** differ: the low-bank contiguous range **`7E:01DE..01F6`** (25 bytes in stack territory), plus **`7E:2000`** and **`7E:2004`**. The last two appear *only at the authentic next Bowl active-entry frame*, Zoo-result-relative **+267**: `7E:2000` original `04` versus native `03`, and `7E:2004` original `40` versus native `80`. At the adjacent sampled frame **+268**, all **131,072 WRAM bytes** are identical. Source original and both fresh guests enter Bowl at +267; **all eleven complete 8-KiB SRAM pairs** are byte-exact, including the earned Zoo best lap 2510 and checksum 64622.

**Do not mask these bytes.** The `7E:01DE..01F6` region overlaps known stack traffic, but executed-PC equality and subsequent live reads at each sample are not yet established. RF-012 separately implicated a `7E:2000` transient list in earlier 2P result investigations, but that is a research lead, not source proof that the two entry-frame bytes are cosmetic or dead here. A bounded semantic/logic-frame contract requires independently established original writer, reader/liveness and state guard, plus falsifying mismatches; the strict comparator and acceptance semantics remain unchanged. No instruction-time or full-event credit follows from sparse raw convergence.

**Separate red job cause:** The authentic producer and strict classifier completed successfully. The overall case job failed later in optional cold-guest record reload because `qa01_cold_result_record.py` accepted only the older short replay script SHA-256 `04ad1c...`, while this unchanged-original-input next-Bowl schedule has SHA-256 `414cb0...`. This PR now adds an **explicit exact-source-identity guard for the extended replay** (pinned archived movie-window and verified +267 source/guest handoff), with adversarial negative tests. A separate real cold-guest execution is still needed before that scoped test can be called proven; even successful guest-process record loading would not certify host OS disk durability or hard-kill recovery.

**Acceptance:** still **0/45 USA**. Linux RF-017 Baldosa guest evidence is not an independently matched, fault-tested Windows product executable.

### Interpretation of the two non-stack bytes is now bounded

The repository's already-reviewed [RF-015/2P first-difference research](RESEARCH-FINDINGS-QUEUE.md#product-core-baldosas-result-phase-is-one-frame-short-rf-015-resolved-2026-10-14) associates **`7E:2000`** with the sound-command queue read index (`wSndQueueRead`), **`7E:2002`** with the queue write index, and **`7E:2004`** with an APU toggle. The same original/bsnes/Snes9x comparison found one-frame differences in this sound-queue region under otherwise matching gameplay, but warned that those do **not** by themselves prove a CPU–APU handshake defect. Reusing this *existing* identification is better than inventing a new mysterious gameplay variable.

In the executed RF-017 Zoo-to-Bowl repeat, only `2000` and `2004` differ outside stack territory, exactly at result-relative **+267**; **both agree at +268**. This makes an audio-queue/NMI timing boundary the leading *testable hypothesis*, **not** a proven liveness classification. A minimal next source experiment would read the original and native opcode-/writer-scope and APU-port transactions immediately surrounding each guest's **own** Bowl entry (**reference absolute host 6447, native 6449**), then test whether the mismatched bytes were read before being overwritten. Do not align the two hosts as the same instant, treat imported symbol names as executed source proof, or mask either byte. If the instrumented writes/reads are identical despite an observed host-frame difference, stop digging and retain the strict unmasked evidence as a sampled scheduler-phase observation. If a live read or sound command differs, hand that exact source scope to the CPU/APU owner rather than changing sound playback here.

A second independent actual original/native replay ([run 38820862424](https://github.com/gamesbyian/UR-Recomp/actions/runs/38820862424), retained case artifact **12013343141**, ZIP SHA-256 `1443916e1fff57973ec472e05d5d4b0819bd1b868533184a08f0aa18556b6885`) reproduced the three entire observer objects **exactly**: 31-frame Zoo terminal WRAM counts/values/hashes, six source result-followthrough WRAM and SRAM samples, and eleven real Zoo-to-Bowl handoff samples. The reference core was a distinct SHA-256, while native ELF, controller input and original USA ROM hashes stayed fixed. This is **execution reproducibility**, not full-frame, audio or release acceptance. Both independently downloaded ZIP digests matched the GitHub artifact digests. The [machine receipt](../analysis/data/qa01-zoo-unmasked-wram-20261015.json) pins both producer-report SHA-256 values and explicitly retains zero event credit.

## Executed RF-017 cold-guest ranked-record reload, no Windows durability (2026-10-15)

The first auth-extending `qa01_cold_result_record.py` execution now passes: [Actions run 38822170573](https://github.com/gamesbyian/UR-Recomp/actions/runs/38822170573), **all plan/build/case/aggregate jobs green**, exact experiment head `9f199ed38fdcd222fd08fd0b3b3ccbed30311014`. The real case artifact **12014320977** was downloaded and SHA-256 independently verified at **`3168afc0e2a84f4c61376a997b99aaddd6980a3acfe52e44e36aa90e6399d9c1`**. The source-qualified original/native producer again returned `strict_candidate` and exactly the same canonical original movie/window and corrected-native ELF identities; no controls or game runtime changed. The independent cold-guest artifact report binds its own producer-report SHA-256 `e3594950f09041cecc0d7098901ac7fa44b9ad4b17e4b1fbd8d4152b851ef804`.

The actual **fresh original Snes9x and fresh native Baldosa guest subprocesses** booted from **guest-produced** original/native Zoo result battery images with the same source seed SHA-256 `6f74bdf5...`. At **cold boot frames 300 and 420**, both guests independently reported MIKE's earned rank-zero Zoom Zoo lap **2510 centiseconds**, holder **0**, computed and stored table checksum **64622**; all 150 original/native record values and all 150 holder indices were separately SHA-equal at both boot samples. The freshly observed whole 8 KiB SRAM image SHA-256 was `b7bfa6aa...` on both guests and at both boot frames; **this differs from the original seed SRAM SHA-256**, so the claim is *preservation/reloading of earned ranked record layout*, not that every full SRAM byte remained unchanged across process initialization.

**Scope boundary:** this validates **two fresh Linux research guest processes consuming previously captured game-authored SRAM**. It does not exercise or certify actual Windows product autosave publishing, atomic/durable host disk writes, user-data root, hard-kill recovery or Windows playback from the source-pinned shipping executable. It does not prove 5,163 continuous instruction/logic-frame identity or any sound-queue live-read meaning. Machine-verifiable hash identities and the four boot observations are in the [same owning executed evidence receipt](../analysis/data/qa01-zoo-unmasked-wram-20261015.json), as `cold_guest_record_reload`. **Official complete-USA-course credit remains 0/45.** The previously red job was a test-harness input-hash whitelist defect, not a gameplay failure; the corrected exact-source admission and adversarial guard tests are retained.

## Opt-in whole-Zoo race checkpoint mesh: limits and stop rule

The ordinary exact-original/native 2014 Zoo result probe's default `sample_frames()` intentionally ends its regular 120-frame mesh at race-relative **+2400**, before the original scored Circuit result at **+5163**. Result-window and actual next Bowl source checks independently close the post-race journey, but do not sample the middle-to-late Circuit frames. A source-pinned, **opt-in only** `--zoo-race-mesh` now reuses the same producer, unchanged original movie/controller masks, 2014 source entrance/result qualification and fixed original/native fresh calibrated host clocks. It adds **24 race-relative checkpoints** (`2520, 2640, ..., 5040, 5100, 5120`) to the existing 0..2400 sparse named-state checks, stopping before the independently observed **+5124 transient 34-frame course-zero terminal prelude**. It does not mistake prelude course-state changes for an active Zoo race.

For **every** existing plus additional genuine original/native race checkpoint, the observer verifies one uniquely logged original dump and one native dump on their **independently measured entry-relative clocks**, requires complete **131,072-byte WRAM** from both, and enumerates every unequal byte with exact first-address, count and 256-byte page distribution (bounded first 24 byte-value details). Both source readouts are hashed. No stack-byte, sound-queue byte or alleged scratch-memory masking is permitted; full 8-KiB SRAM/result and dense terminal checks remain their separate exact existing observers. A missing, duplicated or wrong-clock sample, absent dump, or partial WRAM image fails closed.

This is a *bounded diagnostic*, not a 5,163-frame continuous comparison or CPU instruction/logic/NMI/APU parity witness. The result records **zero event credit**, the earliest *sampled* raw first difference, all retained sampled original/native named-state mismatches and exactly where late-race sampling now reaches. An apparently matching sample set proves nothing about unsampled intervening frames. It does not modify Windows build/OS persistence, the original source input, the main strict `diagnose` comparator, GHA default inputs or the independently owned release ledger. Use one source-qualified manual campaign run, backed by existing archived movie/core/native pins, then stop if the answer is purely repeat sampling without new decision-bearing gameplay findings.

### Executed full-Zoo sparse WRAM mesh (2026-10-15)

The one eligible Actions experiment, [run 38830671735](https://github.com/gamesbyian/UR-Recomp/actions/runs/38830671735), **completed all plan, build, case and aggregate jobs successfully** at exact source revision `2224b2414675c8191999510a9f6e6fcf40bf9a9c`. Actual original/native case artifact **12017545609** was downloaded, ZIP SHA-256 independently recomputed as **`886e533cf029f398af754699c6b7ba3c6a728623b6b7e4243469823bdcdb91f6`**, and the archived producer-report bytes hashed as **`d377ba95dbf5e77bae141980a6d5962bda1b34e300372db8ac075fdc00018a6e`**. Original USA ROM `859ec99f…`, 2014 movie `06dce29e…`, unchanged 2014 controller movie window `7b03f40e…`, original SRAM `a6af0ddf…`, corrected native Baldosa ELF `869df40f…`, source mesh replay script `2fec7f4c…`; exact source-bound binary provenance and all 66 checkpoint counts are retained in [the machine receipt](../analysis/data/qa01-zoo-fullrace-mesh-executed-20261015.json). This source script is intentionally a new SHA because **dump scheduling changed**, not controller masks.

The actual full-WRAM, **131,072-byte unmasked original/native** Census over **66** race-relative checkpoint pairs (including **24** newly captured original/native pairs after the prior +2400 limit) found **44 byte-exact pairs**, **22 differing pairs**, only **86 individual differing byte-occurrences**, and only **eight distinct SNES memory addresses** in the union. The 24 new checkpoints through authentic Zoo **+5120** are **18 byte-exact** and six non-identical. The early and middle source course is thus strongly sampled across the 5,163-frame active-to-result interval; **neither every intervening frame nor a CPU instruction/tick sequence was checked**.

| Observed original/native byte differences | Source meaning allowed by evidence |
| --- | --- |
| `7E:01ED–01F0` (four bytes at 21 sampled frames) | Low-stack region, *not* automatically ignorable without synchronized CPU PC, SP, writer/reader liveness |
| `7E:2000`, `7E:2004` (both at race entry +0 only) | Existing RF-015 sound-queue read index/APU toggle mapping; no instruction-/APU-port-level parity |
| `7E:0063` original `73` / native `4D`, and `7E:0069` original `BE` / native `97` (both only at **+5040**) | Direct-page non-stack late-race one-sample discrepancy, no executed liveness or downstream gameplay cause identified |

For the late direct-page discrepancy, original host frame is **6057**, native host **6059**, each independently calibrated from original +1017 and native +1019 entry. **All 131,072 WRAM bytes agree at the following sampled +5100** and also at +5120. Earlier R-SEED-018 research described `$0069` as an `82:8082` accumulator/run-variant byte in a different bounded investigation, but that is a *lead*, not proof of source-reader irrelevance here, and `$0063` is not assigned a writer/reader identity by this experiment. No byte, page, stack, direct-page, sound or NMI filter was introduced.

**Genuine scored outcome remained identical and unchanged:** no first decoded named-state disagreement across the 66 original/native sampled pairs; both independently observed actual Zoo result at guest-relative **+5163**; matching MIKE scored result and 25.10-second best lap; all six postresult full SRAM pairs and all eleven real Zoo→Bowl full SRAM pairs byte-identical; both guests plus authentic original source enter next active Bowl at result-relative **+267**. The separate full 31-frame terminal and 11-frame Bowl checkpoints continue to retain their earlier unmasked raw residual differences, not waived by this sparse racing mesh.

**Scientific conclusion:** the expanded *sampled* original/native Circuit gameplay state and actual next-course handoff pass; evidence is now more precise about the final 2,700 race frames, particularly the **+5040 `7E:0063/0069` direct-page** lead. Further source-opcode read/write tracing, if required to distinguish live CPU/APU state from scratch phase, belongs to CPU/APU research. No new automatic GHA workflow remains. Still **0/45 complete USA events accepted**; no shipping Windows disk process/storage result is claimed.
