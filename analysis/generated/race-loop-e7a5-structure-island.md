# Race-loop E7A5 structural island

USA `83:E7A5..EBCB` is a race-loop support routine called from the recovered orchestrator at `83:CD3D`. USA/legacy beta end at `83:EBCB`; the PAL-line builds contain inserted/rewritten blocks and therefore grow before the separate 26-byte helper that precedes the already-recovered EC46 step table.

| USA bytes | PAL prototype | Europe | Legacy beta |
|---:|---|---|---|
| 1063 | 83:E79B..83:EBEF (size 1109; delta +46; shifts -10->+36; match 938/1109; edits 106; op 414; other 0) | 83:E7C1..83:EC13 (size 1107; delta +44; shifts +28->+72; match 870/1107; edits 130; op 414; other 0) | 83:E7A5..83:EBCB (size 1063; delta +0; shifts +0->+0; match 1063/1063; edits 0; op 400; other 0) |

## Boundary and divergence result

- USA retail and legacy beta are byte-identical at 1,063 bytes.
- PAL prototype starts at shift `-10` but ends at `+36`, yielding 1,109 bytes (+46).
- Europe starts at `+28` but ends at `+72`, yielding 1,107 bytes (+44).
- All four regional extents are fully analyzer-reached code. The PAL-line variants contain many small operand/code edits plus several inserted blocks, so a single constant-shift opcode comparison is invalid for this routine.
- The regional exits are anchored by the accepted EC46 step-table homologs: the excluded EBCC helper remains 26 bytes immediately before that table in each build.
