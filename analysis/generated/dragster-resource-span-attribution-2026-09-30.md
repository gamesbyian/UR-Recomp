# Dragster course-resource span attribution — 2026-09-30

This pass combines three independent evidence surfaces:

1. the frame-exact course-load WRAM artifact from run `36517460851`;
2. `Course_LoadAndMaterialize` / `82:B2AD` descriptor semantics;
3. the project rule to prefer structural/relational fingerprints over identical addresses or IDs.

## Dragster resource list recovered

The decoded Dragster tail at `7F:840F` is:

```
01 02 14 24 16 18 FF FF
```

The loader's 16-bit cursor begins at `0x840F`, consumes six resource IDs, reads the terminator at `0x8415`, and stops with cursor `0x8416`. The byte at `0x8416` is a second `FF`.

Frame +43 catches the loader after it has advanced the cursor to `0x8412`; at that instant only resources `01` and `02` have completed materialization, while resource `14` is in flight. The runtime cumulative cursors are then:

- A000 plane: `0x0040`;
- C000 plane: `0x0002`.

That exactly matches the descriptor-derived spans of resources 01 and 02.

## Descriptor-derived materialization spans

`82:B2AD` indexes five-byte descriptors from the table selected by `Course_LoadAndMaterialize` at `82:B7DA`.

The descriptor fields used here are:

- byte 0 low 7 bits: source bank;
- byte 0 bit 7: compressed/special path flag;
- bytes 1-2: source offset;
- bytes 3-4: size-like value consumed by the loader.

In `82:E329..E380`, the size contributes:

- A000 output span = `size >> 2`;
- C000 output span = `size >> 7`.

For Dragster's six resources:

| Resource ID | Descriptor bytes | Source | Size | A000 span | C000 span | C000 range |
|---:|---|---|---:|---:|---:|---|
| `01` | `16 80 80 80 00` | `16:8080` | `0x0080` | `0x20` | 1 | `0..0` |
| `02` | `16 00 81 80 00` | `16:8100` | `0x0080` | `0x20` | 1 | `1..1` |
| `14` | `16 00 D9 00 02` | `16:D900` | `0x0200` | `0x80` | 4 | `2..5` |
| `24` | `16 80 FF 80 04` | `16:FF80` | `0x0480` | `0x120` | 9 | `6..14` |
| `16` | `16 00 DD 00 02` | `16:DD00` | `0x0200` | `0x80` | 4 | `15..18` |
| `18` | `16 00 E1 80 00` | `16:E100` | `0x0080` | `0x20` | 1 | `19..19` |

Total predicted spans:

- A000: `0x200` bytes;
- C000: `0x14` bytes.

The final runtime snapshot contains exactly a 20-byte C000 course-object span:

```
00 00 12 1C 00 00 14 14 14 14 14 14 14 14 14 02 02 02 02 02
```

## Checkpoint/finish attribution

The span boundaries make the attribution exact:

- resource `01`: C000[0] = `00`;
- resource `02`: C000[1] = `00`;
- resource `14`: C000[2..5] = `12 1C 00 00`;
- resource **`24`**: C000[6..14] = **nine × `14`**;
- resource `16`: C000[15..18] = four × `02`;
- resource `18`: C000[19] = `02`.

Runtime object code `0x14` dispatches to `Race_HandleCheckpointFinish`. Therefore, on Dragster, resource ID **`0x24` is the resource whose entire behavior-plane contribution is checkpoint/finish cells**.

This is a relational proof. The conclusion does **not** come from resource ID `0x14` resembling behavior code `0x14`; in fact resource ID `0x14` materializes behavior bytes `12 1C 00 00`. An ID/address-equality heuristic would have pointed at the wrong resource.

## Structural fingerprint lesson

For course-resource matching, use these features together:

- decoded-course incidence across the 45 tracks;
- list position / tour-slot context;
- descriptor compression flag and size;
- A000/C000 output-span ratio;
- source-pointer relationships;
- runtime behavior-code distribution;
- content signatures where available.

Numeric resource ID and absolute ROM address are useful evidence but should not define identity. Cross-build or cross-course equivalence should survive relocation/renumbering where possible.

## Next discriminator

Run the new corpus analyzer to extract all course tail resource lists and incidence fingerprints. Then:

1. find every course that selects a resource structurally equivalent to Dragster `24`, even if the numeric ID differs;
2. compare its descriptor shape and C000 behavior distribution;
3. test whether checkpoint/finish chunks share a stable structural family across race/circuit/stunt courses;
4. only then promote a game-wide semantic resource label.

This turns one course-specific attribution into a reusable route for decoding the rest of the course-resource vocabulary.
