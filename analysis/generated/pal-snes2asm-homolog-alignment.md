# PAL/prototype snes2asm after homolog alignment

Windows rescored: **32**.
Whole-window role disagreements at identical offsets: **3662**.
Role disagreements after local homolog alignment: **114**.
Reduction: **96.9%**.
Windows with zero role disagreement after alignment: **29 / 32**.

| Europe window | Proto shift | Raw sim | Role disagree same→aligned | M/X disagree same→aligned |
|---|---:|---:|---:|---:|
| `01:BB69..01:BEA3` | -17 | 0.971 | 445→0 | 30→0 |
| `00:ABA9..00:ADE2` | -31 | 0.616 | 296→91 | 62→15 |
| `00:D1D5..00:D37A` | -19 | 0.955 | 244→0 | 6→0 |
| `00:F4FF..00:F617` | -28 | 0.950 | 192→0 | 2→0 |
| `00:A082..00:A1F1` | -24 | 0.981 | 191→0 | 3→0 |
| `00:E217..00:E37A` | -28 | 0.961 | 191→0 | 14→0 |
| `00:B929..00:BA69` | -19 | 0.972 | 184→0 | 36→0 |
| `00:B6BC..00:B7B8` | -19 | 0.980 | 153→0 | 8→0 |
| `00:FAC4..00:FBC4` | -28 | 0.984 | 151→0 | 19→0 |
| `02:B16E..02:B224` | -22 | 0.923 | 126→0 | 4→0 |
| `00:F7F8..00:F88C` | -28 | 0.940 | 104→0 | 4→0 |
| `00:B102..00:B18C` | -13 | 1.000 | 98→0 | 5→0 |
| `00:91C8..00:933B` | -9 | 0.989 | 96→0 | 5→0 |
| `00:C3A9..00:C450` | -19 | 0.875 | 94→5 | 16→0 |
| `00:EFB8..00:F02A` | -28 | 0.983 | 87→0 | 0→0 |
| `00:C1EF..00:C268` | -19 | 0.934 | 84→0 | 8→0 |
| `00:A99C..00:A9F9` | -24 | 0.915 | 76→0 | 6→0 |
| `00:A85F..00:A8D3` | -24 | 0.915 | 74→0 | 0→0 |
| `00:C559..00:C5CA` | -19 | 1.000 | 73→0 | 2→0 |
| `02:B280..02:B2DC` | -22 | 0.978 | 72→0 | 12→0 |
| `00:EB07..00:EB60` | -28 | 0.978 | 71→0 | 3→0 |
| `00:8C49..00:8CCA` | -9 | 0.654 | 70→18 | 1→1 |
| `00:EF31..00:EF88` | -28 | 0.943 | 70→0 | 8→0 |
| `00:B07F..00:B0DB` | -13 | 0.914 | 63→0 | 0→0 |
| `00:8853..00:88B1` | -5 | 0.789 | 58→0 | 3→0 |
| `00:9372..00:93CA` | -9 | 0.989 | 58→0 | 0→0 |
| `00:9860..00:98B2` | -9 | 0.928 | 55→0 | 0→0 |
| `00:D4F0..00:D524` | -19 | 0.962 | 45→0 | 0→0 |
| `00:9568..00:95A4` | -9 | 0.918 | 38→0 | 0→0 |
| `00:B5FF..00:B625` | -19 | 0.974 | 38→0 | 1→0 |
| `00:94E2..00:9510` | -9 | 0.851 | 37→0 | 0→0 |
| `00:96F4..00:9718` | -9 | 0.946 | 28→0 | 5→0 |

Only disagreements that survive homolog alignment should be considered candidates for da65/Ghidra adjudication. Same-offset disagreement is retained as raw evidence but is not itself semantic evidence.
