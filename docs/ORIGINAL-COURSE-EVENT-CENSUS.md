# QA-01 / QA-07: original course and expert-event acceptance census

**Status (2026-10-08): bounded L2 investigation, no L4 course/event completion pass.**
Release authority remains `docs/RELEASE-QUALITY-LEDGER.json`; this file
owns the denominator and the protocol for admitting a complete course result.

## Exact denominator and observation classification

`analysis/data/course-corpus.json` has 45 canonical USA stream-indexed
course identities, nine tours, and nine occurrences of each event slot:
Race A, Circuit A, timed Stunt, Race B and Circuit B. This is **ROM
content/identity evidence**, not a statement that an executable playthrough
has passed. The nine timed stunt courses have decoded `45` at header byte
2 and omit resource `0x24`; the other 36 courses contain that reusable
checkpoint/finish *resource family*. These facts do not identify a unique
contact cell, number of laps, gate order, finish plane or final result.

The primary Windows-original course release gate covers **45 USA-retail
cases**. A broader comparative matrix separately tracks **90 reference
cases** from Europe retail and the 1994-11-29 PAL prototype. Together
this is **135 course/build cases** (108 race/circuit and 27 timed stunt),
with 27 cases for each event-slot family across all three builds. The
comparison variants identify regional divergences; completing every
prototype case is not an automatic Windows shipping requirement. The
historical legacy beta is a separate archival build. A complete `passed` entry must include the
original route and start, event-specific contact/checkpoint/lap/finish
(or stunt score/timer) and result, matched against a pinned Snes9x or
MesenCE run from an independently named native run, on a fresh process,
with exact ROM and candidate provenance.

The primary-USA baseline is **0/45 complete event passes**, **2/45
partial observations**, **43/45 unverified**. Across all three builds,
**0/135 complete**, **2/135 partial**, **133/135 unverified**, as encoded in
`analysis/data/course-event-runtime-evidence.json`. Specifically:

- **USA Dragster (course 01), partial:** the seven-frame native WRAM
  progression witness observes the postframe checkpoint/lap/finish gate
  transition, but does not capture the instruction-time dispatcher value
  or demonstrate original/native all-event/result parity.
- **USA Jumpover (course 20), partial:** six bounded input-only
  original/native stunt landing-reward thresholds match **on a circuit B
  course**, but no complete circuit lap/finish/result or 45-second stunt
  event is established. All nine timed-stunt identities remain untested
  end-to-end.

Every Europe-retail and PAL-prototype case remains unverified at comparative L4.
No paired-ROM payload CRC, native unit test, static course-cell match,
or success on Dragster can be counted as a substitute.

Recompute the matrix and deny a forged/incomplete pass:

```sh
python3 tools/audit_original_course_event_coverage.py
python3 tools/audit_original_course_event_coverage.py --check
python3 -m unittest discover -s tests/unit -p 'test_audit_original_course_event_coverage.py'
```

The report is generated at `analysis/generated/course-event-qa-census.json`.
The observation register is intentionally small and must change only when
new original/native evidence is retained. The validator checks
completeness and source categories, **not** whether a witness is truthful;
reviewers still admit each candidate and exact trace.

The retained ROM-side evidence separates 42 nonzero numerical matches
between the optimizer's unused startX constants and header A.x×16, one
nonzero disagreement (Zoom Zoo), and two zero-value annotations whose
runtime interpretation is unknown (Jumps, Hill Climb). The source script
never reads startX when performing calculations. Numeric coincidence
is useful for track-identity reconciliation, **not** a dynamic spawn witness.

## Measured USA checkpoint-family cell census (2026-10-09)

The full-ROM placement job (`tools/audit_all_course_checkpoint_placements.py`,
unit log `QA01-45-COURSE-PLACED-CELLS`, PR #1014) confirms all **36/36
Race/Circuit** courses contain *placed* `0x24` cells, and all nine timed
Stunt courses are negative controls. There are **zero** Race/Circuit
courses which list `0x24` but have no placed 16×16 cell. This closes the
specific hypothesis that shipped races are missing the entire checkpoint
resource family.

However, **34/36** courses have *no candidate world cell in the exact
X column* of the historical optimizer's hand-entered finish-X number.
This is primarily evidence that the handwritten coordinate is not an
authoritative event predicate. It does not mean 34 courses are missing
their finish! ROM-static nearest horizontal gaps were 95 units for
**Zoom Zoo**, 30 for **Two Loops**, 28 for **To and Fro**, 27 for
**Hairpin Hill** and 26 for **Flat Fun** and **123 Jump**. Historical
positions are world X only and omit the Y component, racer collision
footprint, entry direction and checkpoint order.

The paired archived **original** Zoom Zoo movie preserves P1 world XY
at guest frames 3400/3800/4200/4600/5000 while still racing. The
follow-on `tools/correlate_zoo_original_positions_with_cells.py` uses
those exact Snes9x samples and all decoded candidate 16×16 rectangles
to report the nearest *two-dimensional* gap and candidate C000 slot
for each sample. This tests whether the historical 95-X-unit anomaly
survives comparison against actual executed world positions rather than
another handwritten coordinate. A geometric zero gap is NOT an
observed contact, handler instruction or lap/finish event: original
instruction-time `0F09` and previous-frame contact remain the required
causal witness. This work does not raise the 0/45 complete-event count.

```sh
python3 tools/correlate_zoo_original_positions_with_cells.py \
  --json-out /tmp/qa01-zoo-real-2d-cells.json
python3 -m unittest discover -s tests/unit \
  -p 'test_correlate_zoo_original_positions_with_cells.py'
```

## Non-Dragster counterexample priorities

1. **Zoom Zoo, USA circuit A (02):** historical hand-entered start X
   `8961` disagrees with `header.spawn_or_landmark_a[0] * 16`
   (`575 * 16 = 9200`). Treat this as a *static interpretation
   discrepancy*, not a proven wrong spawn. First correlate the live course
   load and guest start state with historical position, then collect a
   full lap/checkpoint/gate/result sequence. Test reverse approaches,
   repeated finish-plane contact and lap wraparound.
2. **Jumps, USA timed stunt (13):** the external optimizer hardcodes
   start X `0`, versus header candidate `262 * 16`. Its startX constant
   is never consumed by that script, so the zero is an **unqualified
   historical lead**, not demonstrated incorrect spawn geometry. The
   header has two distinct coordinate tuples and the stunt family
   deliberately has no ordinary `0x24` resource. Confirm runtime track,
   timer, scoring and two-player spawn before claiming any mismatch.
   Do not apply an ordinary lap/finish contract to a timed stunt.
3. **Regional course deltas:** Europe-retail course streams 4, 16, 20,
   26, 27, 35 and 36 differ from USA. The PAL prototype's 45 unpacked
   streams match USA but its live contact register operands relocate.
   Inspect actual runtime entry, decoded-cell activation and parity on
   representative *modified* Europe courses, especially Switcher (04)
   and Jumpover (20), before extrapolating.
4. **Expert-event discriminators:** L-shoulder flips, borderline
   landing contact, held-input combinations, repeated imperfect
   landings, boosts while airborne/offscreen, ground/side collisions
   and narrow pass/finish windows. Pin before/after exact guest-frame
   state and independently compare reference/native; distinguish
   transient progress, queued message IDs, pop-time reward and final
   result. Existing R-hold (22–25) and A-hold (4–5) cases are useful
   threshold seeds, not coverage of these other classes.

## Executable non-Dragster entry discriminator (QA-01 step 1)

`tools/probe_original_non_dragster_course_entry.py` now supplies two
**bounded original-menu input-only** reference/native probes:

- `--case zoom-zoo`: Crawler tour, second track, canonical USA stream 2,
  guest track ID 1, circuit A. Candidate for live spawn and repeated lap
  progression investigations.
- `--case jumps`: Shuffler tour, third track, canonical USA stream 13,
  guest track ID 12, timed Stunt. Candidate for 45-second score/timer
  acceptance. This must not be mislabeled a race/finish event.

Both drives use a recovered-SRAM fresh boot, the existing scripted original
menu state labels, and Snes9x vs native Authentic. They admit a snapshot
**only** if guest course ID, active-race state and entire decompressed stream
match the exact canonical USA ROM at `7F:0000` except the established
loader-mutated cursor bytes. They compare WRAM racer positions, velocities,
contact words, lap and boost fields, plus original-ROM timer digits at eight fixed relative
frames (0/1/2/4/8/16/32/64), including early P1/P2 candidate-header
spawn assignment.
There are no WRAM pokes. Any first discrepancy retains its frame and field
values, but capture-phase differences require a writer/phase diagnosis
before claiming guest semantics differ.

Example (use locally built Snes9x reference driver, core and native target):

```sh
python3 tools/probe_original_non_dragster_course_entry.py \
  --case zoom-zoo --snesref <snesref> --core <snes9x-core> \
  --native <native-executable> --work-dir /tmp/qa01-zoo \
  --json-out /tmp/qa01-zoo.json
python3 tools/probe_original_non_dragster_course_entry.py \
  --case jumps --snesref <snesref> --core <snes9x-core> \
  --native <native-executable> --work-dir /tmp/qa01-jumps \
  --json-out /tmp/qa01-jumps.json
```

Self-check without ROM or emulator:
`python3 -m unittest discover -s tests/unit -p 'test_probe_original_non_dragster_course_entry.py'`.

**Acceptance boundary:** these are runnable investigative probes,
**not successful guest executions in the retained corpus yet**.
Even a matching 64-frame window proves entry/start and initial timer semantics only.
Neither course may become a fully `passed` event/candidate row until
full checkpoint/laps/result (Zoom Zoo) or scoring/timer/result (Jumps) is
captured from each engine. Do not adjust the 0/45 release denominator on
the strength of a test fixture's existence.

## Archived expert-input route to first real timed Stunt result

The imported reset-anchored 2014 `dessyreqt-4250-submission.smv` contains
over 8.7 million original input samples. Its pre-existing first-race replay
`analysis/generated/historical-2014-first-race-replay.json` demonstrates
that **absolute frame-zero native playback is not aligned to the original
reference**: the original first-race entry is frame 794, while the native
screen at that same frame was still in menu flow. Those differences are
timing/phase counterexamples; assigning them to physics would be invalid.
Repeatedly increasing absolute-replay duration would not repair the
starting condition.

`tools/extract_historical_smv_scene_window.py` now selects a bounded
scene-relative input window (up to 24,000 samples) from the pinned original
SMV or its single-file ZIP wrapper. It validates the original movie UID,
sample count, P1 controller bit, NTSC/reset anchor, ROM CRC, controller
offset, reserved joypad bits and absence of reset markers *in the selected
window*. It outputs original input-run lengths and hash/provenance. When
given a **caller-measured** target race-entry frame it can rebase the
exact input masks to a fresh reference/native session. It intentionally
does not infer the actual movie's race-entry frame.

**Prospective expert-play experiment (not yet performed):**

1. First trace the Snes9x archive replay on the **original** core beyond the
   verified first-race window, sampling current track `7E:00CE`,
   active-race `0313`, current menu `009F`, five stunt timer bytes,
   boost and stunt-message ring. Source reconnaissance reports an active
   historical Bowl stunt run ending around movie frame 11867; treat that
   frame as a **search lead**, not a verified event timestamp.
2. Only after observing the exact first original Bowl (`course:03`,
   track ID 2) **race-entry** frame, extract enough of its original input
   timeline to cover scored gameplay, expiry and the actual Stunt results
   transition. Example with *illustrative* frame values:
   ```sh
   python3 tools/extract_historical_smv_scene_window.py \
     --first-movie-frame <verified-original-bowl-entry> \
     --frames <verified-bounded-stunt-window> \
     --json-out /tmp/bowl-original-input.json
   ```
3. Boot both original Snes9x and native Authentic into Bowl through the
   same scene-keyed menu route using the identical original SRAM. Measure
   their own `race-entered` guest frames and independently rebase the
   preserved controller input window to each; do not reuse the movie's
   absolute frame as a native timestamp or transplant a Snes9x freeze.
4. Compare scored-stunt message enqueues, queue-pop and actual reward,
   original clock countdown, results transition and final outcome. Classify
   first divergence at **event-relative guest frames**, with clear
   attribution of reset/host phase and score/physics differences.

The existing idle `ui-stunt-result-route.script` did **not** produce a
result at timer zero in either original or native Bowl. This hypothesis
tests whether *active archived stunt play* reaches results and whether
actual scoring/timeout handling agrees. The scene-window tool is an
input extraction seam only; **no full timed Stunt acceptance row is
promoted** until that paired run has executed and retained its outcome.

## Frame-2903 causal exclusion

The native artifact `analysis/data/dragster-finish-contact-transition.json`
observes P1 postframe word `2024` / C000 slot 10 at 2902, then
postframe `2020` / slot 8 with progression `3/0/1 -> 1/1/0` at
2903. Both select runtime object code `0x14` and both mask to the same
handler control class. The ROM-backed USA main-loop order dispatches
bank-82 course objects **before** bank-81 samples new contact. Thus
the preceding slot-10 word is the stronger **candidate** for the
frame-2903 dispatch input. No instruction-time capture yet proves
that value was consumed, and no 16x16 cell is definitively assigned
by the postframe snapshots.

The phase-correlation tool now refuses backward gate transitions or
multi-lap discontinuities and builds its explanation from the actual
frame and words rather than a hardcoded frame-2903 sentence. This
hardens **evidence interpretation**, not the guest's physics or lap
behavior. Next decisive trace: break at USA `82:8C32` (P1 object call),
`81:82ED` (shared word read), and `81:805D` (handler control class),
record `0F09`, `0E95`, `0EF1`, `119D`, per-player identity and guest
frame before and after; retain executed-PC chronology. PAL needs its
independently identified `0F0D` / `0F13` shared words and corresponding
instruction sites, not USA addresses blindly applied to relocated code.

## Admission / stopping rules

A static placement probe establishes only plausible cells. An L2 native
trace establishes only what that specific native run did. A paired
original/native state window establishes event-relative parity for that
window. A full L4 acceptance row requires an **actual** original-menu
launch, start, contacted course events in causal order, terminal result
and independently paired execution, with candidate/ROM hashes and
fresh-process reproducibility. Missing references remain `unverified`
or `blocked`, never `passed`. Where a failure is reproduced, preserve
input sequence, first divergent guest frame and exact WRAM/PC evidence
before modifying the authoritative game.
