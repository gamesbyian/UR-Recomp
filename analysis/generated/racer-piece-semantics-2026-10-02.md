# Racer packed-piece semantic recovery — 2026-10-02

## Scope

This pass closes the finite ordering question for the first ordinary-race racer-presentation family. It does not attempt full animation disassembly or assign names to unresolved packed-word flag bits.

## Mechanically recovered structure

The four-byte frame header is consumed as a 30-position occupancy lattice. The renderer treats the header in storage order, most-significant bit first, excluding byte 3 bits 1..0. That yields five consecutive six-position major groups:

- major 0: byte 0 bits 7..2
- major 1: byte 0 bits 1..0, then byte 1 bits 7..4
- major 2: byte 1 bits 3..0, then byte 2 bits 7..6
- major 3: byte 2 bits 5..0
- major 4: byte 3 bits 7..2

`83:F338..F3C6` and `83:F441..F4CF` reshape those six-position groups into the construction masks used by the renderer. `83:F1AE` initializes the construction cursor at `$8000`; `83:F1DC..F270` shifts that cursor once per constructed slot. Whenever the current occupancy position is set, the selected presentation-record pointer is read as one 16-bit word and advanced by exactly two bytes.

For the retained family, the consequence is deterministic: enumerate the 30 occupancy positions in the order above, discard clear positions, and pair the remaining positions one-for-one with packed words in stream order.

The exact table-bounded byte stream remains authoritative. All decoded records still round-trip byte-for-byte.

## Corpus check

A table-wide monotonic-boundary census found 5,168 comparable records. All 5,168 satisfy:

`record_length = 4 + 2 * popcount(the 30 renderer occupancy positions)`

Byte 3 bits 1..0 are zero in all 5,168 comparable records. Static renderer code does not place them into the recovered occupancy masks, so this report treats them as reserved-zero for the observed corpus rather than inventing a semantic name.

Evidence run: GitHub Actions run 36973753703.

## Packed-word contribution

For each occupied cell, the current 16-bit packed word is staged by `83:F20F..F227` in two independently recoverable pieces:

- high byte: `$1645,Y = $8000 | (high_byte << 5)`
- low-byte bits 7..2: `$15A1,Y = $0027 + ((low_byte & $FC) >> 2)`
- low-byte bits 1..0: still unresolved

Those are deliberately reported as staging transforms, not speculative tile/flip/palette field names. The current evidence is strong enough to reproduce the transform exactly but not to name every downstream meaning.

## Representative frame mapping

The canonical machine-readable mapping is emitted by `tools/extract_racer_presentation_family.py` into `analysis/generated/racer-presentation-family.json` and promoted into `analysis/data/presentation-assets.json`.

Examples:

- frame `0x0542`, header `38 c3 1c 70`: 13 occupied cells, 13 packed records
- frame `0x0544`, header `38 e7 1c 70`: 15 occupied cells, with the two extra occupied positions accounting exactly for the two extra records
- frames `0x0540` and `0x057E`: 13 occupied cells and 13 packed records each

Each emitted piece carries its major/minor occupancy slot, source header bit, packed-word index, exact word value, and the two proven staging values.

## OAM relationship

The packed records do not correspond one-for-one with OAM entries. The ordinary 2P evidence shows a later composition layer.

In retained run 36943103609:

- at `two-player-race-1220`, authoritative racer frame identities are `0x0542` and `0x0540`; sprites 96..99 use the stable racer OAM tile identities `0x88` and `0x00` under the split-screen seam;
- at `two-player-race-1420`, the authoritative identities have changed to `0x057E` and `0x0544`, while the same OAM tile identities remain.

Together with `82:ACA5`, this binds the layers: presentation records select/build the racer tile content, while later OAM composition places that content through stable sprite slots. Frame-specific piece variation therefore lives below the fixed OAM identity layer.

## Remaining uncertainties

The two low bits of each packed word remain unnamed. The recovered five-by-six lattice axes are intentionally called major/minor rather than X/Y until a direct spatial-orientation discriminator warrants stronger naming. Selector-dependent edge/orientation behavior around `$0C83/$0C85` is also left as a renderer policy detail; it does not change the recovered record ordering or word transforms.

This is sufficient to stop treating header/packed-word ordering as an open Phase-E blocker.
