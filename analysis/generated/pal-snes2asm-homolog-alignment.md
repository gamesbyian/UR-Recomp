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

## Surviving aligned role disagreements

### `00:ABA9..00:ADE2` → shift -31
- +`0x176`: Europe unreached 0xF9 vs prototype operand 0xDD
- +`0x177`: Europe unreached 0x07 vs prototype operand 0x0B
- +`0x178`: Europe unreached 0xFC vs prototype opcode 0x18
- +`0x179`: Europe unreached 0x0A vs prototype opcode 0x69
- +`0x17A`: Europe unreached 0x17 vs prototype operand 0x08
- +`0x17B`: Europe unreached 0x50 vs prototype opcode 0x8D
- +`0x17C`: Europe unreached 0xFB vs prototype operand 0xFD
- +`0x17D`: Europe unreached 0xFC vs prototype operand 0x0B
- +`0x17E`: Europe unreached 0x0D vs prototype opcode 0x20
- +`0x17F`: Europe unreached 0x18 vs prototype operand 0x5F
- +`0x180`: Europe unreached 0x50 vs prototype operand 0xA8
- +`0x181`: Europe unreached 0xFB vs prototype opcode 0xA9
- +`0x182`: Europe unreached 0xFC vs prototype operand 0x00
- +`0x183`: Europe unreached 0x10 vs prototype opcode 0x8F
- +`0x184`: Europe unreached 0x56 vs prototype operand 0xAD
- +`0x185`: Europe unreached 0x53 vs prototype operand 0x10
- +`0x186`: Europe unreached 0xFB vs prototype operand 0x77
- +`0x187`: Europe unreached 0xFC vs prototype opcode 0x60
- +`0x19A`: Europe opcode 0x20 vs prototype unreached 0x13
- +`0x19B`: Europe operand 0x47 vs prototype unreached 0x4C
- +`0x19C`: Europe operand 0xAD vs prototype unreached 0x45
- +`0x19D`: Europe opcode 0x6B vs prototype unreached 0x41
- +`0x19E`: Europe opcode 0xDA vs prototype unreached 0x47
- +`0x19F`: Europe opcode 0x5A vs prototype unreached 0x55
- +`0x1A0`: Europe opcode 0x48 vs prototype unreached 0x45
- +`0x1A1`: Europe opcode 0x08 vs prototype unreached 0xFB
- +`0x1A2`: Europe opcode 0xE2 vs prototype unreached 0xFC
- +`0x1A3`: Europe operand 0x20 vs prototype unreached 0x16
- +`0x1A4`: Europe opcode 0xA5 vs prototype unreached 0x4F
- +`0x1A5`: Europe operand 0xCC vs prototype unreached 0x50
- +`0x1A6`: Europe opcode 0x22 vs prototype unreached 0x54
- +`0x1A7`: Europe operand 0x3C vs prototype unreached 0x49
- +`0x1A8`: Europe operand 0x96 vs prototype unreached 0x4F
- +`0x1A9`: Europe operand 0x83 vs prototype unreached 0x4E
- +`0x1AA`: Europe opcode 0xC2 vs prototype unreached 0x53
- +`0x1AB`: Europe operand 0x20 vs prototype unreached 0xFF
- +`0x1AE`: Europe opcode 0x0A vs prototype operand 0xAD
- +`0x1B6`: Europe operand 0x02 vs prototype opcode 0xA5
- +`0x1B7`: Europe opcode 0x85 vs prototype operand 0xCC
- +`0x1B8`: Europe operand 0x78 vs prototype opcode 0x22
- +`0x1B9`: Europe opcode 0xAA vs prototype operand 0x3C
- +`0x1BA`: Europe opcode 0xE2 vs prototype operand 0x96
- +`0x1C0`: Europe operand 0x01 vs prototype opcode 0x0A
- +`0x1C2`: Europe operand 0x51 vs prototype opcode 0x0A
- +`0x1C3`: Europe operand 0x01 vs prototype opcode 0x0A
- +`0x1C5`: Europe operand 0x9A vs prototype opcode 0x18
- +`0x1C6`: Europe operand 0x01 vs prototype opcode 0x69
- +`0x1C7`: Europe opcode 0xC2 vs prototype operand 0xC0
- +`0x1CB`: Europe operand 0x00 vs prototype opcode 0xAA
- +`0x1CE`: Europe operand 0x01 vs prototype opcode 0xA9
- +`0x1DB`: Europe operand 0x01 vs prototype opcode 0xA9
- +`0x1DC`: Europe opcode 0xE8 vs prototype operand 0x1F
- +`0x1DD`: Europe opcode 0xE8 vs prototype operand 0x00
- +`0x1DF`: Europe opcode 0xE8 vs prototype operand 0x99
- +`0x1E0`: Europe opcode 0x1A vs prototype operand 0x01
- +`0x1E1`: Europe opcode 0x88 vs prototype operand 0x00
- +`0x1E4`: Europe opcode 0x20 vs prototype operand 0x00
- +`0x1E5`: Europe operand 0xD4 vs prototype opcode 0xA2
- +`0x1E7`: Europe opcode 0x22 vs prototype operand 0x00
- +`0x1E8`: Europe operand 0xBE vs prototype opcode 0xA0
- +`0x1ED`: Europe opcode 0x0A vs prototype operand 0x01
- +`0x1F2`: Europe operand 0x07 vs prototype opcode 0x1A
- +`0x1F3`: Europe operand 0x00 vs prototype opcode 0x88
- +`0x1F5`: Europe opcode 0xE2 vs prototype operand 0xF5
- +`0x1F6`: Europe operand 0x20 vs prototype opcode 0x20
- +`0x1F7`: Europe opcode 0xA0 vs prototype operand 0xB8
- +`0x1F9`: Europe operand 0x00 vs prototype opcode 0x22
- +`0x1FA`: Europe opcode 0xB9 vs prototype operand 0xBE
- +`0x1FF`: Europe operand 0x05 vs prototype opcode 0x0A
- +`0x200`: Europe operand 0x77 vs prototype opcode 0x0A
- +`0x205`: Europe opcode 0xC2 vs prototype operand 0x00
- +`0x206`: Europe operand 0x20 vs prototype opcode 0xAA
- +`0x20D`: Europe opcode 0x0A vs prototype operand 0xD4
- +`0x20E`: Europe opcode 0xAA vs prototype operand 0x00
- +`0x214`: Europe operand 0x07 vs prototype opcode 0x88
- +`0x215`: Europe operand 0x00 vs prototype opcode 0x10
- +`0x216`: Europe opcode 0xC9 vs prototype operand 0xF5
- +`0x217`: Europe operand 0x00 vs prototype opcode 0xC2
- +`0x21F`: Europe operand 0x05 vs prototype opcode 0x0A
- +`0x221`: Europe operand 0x00 vs prototype opcode 0xAF
- +`0x223`: Europe opcode 0x80 vs prototype operand 0x07
- +`0x22B`: Europe operand 0x77 vs prototype opcode 0xF0
- +`0x22C`: Europe opcode 0xA5 vs prototype operand 0x0A
- +`0x22D`: Europe operand 0xD4 vs prototype opcode 0xC9
- +`0x22E`: Europe opcode 0x29 vs prototype operand 0x03
- +`0x230`: Europe operand 0x00 vs prototype opcode 0xF0
- +`0x231`: Europe opcode 0x9F vs prototype operand 0x05
- +`0x232`: Europe operand 0x86 vs prototype opcode 0xA9
- +`0x236`: Europe opcode 0x68 vs prototype operand 0x03
- +`0x238`: Europe opcode 0xFA vs prototype operand 0x62
- +`0x239`: Europe opcode 0x60 vs prototype operand 0xEA

### `00:C3A9..00:C450` → shift -19
- +`0x35`: Europe opcode 0x92 vs prototype operand 0x7F
- +`0x36`: Europe operand 0xC4 vs prototype opcode 0xC4
- +`0x37`: Europe opcode 0x56 vs prototype operand 0x43
- +`0x38`: Europe operand 0xC4 vs prototype opcode 0xC4
- +`0x39`: Europe opcode 0xB8 vs prototype operand 0xA5

### `00:8C49..00:8CCA` → shift -9
- +`0x5`: Europe opcode 0x08 vs prototype unreached 0xFA
- +`0x6`: Europe opcode 0xE2 vs prototype unreached 0x89
- +`0x7`: Europe operand 0x20 vs prototype unreached 0x80
- +`0x8`: Europe opcode 0xA9 vs prototype unreached 0x60
- +`0x9`: Europe operand 0x04 vs prototype opcode 0x08
- +`0xC`: Europe operand 0x8B vs prototype opcode 0xA9
- +`0x10`: Europe opcode 0x86 vs prototype operand 0x8B
- +`0x16`: Europe operand 0x00 vs prototype opcode 0xC2
- +`0x17`: Europe opcode 0xA0 vs prototype operand 0x20
- +`0x18`: Europe operand 0x05 vs prototype opcode 0xA2
- +`0x1A`: Europe opcode 0xBF vs prototype operand 0x00
- +`0x1B`: Europe operand 0x00 vs prototype opcode 0xA0
- +`0x24`: Europe opcode 0xE8 vs prototype operand 0x80
- +`0x25`: Europe opcode 0xE8 vs prototype operand 0x83
- +`0x27`: Europe opcode 0x10 vs prototype operand 0x07
- +`0x28`: Europe operand 0xF1 vs prototype opcode 0xE8
- +`0x2D`: Europe operand 0xFB vs prototype opcode 0x28
- +`0x2E`: Europe operand 0x83 vs prototype opcode 0x60


Only disagreements that survive homolog alignment should be considered candidates for da65/Ghidra adjudication. Same-offset disagreement is retained as raw evidence but is not itself semantic evidence.
