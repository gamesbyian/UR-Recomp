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
