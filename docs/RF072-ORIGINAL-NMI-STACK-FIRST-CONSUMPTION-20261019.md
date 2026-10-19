# RF072: real 2014 original post-NMI stack bytes are consumed before overwrite

**Source-authentic original-65816 finding, October 19, 2026.** The [RF069 genuinely executed Zoo archive](https://github.com/gamesbyian/UR-Recomp/actions/runs/39307624432) is now independently verified by [RF071's 903-row actual getset-entry-to-return consumer](RF071-AUTHENTIC-ORIGINAL-GETSET-RETURN-TRANSACTIONS-20261019.md) and its separate [artifact-verifier run 39310950499](https://github.com/gamesbyian/UR-Recomp/actions/runs/39310950499). RF072 narrows the original-side causal question: **what happens to each of the five real original stack bytes after an NMI push, before its next recorded stack write?**

The original real `post_real_nmi_push` at original host frame 1017 / source global event sequence **193** physically sampled `00:01ED..01F1 = 26 F0 D4 82 26`. Before any next observed original stack getset writer for those addresses, **all five bytes are actually read and returned** through RF044/RF063 true getset entries qualified by RF071's RF045/RF064/RF066 real post-call witnesses:

| Byte | Physical checkpoint | First source getset read | First subsequent source getset overwrite |
|---|---|---|---|
| `00:01ED` | `26` | seq **194**, `26`, source PC context `80:B0EB` | seq **210**, `B9` |
| `00:01EE` | `F0` | seq **196**, `F0`, context `80:B0EB` | seq **210**, `85` |
| `00:01EF` | `D4` | seq **196**, `D4`, context `80:B0EB` | seq **203**, `01` |
| `00:01F0` | `82` | seq **198**, `82`, context `80:D4F0` | seq **203**, `00` |
| `00:01F1` | `26` | seq **200**, `26`, context `82:D4F5` | seq **202**, `00` |

The word read at `00:01EE` contributes both actual little-endian bytes `F0 D4`; its **entire word** `D4F0` was independently matched to the macro return, not created from a nearby memory sample. Every first source read returns the exact five unmasked bytes sampled immediately after the genuine original NMI push.

This is an important **negative result for the unconsumed-stale-stack hypothesis**: the original 65816 actually reads all five source bytes, so **we must not waive original/native raw stack differences on the assumption that nobody reads them**.

## How the verifier avoids false proof

`tools/qa01_rf072_original_postnmi_first_byte_fates.py` reopens the frozen ZIP via [RF071's full authenticated-case verifier](../tools/qa01_rf071_original_real_read_join.py), requiring actual read-entry→post-call returned-value transactions before crediting any byte read. It takes the actual unmasked checkpoint and subsequent source-global bus event ordinal; splits real word reads/writes by little-endian byte; reports the first read and first write for each byte; rejects an unbound getset entry or a first read that contradicts the unchanged checkpoint without a preceding observed write.

A write *before* the first real read is explicitly classified as `first_observed_write_precedes_read`, not promoted. Other guest CPU, DMA or unobserved paths are **not proven absent**. All source event PC snapshots remain live original CPU state **contexts**, not independently decoded opcode-fetch PCs.

This is **only an original Snes9x event ordering**. The 78 original/native full 128KiB WRAM checkpoints still include **92 unmasked differing-byte occurrences**, and the native emulator has not yet shown an **independently semantically matched post-NMI checkpoint with executed native first-byte read/overwrite events and qualified decoded opcode PC**. A raw sampled host-frame difference, or an apparent common `0x26` NMI status byte, is not itself that cross-emulator equivalence proof. Preserve separate original/native clocks, distinct phases and all differences.

```bash
python3 tools/qa01_rf072_original_postnmi_first_byte_fates.py \
  /path/to/exact-rf069-Zoo-case.zip --out /path/to/rf072-first-source-byte-fates.json
python3 -m unittest tests.unit.test_qa01_rf072_original_postnmi_first_byte_fates -v
```

The [machine source receipt](../analysis/data/rf072-authentic-original-postnmi-stack-first-read-before-write-20261019.json) retains every actual original source first read and first next observed write. Nothing is added to an emulator or shipped product; this is an independent strict archived-evidence consumer, **not** `qa01_causal_window.py` normalization. **0/45 USA events accepted, 0/12 Windows release QA gates.**

## Independent archive-executed confirmation

The temporary **read-only** [RF072 archive run 39312520355](https://github.com/gamesbyian/UR-Recomp/actions/runs/39312520355) downloaded the exact source-authenticated original/native Zoo case, SHA256-validated its bytes, invoked the full RF071+RF072 consumers on the real captured original bus log, and successfully archived a recomputed five-byte report. Its [artifact 12215937413](https://github.com/gamesbyian/UR-Recomp/actions/runs/39312520355/artifacts/12215937413), ZIP SHA256 `35a6e4d10be39021816b6c466ebac6285bc7980395cebfaf16a6f6ea1bf37a6a`, was independently reopened and verified CRC-clean. All five real read/first-writer source ordinals, original V/H clocks, exact raw checkpoint `26F0D48226`, 903 prerequisite true original getter→return witnesses, 92 unmasked paired WRAM differences and **zero USA event credit** agree with the permanent [RF072 machine receipt](../analysis/data/rf072-authentic-original-postnmi-stack-first-read-before-write-20261019.json). The temporary validation workflow is research-only and must not merge.

These five original real getter reads are **observed after the original source's own post-NMI push**, before its own next getset writer. This does not establish that the native emulator's differing host-frame stack bytes were present at the exact same intra-frame semantic stage; the native side requires its independently executed first-read/overwrite sequence and decoded opcode identity. Therefore the source result is positive evidence of **consumption**, not proof of an original/native *consumed-value difference*, a waiver, or a finished USA course.
