# RF063: original Snes9x source-local bus-entry and NMI checkpoint order

**Research only; no new source-authentic replay, no modified gameplay, no event acceptance.** USA **0/45** and Windows QA **0/12** remain unchanged. This work complements [RF061](RF061-ZOO-EXECUTED-PC-CAUSAL-PRODUCER-20261019.md), the separate native sound-read RF062 agent, and the strict merged QA01 causal-window consumer.

## Why another witness is needed

Actual historical RF054 Zoom Zoo has 903 original RF044 bus writer records, 1,806 source RF045 stack push/pull records and nine source NMI markers. The source RF045 macro ordinals are macro-local; RF044 getset records and NMI checkpoints cannot be placed on that same physical source-local order. The mixed records cannot safely be sorted by printed log lines, CPU clocks, or guessed offsets from native.

RF063 introduces **one shared, monotonically increasing sequence** into the already-staged original emulator code. The source recorder is intentionally narrower than a completed causal producer: RF044's existing getset call is instrumented *on entry*, before the call has produced/consumed its real return value. It **must not** be passed to QA01 as a proven `read` simply because it carries a real PB:PC and a RAM sample. The RF045 post-call true stack pull remains stronger evidence of the value actually consumed. The original macro-local sequence remains independent.

## Exact original staging and interpretation

Start with a **disposable** original checkout pinned to `snes9xgit/snes9x@1bcc369e89f08243e0a462882fb1f3e42e51de3a`. Follow the established authentic 2014 original build and frozen input/ROM/SRAM path from the RF054 campaign; verify binary/source and original clock origins separately. Do not patch the shipping emulator or native runner.

```bash
python3 tools/qa01_rf044_stack_bus_witness.py original --root "$ORIGINAL"
python3 tools/qa01_rf045_source_stack_macro_witness.py --root "$ORIGINAL"
python3 tools/qa01_rf063_original_shared_sequence.py --root "$ORIGINAL"
# Rebuild original Snes9x only after all three patches, not before.
# Opt in to all three in the genuine frozen original replay:
# UR_QA01_RF044_STACK_BUS=1
# UR_QA01_RF045_STACK_PUSH_PULL=1
# UR_QA01_RF063_SOURCE_ORDER=1
python3 tools/qa01_rf063_original_sequence_report.py /path/to/actual-original.log \
    --out /path/to/rf063-original-order.json
python3 -m unittest tests.unit.test_qa01_rf063_original_sequence -v
```

The RF063 Python source adapter edits **only** already-instrumented `getset.h` and `cpuexec.cpp`. It adds no `S9xGetByte/Word`, `S9xSetByte/Word` or `S9xOpcode_NMI` invocations. `cpuexec.cpp` defines the single C++ global source counter. The pre-existing RF044 `ur_rf044_orig_bus` appends sequenced `QA01RF063ORIGBUS` records at each filtered 01ED..01F1 getset entry. The exact original `S9xOpcode_NMI()` call appends one `QA01RF063ORIGCHECKPOINT` at first host frame 1017, *after the real NMI push and before handler dispatch*, sampling five unmasked `Memory.RAM` bytes 01ED..01F1. These are host-side diagnostics, not additional guest bus operations.

The reporter requires unique contiguous original ordinals across all sequenced getset entries **and that one checkpoint**, no truncation, the actual expected frame/address/filter syntax, and byte-for-byte equality of the snapshot to the independently already-emitted original RF044 post-NMI `new=` stack capture. It refuses pre-RF063 archives, duplicate/gapped/misordered IDs, corrupt raw bytes, synthetic/missing NMI observations, and wrong bus-filter entries.

**Remaining evidence barriers:** a getset-entry sample does not by itself prove the returned byte; word reads/writes may have subtler operation ordering; the RF045 post-call macro-local ordinal has not been transactionally joined; original source and ROM/movie/guest hashes still require external case authentication; independently prove that the native after-push snapshot has precisely the same semantic phase; and reopen native and source raw checkpoint bytes across all relevant differing WRAM addresses before asking `qa01_causal_window.py` for a verdict. The above reporter *always* marks itself ineligible for causal-window promotion. Any failure, replay overhead, NMI shifting, altered 78 full-WRAM sample counts, +5163/+267 timing, SRAM persistence or input identity is a hard hold, not permission to soften the experiment.

## Real follow-through

Run one bounded authenticated RF063 original case alongside the other agent's RF062 native direct-read pilot, if both source preflights and binary product hashes pass. Compare the instrumented **original to its own uninstrumented control** before cross-emulator conclusions. Archive unmasked original/raw five-byte snapshot and all sequence rows, original/source binary SHA256, exact frozen input/ROM and original toolchain identity. Independently reopen logs and validate their semantic phases. Do not run factories for these probes.

This branch provides **source instrumentation and ROM-free adversarial tests only**, not a new authentic guest replay or the first consumed differing byte. A green test suite is not `1/45`.
