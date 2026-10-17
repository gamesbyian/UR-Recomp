# RF037: original/native sound pointer to CPU/SPC transport

Source-qualified read-only genuine 2014 USA Zoo investigation. No CPU/APU
timing change, no controller input change, and no release credit (0/45).

RF035 proved that the original bank-82 sound upload instructions execute and
native sound-pointer readers advance from C773 to C774 at the first +5040
residual. The original 1024-opcode and native 4096-read logs then truncated
before a complete +5045 transaction could be observed. RF036 already rejected
two genuinely executed IPL CC publication-order changes: unmasked 128 KiB
WRAM exact-pair counts regressed 51/78 to 46/78 and 0/78.

The RF037 source observer is staged into independently pinned disposable
Snes9x and Baldosa research guests after RF030 through RF035. It captures:

- Original executed LDA indirect-pointer, STA 2143 payload, STA 2142
  sequence and CMP 2142 echo, preserving original CPU internal frame,
  program counter, accumulator, pointer and beam.
- Original CPU 2142/2143 real publication and SPC F6/F7 actual receiver
  reads on original, separate SPC-age and CPU beam axes.
- Native sound pointer/sequence live helper reads in the actual recomp
  function scope, plus CPU port schedule, apply and SPC recipient reads
  with queue target, SPC age and native host frame.

Instrumented clocks and frames remain separately attributed; the source
does not assume that original internal CPU frame 6072 equals native host 6057
without a measured registration. The source windows include both actual
+5040 and +5045 boundaries and neighboring frames. Every bounded recorder
provides a truncation sentinel; source reports must fail closed if either
target window is absent or truncated.

One source-pinned 2014 USA ROM/movie/SRAM/script replay must preserve all 78
unmasked original/native whole-WRAM paired checkpoints, all 13 adjacent
+5034 through +5046 sound samples, genuine Zoo +5163 result, next Bowl
+267, eleven full earned 8192-byte SRAM pairs and fresh guest cold record
reload. These are regression controls, not a route around exact full-event
CPU/SPC logic-tick parity or shipping Windows acceptance.

Decision-changing criterion: actual consumed pointer at both divergent
frames linked to the CPU port3 data value / port2 sequence and the SPC's
received port values. If absent, preserve the coverage gap instead of
guessing a scheduling correction. No timing patch until downstream liveness
and source-correct causal order are demonstrated; no masking or manual
phase shifts. Delete the temporary Actions trigger and restore the shared
campaign immediately after source execution queues.
