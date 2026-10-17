# QA-01: actual USA Zoo 78-sample, 92-byte residual address census

Executed original/native guest evidence, no masks or waivers. This is an
**address-class audit of observed samples**, not proof of equivalent CPU,
instruction ticks, sound or complete gameplay, and **not** a proposal to
ignore stack memory. Accepted USA events: **0/45**.

Source-pinned [genuine Zoo run 39006650922](https://github.com/gamesbyian/UR-Recomp/actions/runs/39006650922),
immutable source `db6c3b2e2ffdb55ea232831626965b6e587f1d56`,
actual downloaded case artifact **12091825707** (ZIP SHA-256
`2785bc65b8ce41bf2c4ddce39b90422a78a27a0f1a84f07a6b546c9095efeeec`).
The `producer-report.json.zoo_race_mesh.samples` census compared **all
131,072 WRAM bytes in each of 78 original/native paired samples**, with
**zero excluded bytes**. Exactly **51/78** full images match. Across the
remaining **27** comparisons there are **92 byte-difference occurrences**.

| Residual address class | Sampled race-relative frames | Count of differing bytes |
| --- | --- | ---: |
| Stack `7E:01ED`–`01F0` (four bytes per sample) | 1, 2, 4, 32, 219, 604, 840, 841, 1080, 1531, 1532, 1720, 1721, 1800, 2160, 2520, 2880, 3120, 3600, 4920 | **80** |
| Stack `7E:01EE` and `01F1` (two bytes per sample) | 5034, 5035, 5036, 5037, 5038 | **10** |
| Sound direct-page pointer `7E:0063` (one byte per sample) | 5040, 5045 | **2** |
| Every other WRAM address | None among these 78 samples | **0** |

Per-address occurrences: `01ED=20`, `01EE=25`, `01EF=20`,
`01F0=20`, `01F1=5`, `0063=2`. This is **90/92** byte
occurrences in the CPU stack page and **2/92** in the live sound pointer;
these are **occurrences** at checkpoint times, *not* ninety distinct
physical addresses, and the 78 checkpoints do **not** constitute a
complete-frame census.

The leading original/native 4-byte differences are **not** attributable to
the RF037 `$0063` pointer alone. At +1, original stack `01ED–01F0`
contains bytes `26 F0 D4 82`, native `81 97 00 55`. At +5034 to
+5038 the two stack addresses disagree while observed `$0063` does
not; at +5040 and +5045 only `$0063` differs. Do not treat the
two sound-byte samples as the explanation for all 27 non-exact
full-memory checkpoints.

**Potential reuse, not a claimed owner identification:** the earlier
[Switcher source/stack crosswalk](QA01-STACK-PAGE-ORIGINAL-PC-CROSSWALK-20261010.md)
already executed original `I_NMI` `PHA` register/stack capture and
native per-write `SNESRECOMP_WLOG_ADDR` with real generated-function
scopes, including `Snd_SendQueuedCommand_M1X0` stack activity around
`01EF–01F3` in *Switcher*. That does **not** establish which original
or native opcode last wrote `01ED–01F1` in *Zoo*. These bytes may be
inactive old return-address residue, live stack operands, different NMI
phases or another scheduling consequence. No one of those possibilities
has been proven here. Prior Switcher instrument scope and original/native
frame axes also cannot be copied as comparable clock readings.

**Exact next CPU-lane experiment, only if RF037 matched writer-stream
evidence does not subsume it:** source-bound original Snes9x
per-opcode/interrupt push, JSR/RTS/RTI and stack read/write provenance at
`01ED–01F1` across true fresh Zoo +1/+32 and +5034..+5045;
source-bound native `cpu_write8/16` and AOT scope/stack operation on
those same bytes, with separate host/CPU/SPC axes and explicit record
truncation. Establish the **last writes and next reads** before inferring
semantic relevance. Compare original/native source opcode and return
mechanics and NMI/beam timing *before* attempting correction. Preserve
unchanged 2014 inputs, immutable original ROM, all 78 unmasked checks,
authentic Zoo +5163, next Bowl +267, earned SRAM/cold record, and 0/45
release admission. Do **not** mask stack bytes, patch clocks by guesswork
or modify independent release ledger.

Machine-readable, checkpoint-exhaustive address-class receipt:
[`analysis/data/qa01-zoo-stack-residual-address-census-20261017.json`](../analysis/data/qa01-zoo-stack-residual-address-census-20261017.json).
