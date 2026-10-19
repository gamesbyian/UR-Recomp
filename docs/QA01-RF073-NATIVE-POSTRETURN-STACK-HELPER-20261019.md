# QA01: native RF073 post-RTI stack-helper first reads are later gameplay, not RTI operands

**Independent archived-byte review, October 19, 2026.** The historical genuine original/native RF054 case [run 39161563837](https://github.com/gamesbyian/UR-Recomp/actions/runs/39161563837), artifact **12149640496**, ZIP SHA256 `3ccb209a92045e9e89113442e68af51b85a453a160a9b9efaf8ca0d59e79631c`, contains **2,741 sequenced native RF047 events** across nine host frames 1017..1025. This analysis reuses merged [RF073](RF073-AUTHENTIC-NATIVE-NMI-COMPILED-RTI-BRACKETS-20261019.md)'s strict actual original/native archive verifier and its full, self-owned native event ordinals. It never orders a fragmented RF044 prefix as an executed bus transaction.

For **every** native NMI bracket the actual compiled sequence is entry, push `26 EE D4 82` at `00:01ED..01F0`, exactly one native NMI helper status read **`00:01ED=26`**, compiled RTI marker and handler return. There are **no RF047 saved-PC or bank helper reads** between native after-push and compiled RTI. This is a statement about **RF047 helper coverage**, not proof that the native compiled return did not internally consume those bytes.

## Genuine native first observed helper reads *after* the compiled return

The independently inspected genuine RF047 substream has **45 first-later byte-address observations from 29 distinct actual native helper operations**, five byte positions in each of nine native frames, all `nmi=0` and strictly after that frame's compiled return by native-local event ordinal **and native master time**.

| Native host frame | First later `01ED` | `01EE` | `01EF` | `01F0` | `01F1` |
|---|---|---|---|---|---|
| 1017 | `41` | `02` | `01` | `00` | `26` |
| 1018–1019 (each) | `B9` | `85` | `01` | `00` | `26` |
| 1020–1025 (each) | `01` | `00` | `0A` | `00` | `26` |

In **all nine**, the first helper after the compiled return is `01F1=26`, with sequence exactly `handler_return+1`. **Read width matters:** in frame 1017 the first `01ED` and `01EE` byte observations are the *same actual word read* `01ED=0241` (little-endian bytes `41 02`) at seq7; the first `01EF` and `01F0` similarly share the actual word read `01EF=0001` at seq8. For 1020–1025, word reads `01ED=0001` and `01EF=000A` each cover two byte addresses. These first later bytes are **not** the saved `01EE=EE` and `01F0=82` pushed at native NMI entry. This is *not evidence of an incorrect RTI consumed value*: the later getset helper reads occur during subsequent gameplay, at distinct native master counts, with **intervening native RAM writes not comprehensively traced**. They are not semantically equivalent to the original RF072 first post-NMI reads of `26 F0 D4 82 26` because those original observations come from a different research executable epoch with different CPU coverage and no proven source/native clock alignment.

The source original host-frame NMI contexts `82:D4F0` versus native saved resume `82:D4EE` in four frames remain **same-host-frame snapshots, not same fetched-opcode/interrupt phases**. Avoid inferring a skipped CPU read, unchanged value, first diverging consumed byte or correctness/bug from these later helper records. Keep all stack residuals unmasked.

## Repeatable bounded QA, no new emulator execution

New independent `tools/qa01_independent_rf073_posthandler_stack_helpers.py` opens the exact immutable RF054 original/native case, calls merged RF073's full 2,741-event validator, and collects the first subsequent `nmi=0` physical native helper read for each `00:01ED..01F1` address in each independently delimited native NMI frame. It splits real width-one and width-two reads into the corresponding little-endian byte observations, retaining one physical event ordinal per actual read rather than inventing two bus calls. The exact pinned source ZIP must yield **45 first byte positions but only 29 distinct read events**; changed widths or event coverage fail qualification. It fails closed on altered status, missing later read, event ordinal corruption, native master clock rollback or wrong pinned ZIP; unit tests use only synthetic non-ROM event data. Output retains **all 45 original native event ordinals and true master clocks**, plus explicit false qualifications for decoded opcode fetch PC, complete writer visibility and original/native same-phase reads:

```bash
python3 tools/qa01_independent_rf073_posthandler_stack_helpers.py \
  /path/to/exact-RF054-case.zip \
  --output /tmp/qa01-native-first-posthandler-reads.json
python3 -m unittest tests.unit.test_qa01_independent_rf073_posthandler_stack_helpers -v
```

**Next CPU/APU experiment:** instrument the actual compiled native RTI stack-pop consumer, its decoder/fetched opcode PC, operand stack address/value, SP before/after and true native-local instruction/master clock, then pair that with an independently sampled *same-case* original NMI checkpoint and source-return witness. This is source/producer work for the existing CPU/APU owner, **not** an RF047 helper inferred replacement. No input shift, byte mask, emulator code change, factory, gameplay decision or Windows PE approval. **0/45 accepted USA events, 0/12 Windows release QA gates.**
