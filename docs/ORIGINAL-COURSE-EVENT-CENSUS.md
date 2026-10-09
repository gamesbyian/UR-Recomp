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

The initial release comparison matrix covers **three builds**: USA retail,
Europe retail and the 1994-11-29 PAL prototype. Thus there are **135
course/build cases**, comprising 108 race/circuit cases and 27 stunt
cases, or 27 cases for each event-slot family across builds. The historical
legacy beta remains a separate archival/reference build rather than a
mandatory release case. A complete `passed` entry must include the
original route and start, event-specific contact/checkpoint/lap/finish
(or stunt score/timer) and result, matched against a pinned Snes9x or
MesenCE run from an independently named native run, on a fresh process,
with exact ROM and candidate provenance.

The recorded baseline is **0/135 complete event passes**, **2/135
partial observations** and **133/135 unverified**, as encoded in
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

Every Europe-retail and PAL-prototype case remains unverified at L4.
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
