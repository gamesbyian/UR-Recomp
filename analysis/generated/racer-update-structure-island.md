# Racer-update structural corridor: A22B..AA6D

This report recovers structure, not semantic names. The corridor is connected directly to `Race_UpdateRacersFrame`, the named vertical-acceleration routine, and the known input decoder.

## Coverage

The recovered USA/beta corridor spans **2,115 contiguous bytes** from `82:A22B` through `82:AA6D`.

Bounded regions:

- `A22B..A27B`: routine
- `A27C..A2D3`: routine
- `A2D4..A353`: 128-byte / 64-word inline lookup table
- `A354..A497`: routine
- `A498..A5F2`: routine
- `A5F3..A617`: routine
- `A618..A6F0`: routine
- `A6F1..A8C1`: routine
- `A8C2..A967`: routine
- `A968..A9AB`: `Player_ApplyVerticalAcceleration`
- `A9AC..AA08`: routine
- `AA09..AA69`: sibling routine
- `AA6A..AA6D`: long-entry wrapper into the known input decoder at `AA6E`

All code entries above are independently supported by direct calls, adjacency after explicit returns, or an already-promoted semantic anchor.

## Cross-build relocation

The USA/beta corridor is structurally preserved in the PAL prototype and Europe retail.

Before the `A27C` contraction, the first two routines use prototype shift `-10` and Europe shift `+12`. The PAL lineage omits five USA/beta NOP bytes inside the second routine. From the 128-byte table onward, the corridor therefore uses prototype shift `-15` and Europe shift `+7`.

This piecewise shift persists cleanly through the gravity anchor and input-wrapper boundary.

## Five-byte PAL-line contraction

USA retail and legacy beta retain five consecutive NOP bytes at USA `82:A2B2..A2B6`. The 1994-11-29 PAL prototype and Europe retail omit them.

Consequences:

- USA/beta `A27C` routine: 88 bytes.
- PAL prototype / Europe homolog: 83 bytes.
- The following table and every downstream routine in this corridor move by an additional five bytes.

## Inline lookup table

The table is exactly **128 bytes / 64 little-endian words** and byte-identical in all four builds.

The following routine performs a long indexed load from the table base, proving the object is lookup data rather than executable code.

USA words:

`0000 0000 0010 0010 0020 0020 0030 0030 0040 0040 0050 0050 0060 0060 0070 0070 0080 0080 0090 0090 00A0 00A0 00B0 00B0 00C0 00C0 00D0 00D0 00E0 00E0 00F0 00F0 0100 0100 0110 0110 0120 0120 0130 0130 0140 0140 0160 0160 0170 0170 0180 0180 0190 0190 01A0 01A0 01B0 01B0 01C0 01C0 01D0 01D0 01E0 01E0 01F0 01F0 0000 0000`

## Preserved dead-code candidates

Two instruction-shaped blocks are consistently left unreached by trusted-entry-seeded snes2asm and are jumped over by surrounding control flow:

- USA/beta `A484..A490` (13 bytes); prototype `A475..A481`; Europe `A48B..A497`.
- USA/beta `A794..A7A5` (18 bytes); prototype `A785..A796`; Europe `A79B..A7AC`.

No direct bank-82 branch/call target into the first block was found during the bounded check. Both should remain **dead-code candidates**, not data, unless runtime or indirect-target evidence establishes reachability.

## Structural bridge to named semantics

The anonymous corridor terminates in several stable boundaries that connect it to existing semantics:

- `A968..A9AB`: `Player_ApplyVerticalAcceleration`, already promoted from Nitrodon plus instruction semantics.
- `A9AC..AA08` and `AA09..AA69`: adjacent sibling routines with fully reached instruction streams in all builds.
- `AA6A..AA6D`: tiny JSR/RTL long-entry wrapper into the known input decoder at `AA6E`.

This turns a large section of the per-frame simulation call graph from undifferentiated disassembly into a sequence of bounded structural units.
