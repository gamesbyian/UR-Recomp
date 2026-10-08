# PAL course-contact register homology

## Question

A USA-only per-player collision marshal uses the persistent words 0E95
and 0E97 and the shared current-player scratch 0F09. A direct
byte-for-byte search for the same six-byte transfer instructions failed
in both PAL retail and the November 1994 prototype. Consequently, USA
WRAM addresses must not be copied into a PAL runtime contract.

## Existing independent executable correspondence

Both existing snes2asm homolog analyses show a zero-opcode-disagreement,
zero-role-disagreement alignment for the bank-82 race-frame marshal prefix:

| ROM | USA base | aligned shift | regional prefix entry |
|---|---|---:|---|
| USA retail | 82:89B9 | 0 | 82:89B9 |
| Legacy beta | 82:89B9 | 0 | 82:89B9 |
| PAL prototype 1994-11-29 | 82:89B9 | -3 | 82:89B6 |
| Europe retail | 82:89B9 | +19 | 82:89CC |

The role/opcode alignment is already recorded in the project's generated
USA/PAL homolog manifests. It does *not* imply that the operands are
unchanged. The prototype has 134 aligned operand-byte differences in
that region; Europe retail has 203.

## Scoped address decoder

The new tools/probe_pal_course_contact_registers.py reads the actual
LDY absolute / STY absolute instruction pair at the aligned player-one
entry in each preserved ROM. It extracts the **region's own** source and
destination operands. It then searches the neighboring P2 and bank-81
player-save/restore code for coherent source/destination pairs.

Ambiguous or missing candidate matches are reported explicitly and
cannot be promoted to an authoritative mapping. In particular,
matching a stored operand does not show that the same instruction
executes during a given PAL race frame.

Command:

    python3 tools/probe_pal_course_contact_registers.py       --json-out analysis/out/course-pal-contact-registers.json

The focus remains course/checkpoint evidence. The code does not modify
collision physics, input handling, player state, menus, or course
selection. Once actual PAL register identities are confirmed, the next
dynamic discriminator is a native/reference PAL race-contact snapshot
aligned to the correctly selected course.


## ROM-verified mapping, October 8 follow-up

Full canonical-ROM unit run reported unique, coherent bank-82 P1/P2
load pairs and all four corresponding bank-81 enter/exit transfers for
each build. Its preserved register report yielded:

| Build | P1 backing | P2 backing | Shared dispatcher word | Shift from USA |
|---|---|---|---|---:|
| USA retail | 0E95 | 0E97 | 0F09 | +0 |
| Legacy beta | 0E95 | 0E97 | 0F09 | +0 |
| PAL prototype 1994-11-29 | 0E99 | 0E9B | 0F0D | +4 |
| Europe retail | 0E9F | 0EA1 | 0F13 | +10 |

The per-build operand tuples and uniqueness are now regression-pinned,
not inferred from an unbounded similarity search. This closes the
**structural register mapping** across all four preserved builds.
Runtime state observation, dispatcher call timing and finish-line event
behavior in PAL remain separate empirical questions.

An important orthogonal course-data fact: the existing
analysis/generated/rnc-stream-manifest.json contains equal
unpacked SHA-256s for **all 45** course streams in USA retail, legacy
beta and the November PAL prototype. Europe retail differs at exactly
indices 4, 16, 20, 26, 27, 35 and 36. Thus PAL's +4 register relocation
is not evidence that the prototype uses different course bytes; the
same decoded course content can run against differently placed WRAM
fields.
