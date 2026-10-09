# Per-player course collision-word marshal and checkpoint dispatch

## Status

**ROM-authoritative for USA retail instruction structure.** Verified by
`tests/unit/test_course_contact_marshal_rom_contract.py` against the exact
canonical USA cartridge image, not merely names in an imported listing.

The original Nitrodon bank-81 listing supplies the investigative leads.
Each listed instruction sequence is also asserted against the ROM by CPU
address, and the retained native Dragster frame sequence independently
checks which values survive at the frame boundary.

## Recovered per-player brackets

| Stage | USA CPU | Instructions | Direction |
|---|---|---|---|
| P1 marshal input | `81:8D48` | `LDY $0E95; STY $0F09` | stored P1 collision word → shared current-player word |
| P1 contact/surface/collision | `81:8DD6` | `JSR $9E2A; JSR $8B95; JSR $8FB8` | construct contact geometry → sample course → resolve collision |
| P1 marshal output | `81:8DF3` | `LDY $0F09; STY $0E95` | shared result → stored P1 word |
| P2 marshal input | `81:8EA2` | `LDY $0E97; STY $0F09` | stored P2 collision word → same shared word |
| P2 contact/surface/collision | `81:8F2A` | `JSR $9E2A; JSR $8B95; JSR $8FB8` | same three-stage path for P2 |
| P2 marshal output | `81:8F47` | `LDY $0F09; STY $0E97` | shared result → stored P2 word |

The checkpoint handler at USA `81:805D` reads `$0F09` and masks
`#$1C00`; the object dispatcher at `81:82ED` also reads the shared word.
Neither function is entitled to treat the *settled end-of-frame* scratch
value as a permanent P1 collision record. During P1 processing it can
contain P1's value; during P2 processing it can contain P2's.

This is a provenance and course-object activation result. It does **not**
change the physics/contact calculation or infer an exact collision point.

## Independent native witness

Recovered original native object-activation artifact:
Actions run `36954104693`, artifact `11204794758`.
The reduced, provenance-bound seven-frame snapshot is
`analysis/data/dragster-finish-contact-transition.json`.

From guest frames 2901 through 2907:

- P1's stored word at `7E:0E95` changes from `0x1804` to `0x2024`,
  then `0x2020`, then `0x0022`.
- P2's stored word at `7E:0E97` remains `0x1804`.
- The end-of-frame `7E:0F09` equals P2's stored `0x1804` in every
  retained frame.

The **static handoff sequence** explains this pattern. P2 has a later
update bracket than P1, and the same scratch location is reused.
The snapshots alone cannot prove that every branch executed in every
frame, but they no longer present a contradiction with the dispatcher's
known shared-register input.

## Course-fidelity consequence

At guest frame 2902 the P1 word `0x2024` selects C000 slot 10, whose
runtime object code is `0x14`; the checkpoint/gate/lap state remains
`3/0/1`. At frame 2903 word `0x2020` selects C000 slot 8, still with
code `0x14`, while that state transitions to `1/1/0`.

Those words also appear in the actual native decoded 7F course buffer
at the predicted world-space finish cells, confirmed independently of
the ROM static contract by
`analysis/data/dragster-finish-live-course-cells.json`.

The next semantic investigation belongs at the **P1 instruction-time
contact-state / checkpoint handler** boundary. A frame-end read of
`0F09` is the wrong observation surface for assigning the P1 cell.
Do not widen collision activation or change guest physics while
investigating this state.


## Handler control-class discrimination

USA checkpoint handler 81:805D..8063 loads the shared 0F09
and masks it with 0x1C00, choosing a branch class from those upper
control bits. All six retained frames selecting runtime object code
0x14 have contact words 0x2024, 0x2020 or 0x0022; **all three
yield masked value zero**. Thus the observed progression difference
cannot be credited to a different *masked handler class* merely because
the packed words select C000 slots 10, 8 and 9.

It is still possible for different frames to encounter different
preexisting lap/checkpoint/finish-gate states, object activation timing,
or contact positions. The retained snapshots and this masked-code
comparison do not identify which of those mechanisms caused the single
progression transition. A one-frame correlation must not be elevated
to proof that C000 slot 8 inherently means "finish" while slot 10
inherently means "checkpoint". Both are the same behavior code 0x14,
and the handler sees the same masked class for these recorded words.

## Regional portability boundary

The exact USA address-transfer bytes are also pinned against the legacy-beta
cartridge, where the corresponding bank-81 instructions remain identical.
The initial PAL retail/prototype test deliberately failed: neither PAL build
contains these USA six-byte register-transfer sequences in the tested local
neighborhoods. PAL timer and gameplay fields have known operand/layout
changes, so the USA `0E95/0E97/0F09` addresses must **not** be exported as
PAL authorities without separate homolog and runtime-register evidence.
The course model remains regional-data-aware, while this marshal claim is
currently **USA/legacy-beta only**. This is an actionable research boundary,
not a claim that PAL omits per-player collision bookkeeping.


## Direct dispatcher-side player-source transfer (bank 82)

The per-player course-object dispatcher has its own directly recoverable
input boundary, separate from the bank-81 collision processor:

| Player | USA frame dispatch input | Observed instructions | Object dispatch |
|---|---|---|---|
| P1 | 82:89BB | LDY $0E95; STY $0F09 | 82:8C32 JSL $8182E2 |
| P2 | 82:8EC3 | LDY $0E97; STY $0F09 | 82:911C JSL $8182E2 |

These exact bank-82 instruction bytes are asserted in the USA cartridge
regression. Each player stored contact word is restored to shared scratch
before its course-object dispatch call. Bank-81 contact/surface processing
updates the same per-player backing field through a separate call path.

This supports a specific next frame-phase discriminator: the word visible
at the end of guest frame 2902 might be read by the next player-one object
dispatch, explaining why the observed 0x2024 and the finish-state transition
land in adjacent frame-end snapshots. This is an **inference about call
scheduling**, not yet a confirmed one-frame causal delay. An
instruction-time trace at 82:89BB / 82:8C32 and 81:8DF3 is needed.


## Race frame ordering: course dispatch precedes new surface sampling

At USA 83:CD4E the main race path executes JSL $8289B5, entering the
bank-82 per-player object/update sequence. The P1 object dispatch
within that path reads the stored P1 collision word at 82:89BB and
calls 81:82E2 at 82:8C32. Its P2 counterpart reads its backing word
at 82:8EC3 and calls the same handler at 82:911C.

Only **later in the same caller sequence**, at 83:CD73, does the code
execute JSL $818D14, the bank-81 per-racer contact-shape/surface/collision
update. The USA ROM bytes for both long calls and the bank-82 wrapper
are now pinned in tests.

This gives a concrete frame-phase model for the retained Dragster tail:
a postframe P1 word 0x2024 seen at guest frame 2902 can be the *stored
input* to the next frame's object dispatch, which first mutates
finish/checkpoint state at guest frame 2903, while that frame's later
surface sampler produces postframe P1 word 0x2020. This is consistent
with the observed transition and both handler gate snapshots.

The call order is ROM-proven for this main-race path. The strict
one-frame dispatch-input equality still depends on the path being
followed and no intervening call modifying the saved contact word;
an instruction-time trace is the final discriminator. No collision,
lap, checkpoint or frame timing logic has been changed.


## Phase-corrected interpretation of the Dragster finish transition

The earlier statement that frame 2903's *postframe* contact word
0x2020 (C000 slot 8) "selects the finish handler" should not be
read as proof it caused the **same frame's** state transition.
Two independently recorded domains need to be aligned:

| Frame | Stored P1 word at frame end | C000 slot/code | Finish state at frame end |
|---|---|---|---|
| 2901 | 1804 | 2 / 12 | 3 / 0 / 1 |
| 2902 | 2024 | 10 / 14 | 3 / 0 / 1 |
| 2903 | 2020 | 8 / 14 | 1 / 1 / 0 |
| 2904 | 2020 | 8 / 14 | 1 / 1 / 0 |

The bank-83 main-race call order is **course-object dispatch first,
new contact/surface sampling afterward**. On the normal path, the
object dispatcher starts from the previously persisted player's
collision word. Thus the highest-priority instruction-time hypothesis
is that the frame-2903 checkpoint/finish transition was driven by the
word 0x2024 / **slot 10 from frame 2902**, while frame 2903's new
postframe 0x2020 / slot 8 sample was produced *after* that handler call.

This distinction is material for an eventual course editor or
checkpoint/finish test. Declaring slot 8 a "finish" cell and slot 10
a "checkpoint" cell from simultaneous postframe data alone would
assign semantics to the wrong input phase. Both belong to resource
0x24, both select the same 0x14 runtime object handler, and both
have masked control class zero.

The phase-corrected source-candidate join is implemented in
tools/correlate_dragster_finish_spatial_event.py and regression-tested
against the seven native frames. It resolves 0x2024/slot10 to
world X=25280, Y=816/848/880 and the newly sampled 0x2020/slot8 to
X=25280, Y=800/832/864. The join is **not** a CPU trace: other
writes between frames and the actual contact-point Y are not
established. The decisive next observation is an instruction-time
trace of shared word 0F09 at the P1 bank-82 dispatch/81:82ED and
handler 81:8050 while frame 2903 executes.


## Narrow finish-handler gate and lap mechanics (ROM-verified)

The USA handler itself supports a more specific, *conditional* account
of the frame-2903 result than generic slot proximity alone:

- At 81:8055, the handler reads `$0EF5,Y` and skips if nonzero.
- At 81:805D..80A2, it masks the current-player contact word with
  `0x1C00` to select a control branch; `0x2024`, `0x2020`,
  and `0x0022` all select the **zero-class** branch.
- At 81:80AA it reads `$119D,Y`, skipping an already-set finish gate.
  Otherwise 81:80B2..80B3 increments/stores the gate.
- On the continuing zero-class finish path, 81:8195..81A2 marks a
  state flag at `$0D11` and decrements `$0EF1,Y` (laps remaining).

Exact instruction bytes for the zero-class branch, finish-gate guard,
and lap decrement are regression-pinned in
`test_course_contact_marshal_rom_contract.py`.

In the native Dragster frame-end pair, the gate/laps values change
from `0/1` at frame 2902 to `1/0` at frame 2903.
That pattern is **mechanistically consistent** with the previously
stored `0x2024` word selecting the zero-class handler on frame 2903,
provided the live per-player `0EF5` early-exit gate allowed it.
It does not prove the actual dispatcher contact word, the live
`0EF5` condition at handler entry, or the contacted Y cell.
The previously asserted slot-8 same-frame trigger remains unproven.

## Independent 2014 original Dragster complete-race result (2026-10-09)

The preserved original Snes9x 2014 movie is no longer only a
startup/menu timing counterexample. Its historical workflow run
`37184022134`, artifact `11296685866` includes a raw
`7E`-WRAM write trace of **669,690 records** covering first Dragster
course entry through original results. The reduced original-only
trace result is retained in
`analysis/data/dragster-original-2014-race-result.json`.

The original active-race frame **794** has P1 world `(1088,801)`,
checkpoint 0, gate 0, laps remaining 2. The corresponding decoded
USA header coordinate pair x16 is `(1088,800)`. Actual original
event writes:

| Original movie frame | Course state [checkpoint, gate, laps] before → after | Original raw stopwatch |
|---|---|---|
| **1031** | `0/0/2 → 1/1/1` | `0/0/0/5/2` (~0.5s) |
| **1772** | `1/1/1 → 3/0/1` | `0/1/2/8/5` (~12.8s) |
| **2505** | `3/0/1 → 1/1/0` | `0/2/5/1/0` (~25.1s) |

The source result path then changes menu `0x00→0x84` at
**2835**, `0x84→0x16` at **2869**, clears `inRace`
at **2873**, and enters menu `0x99` at **2874**.
This is an **authentic original-only full race/result**; it is
not a complete same-input reference/native course fidelity pass.

The separately retained **native** Dragster frame-2903 window
observes the same *state-change shape* `3/0/1 → 1/1/0`,
but its previous stored P1 contact word `0x2024` differs
from the original run's `0x2020` near frame 2505.
Those two sequences use different player inputs and independent
guest timelines; matching this event-state pattern is not
instruction-time contact causality or native/original parity.

A short input-test-derived original stopwatch duration does not
automatically demonstrate a fully traversed lap: the first `2→1`
decrement at about 0.5 seconds is the start-line gate transition.
The later decrement `1→0` is the original path's next lap
event. The intermediate checkpoint `1→3` resets finish gate
without decrementing laps, another original counterexample to
the shortcut that any checkpoint-index change means a new lap.

`tests/unit/test_dragster_original_2014_race_result.py`
protects original source/menu/result observations, exact source
provenance, and the native-shape-but-not-parity distinction.
The complete original race strengthens the existing Dragster
**partial** course observation; the **0/45 full paired-event**
release denominator is unchanged.
