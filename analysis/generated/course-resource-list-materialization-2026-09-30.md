# Course resource-list / runtime-object materialization pass — 2026-09-30

This pass follows the newly identified runtime checkpoint/finish object code `0x14` backward through `Course_LoadAndMaterialize` at `82:E165`.

## Header word at decoded offset 0x000B is a mutable resource-list cursor

The Dragster decoded payload is `0x8417` bytes long. Its bytes at offsets `0x000B..0x000C` are `0F 84`, i.e. little-endian word `0x840F`.

The loader repeatedly:

1. reads the 16-bit word at `7F:000B`;
2. uses it as X, an offset into the decoded payload at `7F:0000+X`;
3. increments the word at `7F:000B`;
4. reads one byte at the old cursor position;
5. stops if that byte is `0xFF`;
6. otherwise treats the byte as a resource ID and materializes that resource.

This resolves the previously unexplained runtime mutation of decoded byte 11. The field changes from `0x840F` to `0x8416`, which changes only low byte `0x0F → 0x16`. The mutation is therefore not arbitrary course-state corruption: it is the loader advancing a cursor through a tail resource list.

Because the final cursor is `0x8416`, the terminating `0xFF` was read at offset `0x8415`. Dragster's resource-list span is therefore `0x840F..0x8415` inclusive: six resource IDs followed by `0xFF`. One decoded byte remains after the terminator at `0x8416`; its role is not yet assigned.

## Resource ID → descriptor → paired runtime planes

For every non-`FF` resource ID:

- `82:B2AD` indexes a five-byte descriptor table by `resource_id * 5`; in the course-load path the descriptor table base is `82:B7DA`;
- the descriptor supplies a source/index plus a size-like value in `$4B`, and `82:B2DA` performs the resource transfer/decompression path;
- `82:E30F` then indexes a separate four-byte table at `17:A000` by `resource_id * 4`, obtaining a 24-bit source pointer;
- data derived from that source is appended into the runtime plane at `7E:A000`;
- the same source pointer is transformed relative to `17:A0A4`, on a 32-byte granularity, into a paired source near `17:C4E4`;
- bytes from that paired source are appended into `7E:C000`.

The materializer keeps independent cumulative output cursors for the `A000` and `C000` planes.

This establishes a concrete architecture:

`decoded course header → tail resource-ID list → reusable bank-17 resource descriptors/templates → runtime A000 plane + runtime C000 behavior plane`

The runtime `C000` plane is subsequently queried by the object/collision dispatcher, where even code `0x14` selects checkpoint/finish behavior.

## Implications for the course format

1. The decoded RNC payload is not simply the final runtime map. It contains at least metadata plus a compact list of reusable resource/chunk IDs.
2. `7E:C000` behavior bytes are synthesized from bank-17 templates selected by those resource IDs.
3. To map checkpoint/finish `0x14` backward, the right route is now:
   - locate `0x14` cells and their runtime C000 offsets;
   - determine which appended resource span owns those offsets;
   - identify that resource ID;
   - inspect the corresponding `17:A000` four-byte pointer entry and paired source around `17:C4E4`;
   - then relate the resource ID back to its position in the decoded course tail list.
4. A future editor should probably model reusable course chunks/resources explicitly rather than assuming every course contains a monolithic raw object grid.
5. The six-resource Dragster list is small enough that reconstructing its per-resource A000/C000 output spans is now the highest-value next static/dynamic discriminator.

## Confidence boundaries

Confirmed by exact instruction flow:
- `7F:000B` is a mutable decoded-payload cursor;
- `0x840F` is Dragster's initial resource-list pointer;
- `0x8415` is the terminating `FF` position implied by the observed final cursor;
- resource IDs index both a five-byte descriptor table and a four-byte bank-17 pointer table;
- materialization appends paired data into `7E:A000` and `7E:C000`.

Not yet named:
- the exact semantic role of the A000 plane;
- exact descriptor field meanings in the five-byte `82:B7DA` table;
- the six Dragster resource ID values;
- the purpose of decoded byte `0x8416`;
- dimensions/orientation of each materialized resource chunk.

## Stop rule

Do not brute-force all bank-17 resources. The next useful step is to recover the six Dragster resource IDs and their cumulative C000 spans, because that is sufficient to attribute known checkpoint/finish code `0x14` to one or more source resources.
