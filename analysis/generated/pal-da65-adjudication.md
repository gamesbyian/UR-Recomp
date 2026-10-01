# PAL retail vs prototype: bounded da65 adjudication

Width-state provenance is independent of snes2asm.

| Probe | Range | Retail lines | Prototype lines | Same count | First differing line | Exact |
|---|---|---:|---:|---|---:|---|
| reset-init | `00:91D1..00:933B` | `00:91C8..00:9332` | -9 | 0.989 | 133 | 133 | True | False |
| ppu-init-16bit | `00:A0DA..00:A11E` | `00:A0C2..00:A106` | -24 | 0.957 | 26 | 24 | False | False |
| joypad-helper | `00:D1D7..00:D1E8` | `00:D1C4..00:D1D5` | -19 | 1.000 | 9 | 9 | True | False |

Interpretation rule: the raw-byte shift establishes the homologous region independently of snes2asm. Equal da65 instruction counts support stable boundaries despite relocation; count divergence after a high-similarity raw alignment is a stronger structural-change signal and should be escalated to Ghidra/xref inspection.
