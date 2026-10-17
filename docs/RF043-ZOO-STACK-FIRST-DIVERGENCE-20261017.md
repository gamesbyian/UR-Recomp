# RF043: earliest Zoo stack residual is +1, not late sound phase

**Source-qualified from the existing genuine USA Zoo RF041 control archive, no new hosted research run or gameplay correction. Strict complete USA events 0/45.**

## Immutable source evidence and executable audit

[RF041 genuine original/native case](https://github.com/gamesbyian/UR-Recomp/actions/runs/39069703970/artifacts/12115251490), 18-file ZIP SHA-256 `1c21481aff42ab3580f6292d94c3b0f255d71d8c548b688f2f4d00ae4190ebb0`, records 78 independently paired complete **131,072-byte original/native WRAM samples**, masking/exclusions zero. Source-original archived 2014 movie entered the circuit at movie frame **3190**; independent fresh original/native guest entries were at **host frame 1017**. These are different clock axes and must not be silently rebased or equated with CPU instruction clocks.

From all 78 full byte comparisons, **27 sampled frames** contain unmasked differences, totaling exactly **92** differing-byte occurrences: **20 frames × four** bytes at `7E:01ED–01F0` = 80; **five frames × two** at `7E:01EE` and `7E:01F1` = 10; **two frames × one** live sound pointer `7E:0063` = 2. No other WRAM address differs in these samples.

The **first divergence is at race-relative frame +1 / absolute fresh original/native host frame 1018**, immediately after verified fully byte-exact frame +0 / host 1017. The four differing stack bytes are:

| Address | Original at +1 (hex) | Native at +1 (hex) |
| --- | --- | --- |
| `7E:01ED` | `26` | `81` |
| `7E:01EE` | `F0` | `97` |
| `7E:01EF` | `D4` | `00` |
| `7E:01F0` | `82` | `55` |

At +2 and +4, all four addresses still differ (some values change); by **+8 / host1025**, the **entire unmasked 128-KiB WRAM images match again**. Their later recurrence is at +32, +219, +604, +840/+841, +1080, +1531/+1532, +1720/+1721, +1800, +2160, +2520, +2880, +3120, +3600 and +4920. The separate short late two-address window is +5034..+5038; the two live sound pointer differences are +5040 and +5045. All of these samples remain unmasked in acceptance.

The dependency-free `tools/qa01_rf043_zoo_first_stack_window.py` reads the existing case ZIP, verifies its SHA-256 and every one of the 78 complete observation pairs, checks this precise distribution and returns the machine-readable first causal window:

```bash
python3 tools/qa01_rf043_zoo_first_stack_window.py \
  /path/to/qa01-campaign-case-zoom-zoo.zip \
  --output analysis/data/local-rf043-stack-window.json
```

This audit *qualifies where to instrument*, **not** the actual last writer or next reader. It asserts no stack byte is safe to mask, no CPU opcode or IRQ/NMI causal chain is proved, and no USA event is accepted.

## Next minimal executed original/native witness

Start with the existing pinned original/native Zoo producers and authentic 2014 input, preserving original/source process separation and the established entry host frame. **Capture the precise CPU stack writes and reads from host1017 through host1025, inclusive, with extra focus on host1017→1018.** Original Snes9x instrumentation should wrap the single actual executed 65816 opcode (pre/post `7E:01ED–01F1`, original PB:PC/opcode and S register) and actual NMI/IRQ entry+return stack push/pop, capturing both opcode and non-opcode interrupt writes. Native Baldosa instrumentation should record real `cpu_read8/16` and `cpu_write8/16` WRAM helper accesses, actual host frame / guest register S, last recomp scope and actual interrupt provenance. Reuse existing read-only [Switcher opcode stack probe](../tools/instrument_snesref_qa01_switcher_stack.py), [native writer frame gate](../tools/baldosa_qa_native_writer_window_patch.py), [native stack read scope](../tools/qa01_native_stack_read_patch.py) and NMI/RTI tracing as *patterns*, but **do not blindly reuse Switcher address/frame assumptions**, synthesize a stack writer or assume an ordinary opcode rather than an NMI pushed the bytes. A pre/post-opcode *change* is only a writer candidate until its actual bus store and later read are separately observed.

A source-qualified first difference requires both guest processes and their exact original/native ROM/input source identities, a unique last writer to each of four bytes during host1017→1018, the first actual reader (if any) before overwrite, interrupt/NMI provenance, bounded recorder truncation guards, and independent unchanged control runs. Stop the experiment once this first bracket is decided; do not expand to full-event factories, masks, speculative clock shifts or a Windows release claim. Subsequent +5034 stack recurrence can reuse the same independently calibrated source witness only if the first cause is demonstrated.

**0/45 complete original/native USA events.** Next action should implement this bounded read/write/NMI observer and run one decision-bearing original/native replay, not additional timing-model volume.
