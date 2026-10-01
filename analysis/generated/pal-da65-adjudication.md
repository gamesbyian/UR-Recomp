# PAL retail vs prototype: bounded da65 adjudication

Width-state provenance is independent of snes2asm.

| Probe | USA anchor | Europe range / shift / sim | Prototype range / shift / sim | Lines E/P | Shape | Sizes | Exact |
|---|---|---|---|---:|---|---|---|
| reset-init | `00:91D1..00:933B` | `00:91D1..00:933B` / +0 / 0.997 | `00:91C8..00:9332` / -9 / 0.989 | 133/133 | True | True | False |
| ppu-init-16bit | `00:A0DA..00:A11E` | `00:A0E9..00:A12D` / +15 / 0.971 | `00:A0D1..00:A115` / -9 / 0.971 | 22/22 | True | True | False |
| joypad-helper | `00:D1D7..00:D1E8` | `00:D1E8..00:D1F9` / +17 / 0.944 | `00:D1D5..00:D1E6` / -2 / 0.889 | 8/8 | True | True | False |

Across these probes, instruction-shape agreement: **True**; instruction-size-sequence agreement: **True**.

Interpretation rule: USA recovered-code ranges provide independent M/X provenance, while raw-byte similarity independently locates each homolog in Europe and the PAL prototype. Equal da65 instruction counts plus shape/size agreement support stable boundaries despite relocation; only a remaining mismatch after homolog alignment should be escalated to Ghidra/xref inspection.
