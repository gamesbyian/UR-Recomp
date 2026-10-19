# RF066: source-original true post-call reads on the shared chronological axis

**19 October 2026.** Source-authentic research producer only, not a gameplay fix or USA event admission. The upstream Snes9x original, ROM, movie and old RF044 through RF064 source instrumentation remain pinned. **USA event acceptance is 0/45; Windows release gates are 0/12.**

## Authentic RF064 negative result, no speculation

The genuine original/native Zoo execution [run 39216237965](https://github.com/gamesbyian/UR-Recomp/actions/runs/39216237965) has finished. Its [actual case archive](https://github.com/gamesbyian/UR-Recomp/actions/runs/39216237965/artifacts/12170321915), SHA-256 `7891a24124c67f414e9b00ed2bb1dbe2e59e4a2b6c50b558e920c25d885e63ea`, was independently reopened. The original log SHA-256 is `0dfe14195cffc9fc2e044adb372f81c9440e94e4b0e5330671906934d475bfad`. The independently retained [machine receipt](../analysis/data/rf064-authentic-original-real-stack-read-missing-getset-20261019.json) records **903 genuine original PullB/PullW returns (710 word, 193 byte)**, **903 RF063 source-ordered getset entries, all WRITES**, no matching getset READ, one real original post-NMI memory checkpoint, and no recorder overflow. RF064 correctly rejected **all 903** getset *read* attributions, because each true macro getter call saw `before == after`: there was no qualifying RF063 source read entry. This is a recorder blind spot. It does **not** mean no CPU read occurred.

All 78 raw 128-KiB WRAM mesh pairs were independently reopened by the original campaign: 51 exact, 27 non-exact, 92 unmasked differing byte occurrences. Zoom Zoo again completed in +5163, fresh next Bowl entry at +267; source-earned ranked SRAM and cold guest reload were checked. **Neither missing source read rows nor normal game progression warrants a stack difference waiver.**

## New narrow witness and truth boundary

`qa01_rf066_original_consumed_sequence.py` stages only **after** RF044 → RF045 → RF063 → RF064, in disposable original `cpuops.cpp`. It appends a source-local `QA01RF066ORIGCONSUMED` event immediately after the real stack getter has returned, using the original macro's **actual returned byte/word**, and increments the pre-existing RF063 ordinal. It leaves the single Snes9x getter and all CPU, SPC, bus, stack and clock operations unchanged. If another instrumented RF063 event occurs during the getter, it records the interval as uncertain instead of inventing an earlier bus timestamp.

Every row is deliberately `phase=post_real_stack_getter_return`, with stack address, returned value, source clock and host frame, original post-call PB:PC context, and genuine RF063 before/after. **That context PC is not an independently decoded opcode-fetch PC**, and the event's ordinal is at the actual macro-return observation, **not** the middle of the guest's bus cycle. The consumer `qa01_rf066_original_consumed_report.py` requires contiguous source-local ordinals across true getset observations, original real NMI five-byte checkpoint and post-call returns; it separately matches complete RF045 macro and RF064 post-call populations (no missing/duplicate values), rejects overlaps, invalid addresses, overflow, phase forgeries, or synthetic sequencing. It always blocks full QA01 causal-window normalization, and never silently fills the original missing getset reads.

## Reproduce and finish qualification

```bash
# Disposable Snes9x source at pinned upstream commit 1bcc369e...
python3 tools/qa01_rf044_stack_bus_witness.py original --root "$ORIGINAL"
python3 tools/qa01_rf045_source_stack_macro_witness.py --root "$ORIGINAL"
python3 tools/qa01_rf063_original_shared_sequence.py --root "$ORIGINAL"
python3 tools/qa01_rf064_original_post_call_pull.py --root "$ORIGINAL"
python3 tools/qa01_rf066_original_consumed_sequence.py --root "$ORIGINAL"
# Rebuild actual original libretro Snes9x after staging, not before.
# Enable all original RF044, RF045, RF063, RF064, RF066 env flags
# while replaying the exact frozen genuine 2014 USA Zoo source/movie.
python3 tools/qa01_rf066_original_consumed_report.py actual-original.log --out rf066.json
python3 -m unittest tests.unit.test_qa01_rf066_original_consumed_sequence -v
```

The existing original Snes9x C++ compile gate is extended to stage RF066 as well. An actual matched original/native USA replay is still required: freeze source, ROM, movie, input, cores, SRAM and producer provenance; verify returned-value records without masking any WRAM differences; preserve all 78 unmasked checkpoint pairs and Zoo→Bowl/SRAM/Windows boundaries. **No RF066 game replay has yet executed at the time of this instrument's initial PR.** The parallel RF062 native M1X0 sound-read owner and independent continuous-frame QA agent retain their separate ownership.

The next proof question is whether the first **differing** stack byte is actually consumed under an equivalent source/native semantic phase, not merely whether a 65816 stack getter returns a value. No event admission follows from a green compiler or a macro-return log alone.
