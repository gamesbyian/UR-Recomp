# RF048: two transient, live Zoo sound-pointer samples after RF047 NMI closure

**Read-only source-qualified analysis of an already-executed original/native USA case. No new emulator run, gameplay patch, WRAM exclusion, cycle shift, or complete-event admission. Accepted 0/45.**

## Immutable original/native source and control population

The corrected RF047 [genuine original/native Zoo run 39096831814](https://github.com/gamesbyian/UR-Recomp/actions/runs/39096831814), source `f47dda877272c4d1672ba75d8fe36c8efb6fc45b`, retained one [18-file case artifact 12124654817](https://github.com/gamesbyian/UR-Recomp/actions/runs/39096831814/artifacts/12124654817), independently SHA256 rehashed `1060a98744fb770bbe43fcdddd89b352bdef691e18f1ab24d4ead5f16996bf6b`. Its `zoo_race_mesh`, `zoo_next_bowl_handoff` and `source_terminal_followthrough` entire JSON objects are exactly equal to immutable RF045 case ZIP `3f06c51d20414833c71ff603ec1ec0b947f765007cf45d250bef158276091773`. Both fresh original/native Zoo entries are **host1017**, with no searched or shifted per-frame offsets in this comparison; the separate authentic archived original movie uses its **own** frame origin.

Across **78** unmasked 131,072-byte original/native WRAM pairs, **51 are byte-exact**, with 92 total unmasked different-byte occurrences. Of those, 90 occur at CPU stack-page `01ED..01F1`, separately source-qualified in [RF047](RF047-NATIVE-NMI-PHASE-WITNESS-20261017.md). The other **two** are only at sound-transfer pointer `7E:0063`.

### Exact 13-frame late-window observation

| Zoo relative frame | Whole-WRAM different bytes | Sound `$63`: original/native | Sound `$69` |
| ---: | ---: | --- | --- |
| +5034 to +5038 | 2 each (stack `01EE/01F1`) | No `$63` difference | Equal |
| +5039 | **0** | `B0/B0` | `9F/9F` |
| +5040 | **1** | **`73/74`** | `BE/BE` |
| +5041 | **0** | `4D/4D` | `97/97` |
| +5042 | **0** | `27/27` | `71/71` |
| +5043 | **0** | `00/00` | `4A/4A` |
| +5044 | **0** | `DA/DA` | `24/24` |
| +5045 | **1** | **`B3/B4`** | `FE/FE` |
| +5046 | **0** | `8D/8D` | `D7/D7` |

Thus **every one** of the 131,072 WRAM bytes is identical immediately before and after both independent one-byte `$63` samples. The sound-counter `$69` is equal at all eight +5039..+5046 samples, as is pointer high byte `$64` (every whole image has at most the one named mismatch). These observations are actual guest-state frame samples, **not all instructions within each host frame**, so recovery one frame later cannot by itself establish where the original and native APU receiver observed the byte or whether they received identically timed sound.

[Exact complete 13-sample address/value machine receipt](../analysis/data/rf048-zoo-two-one-byte-sound-pointer-transients-20261018.json) retains every whole-WRAM difference, all actual addresses, guest-local host clocks, live-consumer antecedents and immutable source SHA.

## Actual pointer readers and original source CPU procedure

RF035 [genuine source-executed case](RF035-EXECUTED-LIVE-SOUND-CONSUMER-20261016.md) and RF037 [producer/receiver chain](RF037-SOUND-TRANSACTION-20261017.md) already **proved actual native pointer-helper consumption** at the residual boundary: native `Snd_IncDataPtr_M1X0` last recorded word `C773` immediately before `Snd_UploadBlock_80D1_M1X0` first consumed `C774` at native host6057, and likewise `D0B3→D0B4` at host6062. These pointer values are live; do not mark `$63` unconsumed.

The repository's authentic Nitrodon [USA bank-82 disassembly](../reference/imported/reverse-engineering/nitrodon/bank%2082.txt) directly identifies sound pointer setup/advance and CPU/APU output operations:
```asm
82:82CC  LDY $63
82:82CE  STZ $63
82:82D0  STZ $64
82:82F0  LDA [$63],Y
82:82F2  STA $2143
82:82F6  STA $2142
82:82F9  INY
82:8301  CMP $2142
```
This authentic code exposes the separate pointer/read/port-echo stages, but merely seeing `INY` adjacent to a one-byte sample difference **does not attribute the specific observed writer or a missing CPU instruction**. RF037's fully genuine sound CPU-port payload comparison established **45,645 original port2/3 payloads matching native prefix values**, subject to three still-unresolved same-original-SPC-age two-write order ties. RF038–041 subsequently isolated target 6 original versus 3 native echo polls and a **+156-master-clock** transfer interval, genuine SPC F6 original-old23-before-new24 versus native-new24 ordering, with **distinct, unaligned absolute CPU/SPC clock epochs**. RF042's attempted equal-age APU publication treatment *regressed* real full-WRAM pairs **51→46** and byte discrepancies **92→106**, and its targeted native writer trace missed the intended source transfer. It remains a rejected hypothesis.

**Causal limit:** Short-lived native `$63` one-byte advancement and eventual byte-exact recovery are consistent with differently sampled upload progress, but actual original/native **first source pointer value read → original CPU `$2142/$2143` write → SPC F6/F7 receipt** is not connected at *both* frame boundaries with calibrated clocks. A present native read plus a later equal WRAM frame is not sufficient to declare a harmless pointer or a safe universal APU retiming. No production runtime or strict comparator correction is proposed.

## Acceptance decision, not another factory

Preserve RF047's independent QA-01 [issue #967](https://github.com/gamesbyian/UR-Recomp/issues/967) adjudication for stack residue. The sound pointer is a **distinct** CPU/APU owner problem in [issue #1689](https://github.com/gamesbyian/UR-Recomp/issues/1689). Before any new run, consume the already-qualified RF035–041 genuine CPU/SPC writer/receiver logs and the complete 45,645-value port-prefix receipt, with separately registered guest clocks. If that cannot settle the consumer clock at +5040/+5045, only one additional finite source-proven **original and native actual first-reader/port-publication/receiver** witness on the 2014 Zoo input is justified. Do not introduce a global offset, inferred three extra CPU polls, broad 45-course campaign, speculative stack exemption or secondary emulator.

Positive bounded state remains **Zoo result +5163, next Bowl +267, eleven matching entire earned SRAM snapshots and genuine cold reload**; these cannot substitute for all-frame source-clock gameplay equivalence, Windows shipping guest identity, independent physical/system QA or the first **complete USA event (0/45 accepted)**.
