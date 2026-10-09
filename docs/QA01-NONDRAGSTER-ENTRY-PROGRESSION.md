# QA-01: non-Dragster entry progression blind spot

**Evidence class:** corrected measurement coverage, not an observed native gameplay
bug, course completion, or independent emulator parity pass. Updated
2026-10-09. The canonical denominator lives in
[`ORIGINAL-COURSE-EVENT-CENSUS.md`](ORIGINAL-COURSE-EVENT-CENSUS.md).

## Reproduced harness omission

Before this correction, `tools/probe_original_non_dragster_course_entry.py`
accepted a fresh original/native Zoom Zoo or Jumps entry window when
player positions, P1 velocities, P1/P2 stored contact, P1 laps,
P1 boost, and raw clock bytes matched. **Neither player's checkpoint
nor finish gate was sampled**, and **P2 laps and velocities were omitted**.
A hypothetical native run with the *same positions and contacts* but
an improperly advanced P1 checkpoint/finish gate or P2 lap counter
would therefore have produced the same "passed_entry_window" verdict.

The input-only fresh-process route, exact USA-ROM hash check, both engines'
full decoded `7F:0000` course identity, selected original menus, fixed
relative samples `0,1,2,4,8,16,32,64`, and separate race-entry
calibrations are unchanged. This correction adds raw **USA retail**
per-player semantic fields to the compared output:

| Role | P1 WRAM | P2 WRAM |
| --- | --- | --- |
| X/Y speed, signed words | `04B7/04BB` | `04B9/04BD` |
| Persisted contact, unsigned word | `0E95` | `0E97` |
| Next checkpoint, unsigned word | `1199` | `119B` |
| Finish gate, unsigned word | `119D` | `119F` |
| Laps remaining, unsigned word | `0EF1` | `0EF3` |

The P1/P2 speed and race-progression offsets are the existing established
`tools/uniracers_state.py` and
`tools/summarize_paired_player_slots.py` mappings. The P1/P2 contact
backing-store offsets are independently established for the USA ROM
in `docs/COURSE-CONTACT-MARSHAL.md`. They **are not portable** to the
PAL prototype or Europe retail, whose contact marshals differ.

## Fail-first counterexample

`test_phantom_checkpoint_finish_or_p2_lap_fails_at_first_bounded_frame`
constructs two identical valid 128 KiB active Zoom Zoo snapshots with
the *same* synthetic decoded course buffer, movement, stored contact,
boost and clocks. It changes only P1 checkpoint `0→1`, P1 finish gate
`0→1`, and P2 laps `3→2` in the native sample at relative frame
`+8`. The actual `sample_state`→`first_difference` path must report
exactly those three fields at +8. A second test records raw progression
registers on Jumps without asserting that a timed stunt uses race-lap
semantics. These are **synthetic test inputs**, not a claimed original
Snes9x or native discrepancy.

Run on a machine with the canonical repository and its test assets:

```sh
python3 -m unittest discover -s tests/unit \
  -p 'test_probe_original_non_dragster_course_entry.py'
python3 tools/probe_original_non_dragster_course_entry.py \
  --case zoom-zoo --snesref <snesref> --core <snes9x-core> \
  --native <native-executable> --work-dir /tmp/qa01-zoo
python3 tools/probe_original_non_dragster_course_entry.py \
  --case jumps --snesref <snesref> --core <snes9x-core> \
  --native <native-executable> --work-dir /tmp/qa01-jumps
```

## Admission boundary and next test

The synthetic regression closes a **known false-negative measurement hole**.
It does not demonstrate that original/native differ in the wild. The
8-sample entry probe covers only the first **64** guest-relative frames
in two of **45** USA course identities, no full circuit traversal,
timed-stunt expiry, terminal result or adversarial lateral finish
approach. It cannot advance the full-event ledger (still **0/45** USA
complete, **0/135** with PAL comparisons).

The priority runtime discriminator is a fresh input-only original/native
Zoom Zoo race-entry run followed by a scene-relative **multi-lap** trace
with both players' progression and stored contact, comparison of the
original's observed `3→0` non-lap wrap versus later `0→1` lap
decrement, and an instruction-time P1 dispatch trace before attributing
a particular C000 cell to frame 2903. Stunt courses need separate
timer, score, reward-consumption and actual result evidence; do not
count their incidental lap-register contents as race events.
