# QA-07: 2014 original Snes9x movie, Zoom Zoo scene anchor

The preserved `reference/imported/tas-bots/dessyreqt-4250-submission.smv`
contains 8,767,529 recorded NTSC P1 samples, reset-anchored with embedded
SRAM. It is an authentic archived *input source*, but earlier absolute-frame
native playback diverged in menu onset. A frame-0 native/reference mismatch
cannot be promoted to an original guest physics discrepancy.

There is, however, a usable later scene candidate in **already retained
original Snes9x execution evidence**:

- The first original race enters at movie/reference frame **794**, and the
  first race results screen at frame **2874**.
- The original Snes9x `in_race_transitions` records a second `0→1`
  transition at **3190**.
- At frames **3400, 3800, 4200, 4600 and 5000**, the original
  sampled guest state is `inRace=1, track=1`. Per the canonical
  `trackID=streamIndex−1` mapping, that is **Zoom Zoo**, course:02
  (circuit A).
- The **native** guest at the same absolute movie frame 3400 is
  different. That is known startup/menu phase drift and is not itself
  usable as native/reference circuit or physics parity.

`tools/verify_historical_zoom_zoo_scene_anchor.py` enforces this retained
original evidence using
`analysis/generated/historical-2014-first-race-reference.json`,
`analysis/generated/historical-2014-first-race-replay.json`,
and `analysis/generated/historical-2014-smv-metadata.json`. Changing
the source movie UID, first race/results, second race-entry transition,
first observed course ID, or required subsequent checkpoint fails closed.
This verifier does not execute a guest or read ROM bytes.

It is now plausible to take a bounded original SMV input window beginning
at **3190**, use the existing separate archived scene-window extractor
when merged, and replay that window after both native Authentic and pinned
Snes9x independently enter Zoom Zoo through the original menus.
Rebase the original movie controller input relative to each runtime's
observed entry. Compare a dense checkpoint/contact/lap trace, not absolute
elapsed startup frames. Start with up to 1,810 scene-relative frames so
the already recorded frame-5000 original anchors provide upper bounds.
The exact **controller sample acts-before/after frame 3190** convention
requires an explicit ±1 guest-frame phase discriminator. A later complete
circuit result and native/reference event parity remain unverified.

Use `python3 -m unittest discover -s tests/unit -p
'test_verify_historical_zoom_zoo_scene_anchor.py'` for the pure guards;
`python3 tools/verify_historical_zoom_zoo_scene_anchor.py`
prints the candidate source provenance.

**Evidence label: original Snes9x temporal anchor, not an accepted
course completion, native parity result, or new gameplay bug.**
