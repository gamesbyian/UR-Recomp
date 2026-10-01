# Per-racer course runtime surface sampler: 81:8B95..8D13

ROM-backed run `36856034874` confirms this 383-byte routine as fully reachable executable code in all four preserved builds. It is called from both player paths after collision/contact-shape construction and before the later collision path.

## Cross-build structure

| Build | Range | Shift | Raw similarity | Opcode bytes | Operand bytes | Unreached/data |
|---|---|---:|---:|---:|---:|---:|
| europe-retail | `81:8B75..81:8CF3` | -32 | 0.971 | 167 | 216 | 0 |
| legacy-beta | `81:8B95..81:8D13` | +0 | 1.000 | 167 | 216 | 0 |
| pal-prototype-1994-11-29 | `81:8B75..81:8CF3` | -32 | 0.971 | 167 | 216 | 0 |
| usa-retail | `81:8B95..81:8D13` | +0 | 1.000 | 167 | 216 | 0 |

## Why this matters

- USA retail and legacy beta are byte-identical across the routine.
- PAL prototype and Europe retail both relocate the complete routine by exactly **-32 bytes** and retain the same 167-opcode / 216-operand shape.
- Europe and the prototype are not byte-identical to each other, so the shared relocation does not imply identical regional constants or operands.
- The suspicious Nitrodon linear listing around USA `81:8C03..8C1F`, which visually resembles stray `BRK`/`RTI` instructions, is fully classified as ordinary executable instruction/operand bytes by trusted-entry snes2asm. Treat that old appearance as width/context drift in the linear listing, not embedded data or exceptional control flow.
- The routine directly consumes both runtime course planes: `7E:C000` for behavior/orientation decisions and `7E:A000/7E:A001` for paired surface values. It therefore closes part of the semantic bridge from course materialization to per-racer collision/surface response.

## Call context

- P1 path: `81:8DD9 JSR $8B95`.
- P2 path: `81:8F2D JSR $8B95`.
- Both calls follow `JSR $9E2A`, the recovered collision/contact-shape constructor.
- Both precede `JSR $8FB8`, the later collision path.

The descriptive symbol `Course_SampleRuntimeSurface` is intentionally structural. Exact meanings of every A000/C000 value remain separate semantic work and should only be deepened where course/editor or physics implementation needs them.
