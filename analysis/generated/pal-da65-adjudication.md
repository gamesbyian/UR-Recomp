# PAL retail vs prototype: bounded da65 adjudication

Width-state provenance is independent of snes2asm.

| Probe | Range | Retail lines | Prototype lines | Same count | First differing line | Exact |
|---|---|---:|---:|---|---:|---|
| reset-init | `00:91D1..00:933B` | 133 | 133 | True | 0 | False |
| ppu-init-16bit | `00:A0DA..00:A11E` | 26 | 25 | False | 0 | False |
| joypad-helper | `00:D1D7..00:D1E8` | 9 | 9 | True | 0 | False |

Interpretation rule: equal instruction counts and long aligned prefixes support stable boundaries; early count/prefix divergence supports genuine structural change or a wrong independent mode assumption and should be escalated to Ghidra/xref inspection.
