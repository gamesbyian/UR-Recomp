# PAL retail vs 1994-11-29 prototype: normalized snes2asm delta pass

Non-RNC differing bytes: **103446**.
Changed bytes code-related in at least one snes2asm trace: **5979**.

## Classification

| Class | Bytes |
|---|---:|
| unreached-both | 97467 |
| instruction-boundary-disagreement | 2812 |
| reachability-disagreement | 1528 |
| opcode-change | 1485 |
| operand-or-literal-change | 148 |
| mx-state-disagreement | 6 |

## Highest-value bounded windows

| Range | Changed bytes | Span | Classes | da65? |
|---|---:|---:|---|---|
| `01:BB69..01:BEA3` | 778 | 827 | reachability-disagreement:100, instruction-boundary-disagreement:412, opcode-change:261, operand-or-literal-change:5 | yes |
| `00:ABA9..00:ADE2` | 535 | 570 | reachability-disagreement:70, instruction-boundary-disagreement:287, opcode-change:175, operand-or-literal-change:2, mx-state-disagreement:1 | yes |
| `00:D1D5..00:D37A` | 413 | 422 | reachability-disagreement:46, opcode-change:85, instruction-boundary-disagreement:276, mx-state-disagreement:1, operand-or-literal-change:5 | yes |
| `00:E217..00:E37A` | 350 | 356 | reachability-disagreement:55, instruction-boundary-disagreement:169, opcode-change:124, operand-or-literal-change:2 | yes |
| `00:A082..00:A1F1` | 345 | 368 | reachability-disagreement:46, instruction-boundary-disagreement:193, opcode-change:91, mx-state-disagreement:1, operand-or-literal-change:14 | yes |
| `00:B929..00:BA69` | 317 | 321 | reachability-disagreement:37, instruction-boundary-disagreement:173, opcode-change:107 | yes |
| `00:F4FF..00:F617` | 263 | 281 | reachability-disagreement:111, instruction-boundary-disagreement:107, opcode-change:44, operand-or-literal-change:1 | yes |
| `00:91C8..00:933B` | 252 | 372 | reachability-disagreement:18, instruction-boundary-disagreement:109, opcode-change:67, operand-or-literal-change:58 | yes |
| `00:FAC4..00:FBC4` | 242 | 257 | reachability-disagreement:54, instruction-boundary-disagreement:121, opcode-change:64, mx-state-disagreement:3 | yes |
| `00:B6BC..00:B7B8` | 235 | 253 | reachability-disagreement:76, instruction-boundary-disagreement:108, opcode-change:51 | yes |
| `00:C3A9..00:C450` | 165 | 168 | reachability-disagreement:38, opcode-change:59, instruction-boundary-disagreement:66, operand-or-literal-change:2 | yes |
| `02:B16E..02:B224` | 158 | 183 | reachability-disagreement:86, opcode-change:27, instruction-boundary-disagreement:45 | yes |
| `00:F7F8..00:F88C` | 147 | 149 | reachability-disagreement:54, instruction-boundary-disagreement:64, opcode-change:29 | yes |
| `00:B102..00:B18C` | 131 | 139 | reachability-disagreement:52, instruction-boundary-disagreement:58, opcode-change:21 | yes |
| `00:8C49..00:8CCA` | 129 | 130 | reachability-disagreement:14, opcode-change:27, instruction-boundary-disagreement:88 | yes |
| `00:C1EF..00:C268` | 121 | 122 | reachability-disagreement:38, instruction-boundary-disagreement:56, opcode-change:25, operand-or-literal-change:2 | yes |
| `00:A85F..00:A8D3` | 116 | 117 | reachability-disagreement:55, instruction-boundary-disagreement:27, opcode-change:34 | yes |
| `00:EFB8..00:F02A` | 115 | 115 | reachability-disagreement:56, opcode-change:23, instruction-boundary-disagreement:36 | yes |
| `00:C559..00:C5CA` | 101 | 114 | reachability-disagreement:37, opcode-change:21, instruction-boundary-disagreement:41, operand-or-literal-change:2 | yes |
| `00:8853..00:88B1` | 94 | 95 | reachability-disagreement:10, instruction-boundary-disagreement:71, opcode-change:13 | yes |
| `00:A99C..00:A9F9` | 92 | 94 | reachability-disagreement:47, instruction-boundary-disagreement:33, opcode-change:12 | yes |
| `02:B280..02:B2DC` | 92 | 93 | reachability-disagreement:52, opcode-change:19, instruction-boundary-disagreement:21 | yes |
| `00:B07F..00:B0DB` | 90 | 93 | reachability-disagreement:26, instruction-boundary-disagreement:51, opcode-change:12, operand-or-literal-change:1 | yes |
| `00:9372..00:93CA` | 89 | 89 | reachability-disagreement:18, instruction-boundary-disagreement:55, opcode-change:16 | yes |
| `00:EB07..00:EB60` | 86 | 90 | reachability-disagreement:55, opcode-change:10, instruction-boundary-disagreement:20, operand-or-literal-change:1 | yes |
| `00:EF31..00:EF88` | 83 | 88 | reachability-disagreement:54, opcode-change:14, instruction-boundary-disagreement:15 | yes |
| `00:9860..00:98B2` | 82 | 83 | reachability-disagreement:25, instruction-boundary-disagreement:35, opcode-change:22 | yes |
| `00:9568..00:95A4` | 61 | 61 | reachability-disagreement:18, instruction-boundary-disagreement:31, opcode-change:12 | yes |
| `00:D4F0..00:D524` | 53 | 53 | reachability-disagreement:38, instruction-boundary-disagreement:8, opcode-change:7 | yes |
| `00:94E2..00:9510` | 47 | 47 | reachability-disagreement:18, opcode-change:4, instruction-boundary-disagreement:25 | yes |
| `00:B5FF..00:B625` | 39 | 39 | reachability-disagreement:38, opcode-change:1 | yes |
| `00:96F4..00:9718` | 37 | 37 | reachability-disagreement:18, opcode-change:8, instruction-boundary-disagreement:11 | yes |
| `00:F0BA..00:F0ED` | 48 | 52 | reachability-disagreement:48 | no |
| `03:FB41..03:FB55` | 20 | 21 | reachability-disagreement:20 | no |
| `03:AC89..03:AD30` | 18 | 168 | operand-or-literal-change:18 | no |
| `03:ABBF..03:AC2A` | 16 | 108 | operand-or-literal-change:16 | no |
| `03:AD64..03:AD91` | 5 | 46 | operand-or-literal-change:5 | no |
| `03:ADD6..03:ADFE` | 5 | 41 | operand-or-literal-change:5 | no |
| `03:9211..03:9224` | 2 | 20 | operand-or-literal-change:2 | no |
| `03:A999..03:A99A` | 2 | 2 | operand-or-literal-change:2 | no |
| `03:8B19..03:8B19` | 1 | 1 | operand-or-literal-change:1 | no |
| `03:8B9F..03:8B9F` | 1 | 1 | operand-or-literal-change:1 | no |
| `03:9410..03:9410` | 1 | 1 | operand-or-literal-change:1 | no |
| `03:94C6..03:94C6` | 1 | 1 | operand-or-literal-change:1 | no |
| `03:99A5..03:99A5` | 1 | 1 | operand-or-literal-change:1 | no |

## Next analyzer step

Run bounded da65 only on windows marked `da65=yes`, supplying CODE range and independently supported M/X state. Use Ghidra only where that bounded second witness disagrees with snes2asm or where xrefs/function boundaries are needed.
