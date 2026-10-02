# Course presentation-contract sample validation

Deliberately small cross-course invariant check, not a 45-course census.

| course | dims | coarse grid | fine records | C000 slots | A000 bytes | all checks |
|---|---:|---:|---:|---:|---:|---|
| 1 (Dragster baseline) | 256x4 | 1024x16 | 32 | 20 | 640 | yes |
| 9 (128x8 race) | 128x8 | 512x32 | 736 | 216 | 6912 | yes |
| 5 (32x32 circuit) | 32x32 | 128x128 | 607 | 199 | 6368 | yes |
| 6 (16x64 race) | 16x64 | 64x256 | 463 | 144 | 4608 | yes |

Validated invariants:

- header dimensions multiply to 1024;
- runtime expansion yields 16,384 coarse sectors and an exact 0x8000-byte u16 coarse table;
- 0x800F to the resource cursor is an integral number of 32-byte fine records;
- every coarse reference stays inside the fine-record table;
- every normal packed surface word selects a C000 slot inside the materialized resource span;
- A000 materialization is exactly 32 bytes per C000 slot.

This is enough to treat the Dragster two-level spatial/resource shape as a reusable family invariant for Widescreen-facing queries while still deferring a full-corpus/editor-format census.
