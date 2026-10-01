# Racer-update structural island: A22B..A497

This report recovers structure, not semantic names. Boundaries are anchored by direct calls from the racer-frame update hub, explicit returns, exact cross-build table identity, and trusted-entry-seeded snes2asm.

## Recovered structure

- USA/beta routine 1: `82:A22B..A27B` (81 bytes).
- USA/beta routine 2: `82:A27C..A2D3` (88 bytes).
- PAL prototype routine 2: `82:A272..A2C4` (83 bytes).
- Europe retail routine 2: `82:A288..A2DA` (83 bytes).
- Inline lookup table: USA/beta `82:A2D4..A353`, prototype `82:A2C5..A344`, Europe `82:A2DB..A35A`.
- Following routine: USA/beta `82:A354..A497`, prototype `82:A345..A488`, Europe `82:A35B..A49E`.

## Five-byte PAL-line contraction

USA retail and legacy beta retain five consecutive NOP bytes at USA `82:A2B2..A2B6`. The 1994-11-29 PAL prototype and Europe retail omit those five bytes. This contracts the second routine from 88 to 83 bytes and moves the table plus following routine by an additional five bytes.

This is a lineage-aware function-boundary result, not merely a raw regional diff.

## Inline lookup table

The middle object is exactly **128 bytes / 64 little-endian words** and is byte-identical in all four builds.

USA words:

`0000 0000 0010 0010 0020 0020 0030 0030 0040 0040 0050 0050 0060 0060 0070 0070 0080 0080 0090 0090 00A0 00A0 00B0 00B0 00C0 00C0 00D0 00D0 00E0 00E0 00F0 00F0 0100 0100 0110 0110 0120 0120 0130 0130 0140 0140 0160 0160 0170 0170 0180 0180 0190 0190 01A0 01A0 01B0 01B0 01C0 01C0 01D0 01D0 01E0 01E0 01F0 01F0 0000 0000`

The following routine performs a long indexed load from `82:A2D4,X`, independently proving the block is lookup data rather than executable code. The table is therefore a stable cross-build structural landmark.

## Preserved unreachable instruction block

Trusted-entry-seeded snes2asm leaves exactly 13 bytes unreached inside the following routine in every build:

- USA/beta: `82:A484..A490`
- PAL prototype: `82:A475..A481`
- Europe retail: `82:A48B..A497`

The bytes are instruction-shaped in the recovered listing, but surrounding control flow jumps over the block and no direct bank-82 branch/call target to it was found. Treat this as a **preserved dead-code candidate**, not as data, until runtime or indirect-target evidence says otherwise.

## Why this matters

This island demonstrates the intended comparative-structure workflow: direct-call targets establish entries, cross-build relocation exposes a five-byte deletion, exact table identity establishes a code/data boundary, and independent reachability analysis identifies a preserved dead block. None of those require prematurely assigning gameplay semantics.
