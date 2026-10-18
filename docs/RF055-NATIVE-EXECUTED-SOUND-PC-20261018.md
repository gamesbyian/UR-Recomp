# RF055: executed native opcode identity at the late Zoo sound transfer

**Research-only; complete USA events accepted: 0/45.** This inherits the exact
2014 USA Zoo experiment, not a new emulator, ROM, route, 45-course factory or
shipping fix. The scope is original/native CPU↔SPC causality and *only* the
previously verified RF054 11:C774/D0/63 upload transaction.

## Resolved source evidence, existing controls

* Merged [RF054 #1838](https://github.com/gamesbyian/UR-Recomp/pull/1838)
  established a genuine native CPU read helper of ROM `11:C774`,
  A=`630D`, at host6124/master2188739002 in
  `Snd_UploadBlockList_82EF_M1X0`. Same native compiled scope invokes real
  `RtlApuWrite` port3=D0/master2188739032 and port2=63/master2188739082.
* Actual original USA `82:82F0 LDA [$63],Y` consumes `11:C774`,
  A=`630D→63D0`; real original Snes9x CPU→APU writes D0/63 at original
  SPC ages104485254/258. Native queue applies the same transfer at native
  ages104485230/233, followed by genuine native SPC reads at238/243/247.
* Original/native *whole* 322-step SPC700 F6/F7 PC/port/value read sequence
  agrees uniquely within 1,959 native reads; corresponding original-minus-native
  local SPC ages alternate between 22 and 23. That does not register original
  and native absolute CPU clocks, or justify an offset/timing patch.
* Original/native Zoo +5163, next Bowl +267, eleven full earned SRAM pairs,
  separate guest cold ranked reload and original 78 whole unmasked 128KiB WRAM
  checkpoints (51 exact, 92 different-byte occurrences) remain required.
  Every original USA ROM, movie, input and seed SRAM identity must match
  immutable RF047 baseline artifact 12124654817 and RF052 source artifact
  12136344183; `strict_candidate` grants **zero** event credit.

## Independent archive-only 65816 local master-clock constraint

[Original RF054 authenticated replay 39161563837](https://github.com/gamesbyian/UR-Recomp/actions/runs/39161563837), artifact12149640496
SHA256 `3ccb209a92045e9e89113442e68af51b85a453a160a9b9efaf8ca0d59e79631c`,
includes 38 genuinely executed original `S9xAPUWritePort` records
in RF050 and 1,312 genuinely invoked native `RtlApuWrite` CPU records in
RF054. Pair each *adjacent real port3→port2 instruction publication* and
measure original Snes9x local beam-master interval
`(V₂−V₁)×1364+(H₂−H₁)` against native actual
`CPU.master_cycles` subtraction. **All 16/16 original and 656/656 native
pairs are exactly 50 local CPU master clocks**. The original source-local
SPC-age gaps were **2 ticks ×8** and **4 ticks ×8**, so equal CPU master
intervals must not be mistaken for equal CPU→SPC port queue visibility or
absolute CPU/SPC epoch registration. All 656 native actual `cpu_read8`
ROM operand effective addresses form an *unbroken* bank11 byte sequence
`11:C589..11:C818`, with the independently established target
`11:C774` as index492 (one-based). [Immutable machine census](../analysis/data/rf055-original-native-cpu-local-writer-interval-census-20261018.json).
No correction or complete-event credit follows; the earlier genuine six-vs-three
sound echo polls remain a separate observed CPU execution difference.

## Executed source-PC discriminator

The pinned Baldosa v2 emitter
`baldosa/snesrecomp@075fbe4c8e0d97b0013be541795c39cb644a9709`
uses the actual decoded `di_insn.addr` and an instruction-IR loop in
`recompiler/v2/emit_function.py`. RF055 adds a disposable code-generation
probe **before each existing instruction IR**, with exactly three gated 65816
guest PCs: `82:82F0`, `82:82F2`, `82:82F6`. It records the emitted
guest-PC constant, native host6124 CPU master clock, A/Y/D and direct DP
pointer bytes. A generated instruction site executing is stronger than an
adjacent name of a C function; the runtime does *not* read a separate guest
program counter. RF055 explicitly labels this source-qualified generated-PC
identity, not an original/native common clock origin.

The companion fail-closed reporter requires an entire ordered
**F0-PC → actual ROM cpu_read8 → F2-PC → actual port3 → F6-PC → actual
port2** chain, correct real effective pointer address and A/port values.
It independently reuses RF054's verified genuine 322-step SPC receiver
alignment and its full RF047 Zoo/Bowl/SRAM comparator controls. Synthetic
negative tests reject missing or spoofed PC, changed clocks/operand/owner,
missing rows and altered output. No unsampled-logic, audio sample, native
65816 instruction-tick, Windows PE or complete-USA-event equality is claimed.

## One-shot execution and first attempted result

[One-shot run 39165841295](https://github.com/gamesbyian/UR-Recomp/actions/runs/39165841295)
was launched with exact research source
`5c8135dbcc979ab3283ac7227a0cb2db7843b5aa`.
Plan passed; **build verification failed before compilers or genuine replay**:
the unit-generated Python emitter fixture exposed a nested quotation escaping
error at `f""QA01RF055...`. This is **harness failure**, neither an observed
guest opcode mismatch nor a timing regression; it cannot be counted as RF055
original/native experimental evidence. The one-shot push trigger was removed
immediately and reusable QA workflow restored byte-for-byte to baseline.

The correction restores the two string-escaping layers (outer observer patch
text → Python native emitter source → emitted C string), rather than suppressing
the failing test. Another one-shot is justified **only after** the current
RF055 unit/hygiene checks pass; stop on first producer failure, examine its
first failing step, never repeatedly poll/cancel Actions or start a factory.

## Decision gate

If source-qualified replay produces one-to-one generated 82:82F0/82F2/82F6
identities and the immutable controls, record exact per-instruction/master
clock and narrow what is still missing for first event. Otherwise retain the
unproven generated-PC link, report failed exact artifact and stop. Either way,
the earliest *consumer-meaningful* residual at Zoo +5040/+5045 still needs its
actual source/native producer/read/port lifecycle; a late matched source
transaction alone cannot waive those residuals. An independently accepted
complete USA event remains **0/45**, and this research lane never edits the
shipping CPU/APU, graphics, Modern, release package, observation mask or QA
ledger.

**Qualified bounded retry:** Source fixture escaping and exact 24-bit decoded guest-PC guard were repaired and actual [unit run39166846551](https://github.com/gamesbyian/UR-Recomp/actions/runs/39166846551) plus [hygiene39166846606](https://github.com/gamesbyian/UR-Recomp/actions/runs/39166846606) finished green. [One-shot run39167048486](https://github.com/gamesbyian/UR-Recomp/actions/runs/39167048486) checked out immutable source `3148dc522e03549823a8ed1305a996dc9bc3a02d` and passed the pinned original/native **build**. The actual guest-replay decision requires its preserved case logs; no replay result is inferred from successful compilation. Immediately after scheduling, the second one-shot trigger was removed and the reusable campaign restored byte-for-byte to main. This experiment must stop on the actual reporter's earliest genuine failure without further speculative timing trials.
