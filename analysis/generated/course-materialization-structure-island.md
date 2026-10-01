# Course materialization structural island: 82:E165..E395

This island follows the full named course loader from its direct entry through resource-list iteration, VRAM/DMA staging, A000/C000 WRAM materialization and the common exit.

| Region | Size | USA | PAL prototype | Europe | Legacy beta |
|---|---:|---|---|---|---|
| setup | 107 | 82:E165..82:E1CF (+0, sim 1.000; op 42, unreached/data 0) | 82:E101..82:E16B (-100, sim 0.944; op 42, unreached/data 0) | 82:E12B..82:E195 (-58, sim 0.944; op 42, unreached/data 0) | 82:E165..82:E1CF (+0, sim 1.000; op 42, unreached/data 0) |
| resource_record_header | 67 | 82:E1D1..82:E213 (+0, sim 1.000; op 30, unreached/data 0) | 82:E16D..82:E1AF (-100, sim 0.896; op 30, unreached/data 0) | 82:E197..82:E1D9 (-58, sim 0.896; op 30, unreached/data 0) | 82:E1D1..82:E213 (+0, sim 1.000; op 30, unreached/data 0) |
| dma_row_loop | 234 | 82:E216..82:E2FF (+0, sim 1.000; op 101, unreached/data 0) | 82:E1B2..82:E29B (-100, sim 0.885; op 101, unreached/data 0) | 82:E1DC..82:E2C5 (-58, sim 0.885; op 101, unreached/data 0) | 82:E216..82:E2FF (+0, sim 1.000; op 101, unreached/data 0) |
| resource_materialize_A000_C000 | 132 | 82:E302..82:E385 (+0, sim 1.000; op 77, unreached/data 0) | 82:E29E..82:E321 (-100, sim 0.955; op 77, unreached/data 0) | 82:E2C8..82:E34B (-58, sim 0.955; op 77, unreached/data 0) | 82:E302..82:E385 (+0, sim 1.000; op 77, unreached/data 0) |
| exit | 14 | 82:E388..82:E395 (+0, sim 1.000; op 7, unreached/data 0) | 82:E324..82:E331 (-100, sim 0.929; op 7, unreached/data 0) | 82:E34E..82:E35B (-58, sim 0.929; op 7, unreached/data 0) | 82:E388..82:E395 (+0, sim 1.000; op 7, unreached/data 0) |

## Structural result

- All five USA partitions are fully analyzer-reached after trusted entry seeding: **257 opcode bytes / 297 operand bytes / 0 unreached bytes** across 554 bounded bytes.
- Europe retail preserves the same five-part structure at a constant **-58-byte** shift.
- The 1994-11-29 PAL prototype preserves the same structure at a constant **-100-byte** shift.
- Legacy beta is byte-identical to USA across all five partitions.
- The newly extended `resource_materialize_A000_C000` block has raw similarity **0.955** in both PAL-line builds; the common exit has **0.929** similarity.

## Structural boundaries

- `setup`: entry through DMA/pointer initialization.
- `resource_record_header`: mutable decoded-course resource cursor, `FF` terminator, descriptor resolution and per-resource row metadata.
- `dma_row_loop`: repeated 0x40-byte transfer rows with LoROM bank-wrap and VRAM progression.
- `resource_materialize_A000_C000`: copies the resolved resource payload into paired runtime planes at `7E:A000` and `7E:C000`.
- `exit`: restores the bank-82 vector at DP `$4F/$51` and returns.

Run 36854224907 is the ROM-backed evidence run. This is structure recovery, not a claim that every field inside the island is semantically named.
