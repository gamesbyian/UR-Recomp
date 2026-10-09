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

## Preserved movie-input fingerprint

The separate authentic-input unit probe (#1008) decoded **1,810 original
controller frames** 3190..4999 as **116 nonzero runs** with 15 distinct
button masks. Exact raw 3,620-byte controller-window SHA-256:

`e77f10e4d652dfb2ed9afcf4c252e3e9f14e551a30edbbaa2a69ec50996f90b6`

This is the archived original source input, not yet evidence that either
newly booted guest completed Zoom Zoo under those inputs. The 1,811-frame
comparison extension includes the following sample at movie frame 5000,
and also retains the separate 1,810-frame exact-source fingerprint
regression before constructing any runtime comparison.

## Fresh-process paired semantic replay harness (proposed, not yet executed)

`tools/probe_historical_zoom_zoo_scene_parity.py` makes the above lead
executable without transplanting original guest state. It first confirms the
retained scene anchor and exact USA ROM, extracts **1,811 source input frames
3190..5000**, and boots both original pinned Snes9x and native Authentic
into Zoo through the same original menus with the same supplied SRAM.
Each engine's race-entry frame is measured independently in a calibration
run. Archived movie inputs are then shifted to those scene-relative frames,
and replayed after a fresh boot of each engine.

A 101-sample matrix compares menu/race state plus active-course X/Y,
velocities, persisted contact word, next-checkpoint, finish gate,
laps remaining, and boost. It retains the original 21 sparse phase
checkpoints and additionally captures **every guest frame** in relative
windows **190..230** and **590..630** (inclusive, no duplicate dumps).
Those are the neighborhoods of original Snes9x movie frames
**3400** (+210) and **3800** (+610), where the first exact USA-ROM
two-dimensional test found rider centers just **91** and **54** world X
units from a checkpoint-family cell with overlapping Y. The selected
capture windows are an explicit spatial hypothesis, not proof of
frame-specific guest contact. They target brief contact-word,
checkpoint-order and lap-gate transients that sparse observations
could miss. Source inputs, individual active-course checks and
reference/native calibration remain identical.
The script explicitly carries a `--phase` hypothesis (`-1`, `0`,
or `+1`) because the movie-frame/controller latch convention has
not been measured between runtimes. A different phase is an
experimental intervention, **not** permission to choose a flattering
result after discarding mismatches.

The supplied run SRAM is SHA-256 compared to the movie's archived
8 KiB SRAM and the result is tagged if it differs. By default this
is an **archived input transplant** between identically seeded guest
runtimes, not a verbatim reproduction of the 2014 race environment.
`--require-original-sram` rejects input transplant when the supplied
SRAM does not match the original movie's extracted 8 KiB SRAM. A
matching SRAM hash alone still cannot prove all emulator startup
variables are identical.

```sh
python3 tools/probe_historical_zoom_zoo_scene_parity.py \
  --snesref <snesref> --core <snes9x-libretro-core> \
  --native <native-executable> --rom <canonical-usa-rom> \
  --sram <supplied-sram> --phase 0 \
  --work-dir /tmp/qa07-zoo-scene \
  --json-out /tmp/qa07-zoo-scene.json
```

Both engines must demonstrate the previously calibrated course entry
frame again before accepting their replay snapshots. A mismatch
records the first guest-relative checkpoint, exact fields and values.
Only after determining whether it is phase, scene entry, contact,
lap or other guest behavior should the original simulation be changed.

**Validation status:** synthetic negative unit tests are provided.
No guest run of this extended comparator has been admitted here.
Passing the bounded sampled checkpoints would close only this named 1,811-frame
input-transplant experiment; neither an entire circuit result nor
the overall QA-01 45-course release requirement.

## Fail-closed course and active-window validation (2026-10-09)

The +1,800-frame benchmark has two especially dangerous false-pass modes:
both engines could carry an identical **wrong** course buffer despite the
menu reporting track 1, or both could leave the race early and subsequently
display the same menu/results state. Either condition would cause sparse
field equality to overstate fidelity to the archived Zoom Zoo race.

The paired runner now unpacks the exact canonical USA stream 2 and requires
the entire resident `7F:0000` course payload at **every observed active
checkpoint**, except the original loader-mutated two-byte cursor at
`0x0B..0x0C`. A wrong/partially loaded course causes explicit evidence
rejection even when both runtimes match each other. After comparing guest
state, it separately verifies that all 101 event-relative checkpoint samples
still show `inRace=1`, `trackID=1`, as expected for the archived original
movie through frame 5000.

A matched **premature exit** is retained as `reference_active_window` and
`native_active_window` diagnostics but makes the 1,811-frame active-window
result nonpassing. This check does not assert an early result is itself a
gameplay defect: scene phase, SRAM identity and input origin must first
be adjudicated. ROM-free regression tests cover identical early exits,
wrong resident course bytes and the authorized cursor exception.


## Original 2014 controller-byte provenance gate (2026-10-09)

A valid-looking SMV UID, NTSC flag, sample count and ROM CRC can survive
modification of its *controller bytes*. That would let both guest engines
faithfully reproduce a **different** sequence while a report mislabeled it
as preserved expert play. The full paired runner now rejects this false
archival claim **before starting either emulator** by comparing the exact
raw input bytes for source frames **3190..4999** against the independently
pinned SHA-256
`e77f10e4d652dfb2ed9afcf4c252e3e9f14e551a30edbbaa2a69ec50996f90b6`.
The existing 1,811-sample archive window remains available for report/input
chronology; its final sample at original frame 5000 lies **after** the
last compared guest checkpoint (+1800, source frame 4990). That final
unused byte is not silently described as pinned source evidence.

Unit tests mutate an otherwise valid SMV's controller byte while leaving
its header intact and prove the paired runner refuses it. The exact
original archive requirement is independent of `--require-original-sram`:
the latter controls how closely the fresh-run initial conditions match
the historic 2014 movie, while the SHA controls whether the source
**input intervention** is actually authentic.


## Event-state parity independent of early motion drift (2026-10-09)

The original/native replay now also emits
`event_state_diagnostics` through
`tools/summarize_zoo_scene_event_transitions.py`. On the original
and native observation streams independently it records every interval
where P1 `next_checkpoint (1199)`, `finish_gate (119D)`, or
`laps_remaining (0EF1)` changes. It also inventories changes to the
persisted P1 contact word `0E95` and decodes its C000 slot, separately
from progression and boost.

This is necessary because the **first raw mismatch** may be a harmless
initial position/velocity phase difference while the **first gameplay
progression mismatch** appears much later. The report now preserves the
earliest *sampled* disagreement in each of three independent dimensions:
checkpoint/lap/gate, stored contact and boost. Matching world positions
are not required for those questions, but any initial phase discrepancy
still needs adjudication before assigning a gameplay bug.

For any changed progression value, consecutive postframe samples can
localize the change only to that one guest-frame interval. The **prior
postframe P1 contact word** is retained as the hypothesis for next
dispatch input, alongside the newly sampled postframe word, following
the ROM-authoritative USA object-dispatch-before-surface-sample order.
Neither value is promoted as the instruction-time consumed word.
Transitions between sparse checkpoints are labeled
`sparse_interval_may_contain_multiple_events`, never assigned an
invented exact frame. An empty set of observed progression changes
does not mean a circuit or its result has passed.

The existing active-course identity gate and 101-checkpoint sampling
window remain intact. The new event summary is additional diagnostic
evidence, not a replacement for full event and result acceptance.
Validate its pure contracts with
`python3 -m unittest discover -s tests/unit -p
'test_summarize_zoo_scene_event_transitions.py'`.
