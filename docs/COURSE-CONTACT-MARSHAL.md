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
