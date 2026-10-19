# RF064: original real PullB/PullW returns linked to one sequenced WRAM access

**19 October 2026. ROM-free source producer, not a guest replay.** This continues merged RF063 and RF061. It does not change native or production gameplay or award USA event credit: **0/45 USA**, **0/12 Windows release QA**.

## A genuine post-call return, not an inferred read

RF063 supplies one source-original event sequence spanning RF044 filtered WRAM getset *entries* and an unmasked real post-NMI-push checkpoint. Entry-time RAM sampling does **not** prove the CPU received the sampled byte. RF045 independently records the actual value returned by real Snes9x stack PullB/PullW, but its macro-local ordinal alone cannot locate the corresponding source bus entry.

RF064 measures the shared source bus ordinal immediately before and after the **unchanged original** S9xGetByte/S9xGetWord call inside PullB/PullW. If it advances by **exactly one**, within the RF063 recorder capacity, the macro's call contributed one unique eligible source getset entry. More than one bus entry, overflow or a nested guest event makes the join **ambiguous**. RF064 keeps that ambiguity visible rather than assigning a guess.

The independent reporter requires original RF063 contiguous ordinals and real NMI five-byte parity against RF044; it then matches the original RF045 actual macro-return value to the unique RF063 source entry by its ordinal, physical stack address, getset read kind, width, frame and sampled bytes. It recomputes uniqueness instead of trusting the instrument's claim. It rejects mixed rows, gaps, counterfeit macro returns, incorrect values, truncation, and changed checkpoints.

## Source-original staging

Use a disposable Snes9x checkout pinned to snes9xgit/snes9x commit 1bcc369e89f08243e0a462882fb1f3e42e51de3a. Preserve actual original ROM, movie, input, seed SRAM, binaries and native/original local clocks.

Stage in this exact order **before** compiling and running the genuine frozen original case:

1. python3 tools/qa01_rf044_stack_bus_witness.py original --root "$ORIGINAL"
2. python3 tools/qa01_rf045_source_stack_macro_witness.py --root "$ORIGINAL"
3. python3 tools/qa01_rf063_original_shared_sequence.py --root "$ORIGINAL"
4. python3 tools/qa01_rf064_original_post_call_pull.py --root "$ORIGINAL"

For original guest frames 1017..1025 enable UR_QA01_RF044_STACK_BUS=1, UR_QA01_RF045_STACK_PUSH_PULL=1, UR_QA01_RF063_SOURCE_ORDER=1 and UR_QA01_RF064_POST_CALL_PULL=1. After the authentic original replay, run:

    python3 tools/qa01_rf064_original_pull_return_report.py /path/to/original.log --out /path/to/rf064.json
    python3 -m unittest tests.unit.test_qa01_rf064_original_post_call_pull -v

The patch changes only the **original cpuops.cpp** macro instrumentation. It adds no SNES memory operation, changes no stack pointer arithmetic, preserves the one real bus getter call per macro, and adds no CPU/APU cycles. Every return record includes before/after serial, real returned value, stack address, source guest PC, and whether the interval had a unique eligible getset event.

## Remaining stop/go conditions

This is proof of an individual **original** post-call stack value when actual replay qualifies it. It is not yet proof of the native consumed value, saved PC/bank equality, full-race parity, clock synchronization or a first differing byte. Source/native exact input and source hashes, instrumented vs uninstrumented guest invariants, unmasked *full* WRAM bytes, per-read native executed instruction binding, and independent matching semantic checkpoints remain prerequisites for QA01 causal-window normalization. Native RF062 and the independent continuous-frame agent own the complementary work.

**No new source-authentic RF064 guest execution has taken place on this branch. No event credit or gameplay patch is authorized by these tests.**

## RF065 exact-source compile qualification

The focused `.github/workflows/qa01-original-stack-producer-compile.yml` merge-validation workflow builds the repository-owned, vendored original libretro Snes9x at upstream revision `1bcc369e89f08243e0a462882fb1f3e42e51de3a` after independently checking the original source closure against its immutable island-manifest SHA-256 (the vendored staging directory deliberately has no `.git`), stages RF044 → RF045 → RF063 → RF064 on the disposable original sources, and builds the actual modified `getset.h`, `cpuexec.cpp` and `cpuops.cpp` C++ translation units. It retains source and final binary SHA-256 receipts. This is deliberately a **ROM-free source/ABI compatibility gate**, not a real original event replay or a completed read witness. If compilation fails, correct the narrow staging mismatch before consuming any more authentic Zoo research runners. The workflow does not run after unrelated PRs.

### Pinned actual source compiler verdict, October 19

[RF065's real 2014 Snes9x original-source compile](../analysis/data/rf065-authentic-pinned-snes9x-compiled-original-observer-20261019.json) succeeded on the exact pinned **vendored** source, including all RF044→RF045→RF063→RF064 transformations, after the compiler caught and we fixed an actual RF064 word-pull stack-variable typo. [Workflow run 39215804536](https://github.com/gamesbyian/UR-Recomp/actions/runs/39215804536) finished successfully; the independent unit and hygiene jobs also succeeded. The receipt retains the tested PR head SHA, merged main SHA, pristine island tree SHA-256, source build artifact ID and digest. This establishes real C++ source compatibility but **does not execute a game or prove any actual stack read**. The one-shot authentic Zoom Zoo execution remains independent and must be assessed on its real archived logs, not deduced from this compiler success.
