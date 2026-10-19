# QA01 genuine RF064 original-read-path audit (19 October 2026)

**Disposition: independently reproduced actual source observations, causal producer HOLD.** This is a read-only review of immutable genuine [one-shot original/native Zoom Zoo run 39216237965](https://github.com/gamesbyian/UR-Recomp/actions/runs/39216237965), source commit `2d572750b5d1658fd18a0e6af82f3c2cb9ca1662`. No new emulator was executed, no gameplay/clock/input altered, no source instrumentation superseded and no full USA event accepted (0/45). The RF064 owner retains the true original source changes; this tool independently checks the recorded results.

Original [case archive 12170321915](https://github.com/gamesbyian/UR-Recomp/actions/runs/39216237965/artifacts/12170321915), downloaded and SHA256 verified: `7891a24124c67f414e9b00ed2bb1dbe2e59e4a2b6c50b558e920c25d885e63ea`; original replay log SHA256 `0dfe14195cffc9fc2e044adb372f81c9440e4b0e5330671906934d475bfad`. The exact archive has 410 members including genuine raw original/native WRAM/SRAM, original log, source run and full progression receipts. This review only consumes the bounded original-source trace members. The source-original/NMI, result and SRAM evidence does not by itself imply full event admission.

## Independently recomputed return/source bus relationships

The new `tools/qa01_rf064_independent_archive.py` independently reopens the ZIP and checks its SHA, complete reference log SHA, nontruncation, true RF045 post-call return vs RF064 record for **every one** of the 903 pulls (same frame, source v/h clock position, kind, PC, base/width and returned byte), all RF044 physical getset visits against their RF063 ordinal-stamped copies, and the real unmasked original RF044 NMI new stack against the RF063 checkpoint. It rejects missing/duplicate/reordered source-local ordinals and producer-report counter contradictions. The [machine report](../analysis/data/qa01-rf064-authentic-original-pull-independent-review-20261019.json) is reproducible with:

```bash
python3 tools/qa01_rf064_independent_archive.py \
  --archive /tmp/qa01-rf064-genuine-case.zip \
  --expect-sha256 7891a24124c67f414e9b00ed2bb1dbe2e59e4a2b6c50b558e920c25d885e63ea \
  --output /tmp/qa01-rf064-source-review.json
python3 -m unittest tests.unit.test_qa01_rf064_independent_archive -v
```

Actual results:

| Source observation | Independently counted |
| --- | ---: |
| RF045 original pull returns | **903**, exactly reproduced by RF064 |
| Original word / byte pulls | **710 word, 193 byte** |
| RF063 sequenced getset entries | **903 writes**, 710 `ww` + 193 `wb` |
| RF063 sequenced original stack *read* entries | **0** |
| RF064 pulls with unchanged getset ordinal before/after | **903/903** |
| RF064 actually joined to one getset read | **0/903** |
| RF063 local ordinals | 1–904 contiguous; one real NMI checkpoint |
| RF044 genuine NMI snapshots | 9; single RF063 checkpoint matches |

The first source original `pullW` returns `9141` at frame 1017/v0/h30, PC `82:9141`, with `before=0 after=0 unique=0`. The following RF063 `ww` getset event writes `914E` at h78; it is **not** the preceding pull's source read. The source-original return bytes are real and can be matched to their RF045 macro witnesses, but the currently instrumented RF044/RF063 getset filter **did not observe a matching read call on this path**. This is not 903 *reentrant getset reads*. It is 903 post-call returns **without an intervening eligible sequenced getset entry**. The original `rf064-original-pulls.json` conservatively groups these as `ambiguous_or_reentrant_original_pulls`; this independent reviewer reports the observed absence separately.

**Interpretation:** the true underlying original stack pull execution is evident from RF045/RF064 return records, while the RF063 bus-entry recorder appears to miss its read path. Do not conclude that the game does not read the stack, or assert which optimization/inlining path caused the gap until the exact 2014 `cpuops.cpp` → `getset.h` source flow is qualified. Instrument the already-executing pull's genuine return/guest PC under the source-local ordinal, rather than adding a fake source read or a second S9xGetByte/Word call. No actual native read PC equivalence has been shown. This closes a producer-observer question, **not** a gameplay/CPU synchronization bug.

The same genuine run produced a source/native diagnostic `strict_candidate` for the Zoom Zoo result at +5163 and next Bowl entry at +267, but retained **8 unmasked WRAM differing-byte occurrences** around next Bowl +266/+280, no original/native whole-race parity and no independently proven guest controller CPU polls/Windows cold persistence. Those outcomes are preserved without a waiver. [QA01 event requirements](QA01-INDEPENDENT-FIRST-USA-EVENT-ACCEPTANCE-20261018.md) and [factory preflight](QA01-RESEARCH-FACTORY-ADMISSION-20261019.md) remain HOLD. No large research campaign or event credit.

## Source-original **actual post-NMI return values** (distinct positive witness)

The one real RF063 checkpoint `seq=67`, original frame 1017, v225/h78, has physical stack bytes at `7E:01ED..01F1` equal to `26 F0 D4 82 26`, independently equal to RF044's immediately post-NMI real snapshot. **Before the next sequenced RF063 getset event** (a later write, seq68), the original RF064 post-call logger and separately matching RF045 post-call macro report exactly these four returns, at original frame 1017:

| Source-local v/h | Physical stack address | Actual returned value | Source executed PC |
| --- | --- | --- | --- |
| v226/h714 | `7E:01ED` | `26` (one byte) | `80:B0EB` |
| v226/h730 | `7E:01EE` | `D4F0` (two little-endian bytes) | `80:D4F0` |
| v226/h738 | `7E:01F0` | `82` (one byte) | `82:D4F0` |
| v226/h834 | `7E:01F1` | `26` (one byte) | `82:D4F5` |

This is **positive evidence that the original source S9xGetByte/Word pull macros actually returned the saved NMI-stack values** in this sampled early frame, not merely that those bytes were present in a snapshot. The independent verifier now recomputes each return from the checkpoint's five unmasked bytes and checks the ordinal, actual return, original timestamp order and original PC. No eligible RF063 getset *write* intervenes, and no eligible RF063 getset *read* is recorded either. It therefore **cannot identify the missing underlying read bus-entry site** or establish independent native same-PC/state equivalence. The first returned PC `80:B0EB` is a source execution observation, not a native guest instruction witness.

The same independent scan also verifies **all nine genuine RF044 NMI snapshots** across original host frames 1017–1025, each followed by precisely four original RF064 returned stack values matching its own saved bytes before the next **observed** sequenced getset write. This independently yields **36 actual returned reads across nine original NMIs**, not nine RF063 checkpoints: only the first NMI has a shared source-local `RF063ORIGCHECKPOINT` record, and the remaining eight are qualified against their actual RF044 NMI log lines and the most recent genuine RF063 getset ordinal. Saved status/return addresses alternate as actually logged; no additional source instruction or bus event is manufactured. The machine report records the distinct `source_nmi_return_sequences` and preserves `native_equivalence_proven=false`. The stronger series check is **within one original source execution**, not nine independent replay replicates.

**Frame caution:** RF044/RF064 instrumented **original host 1017..1025**, near Zoo race entry, *not* the later race-relative +5034..5042 divergence in the separate nine-frame capture. Do not promote these early reads to first consumed reads of the late stack/sound pointer differences. An authentic late bounded experiment must prove its own original and native host-frame origins and independent source input/clock registration first.

## Immediate follow-up for producer owners

RF063/064 source owner: preserve genuine RF045 returns and the newly qualified original core compile, but find the actual original pull data path before normalizing a single bus-read ordinal. Native RF062 owner: independently qualify the real 82:82F0 emitted guest PC in its own clock domain. Independent QA: after authentic original/native equivalent *executed* reads are available, join them to the already retained +5034–+5042 unmasked original/native frame evidence with the merged `qa01_causal_window.py` and `qa01_factory_preflight.py`. Retain source/input/ROM/guest identity; never synthesize missing events from logged host-state snapshots.

Ten synthetic adversarial unit tests exercise missing returns, forged actual values, bus ordinal gaps, RF044/RF063 drift, NMI mutation, tampered ZIP/log SHA and false positive producer claims. These tests qualify **the consumer**, not an emulator or a game event.
