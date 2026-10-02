# Racer packed-word low-two-bit audit — 2026-10-02

## Result

The remaining packed-word low-byte bits 1..0 do **not** affect the bounded racer renderer consumer at `83:F190..F290`.

Static proof:

- `83:F209` reads the next packed 16-bit word.
- `83:F20F` stores the full word in direct-page workspace `$2A`.
- The accumulator's high byte is consumed through `XBA`, five shifts and `ORA #$8000`, producing the already-promoted `$1645,Y` staging value.
- The **only** later `$2A` read in the bounded consumer is `83:F21D`.
- `83:F21F` immediately applies `AND #$00FC`, so bits 1..0 are discarded before the second staging value is derived.

Therefore the correct semantic status is:

> **renderer-ignored in this consumer; producer-side meaning unresolved**

Do not label the bits as H/V flip, palette, priority, or another field without new producer-side evidence.

## Corpus census

The same audit scanned all **5,168** comparable monotonic frame records, covering **51,629** packed words.

| low2 | packed words | frames containing value |
|---:|---:|---:|
| 0 | 18,150 | 3,930 |
| 1 | 12,251 | 2,313 |
| 2 | 12,703 | 2,403 |
| 3 | 8,525 | 2,138 |

All four values are common. Low2 is not a pure function of either the high byte or bits 7..2, so the bits carry structured producer-side variation even though this renderer discards them.

## Falsified hypothesis

A direct source-tile H/V interpretation was tested against the 28 concrete VRAM bindings retained from the ordinary-2P snapshots. No destination tile matched the `$8000 + high_byte*32` source address under any of the four simple H/V transforms.

That hypothesis is rejected.

## Evidence

- tool: `tools/analyze_racer_packed_low2.py`
- successful workflow: **36978386973**
- expanded retained-snapshot workflow: **36978560724**
- canonical consumer: `83:F190..F290`
- canonical data surface: `analysis/data/presentation-assets.json`
