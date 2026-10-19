# QA01 RF062: independently pin all four genuine source ZIPs before parsing

**Evidence-only integrity hardening, 19 October 2026.** No gameplay code, emulator binaries, source SMV/movie/controller inputs, runtime traces, native physical bus returns or release evidence were changed. This hardening closes an independent provenance gap in the previously merged `tools/qa01_rf062_real_read_raw_archive.py` diagnostic.

## Qualified immutable archives

The RF062 four-ZIP consumer independently combines a historic original RF054 opcode/sound-publication witness with actual RF062 decoded native operand reads, the compiler-generated native live function and three real original/native unmasked raw frame pairs. The source evidence has already been documented as **bounded**, **not a course acceptance**. These **four specific GitHub artifacts**, not arbitrary self-consistent replacements, qualify the original facts:

| Source | Artifact | Immutable original ZIP SHA-256 |
| --- | --- | --- |
| RF054 actual historic original/native producer | `12149640496` | `3ccb209a92045e9e89113442e68af51b85a453a160a9b9efaf8ca0d59e79631c` |
| RF062 genuine executed native `82:82F0` case | `12214214743` | `b8287234d2fe515ee32b19b3d2a9b0e1bb58104b437de3a5cbe2e32e3af093ff` |
| Executed generated-native ELF/static provenance | `12215541266` | `5d6ffbf1313d83961f496f3c7dc83021323d76fcd977dfc2662ef9afbf6c7b46` |
| RF062 independent 3-frame original/native raw capture | `12216270293` | `85b8585539001210e4a9d2b22e5484034679fbda5d40808300d221e1ec583aed` |

Before editing, the consumer compared the *first* archive with its independently published original SHA, but only recalculated the other three ZIP hashes **after** parsing them. That is insufficient: a replaced archive with internally consistent altered report/manifest/raw values can produce a new apparently legitimate receipt. It need not preserve the earlier independently qualified authentic run. ZIP archives can also have duplicate member paths, allowing readers to disagree about which byte set is authoritative.

The new `independently_pin_zip` checks **all four** files before extraction or evidence interpretation. Its reusable `qualified_zip_snapshot` closes a further pathname replacement gap: it verifies SHA-256, all members and CRCs against **one size-bounded immutable byte snapshot**, and both archive and script-only consumers parse those same retained bytes rather than reopening source paths after qualification. It requires the exact externally published SHA-256, actual regular file (not symlink), reasonable size ceilings, safe unique names (no absolute or parent-traversal paths, symlink or directory entries), bounded total uncompressed contents and successful CRC verification for every member. It rejects altered **unconsumed** members as well as altered proof-bearing ones. Only then does the existing original/operand/helper/binary/raw forensic consumer execute unchanged and report the four actually qualified ZIP identities plus explicit `all_four_actual_original_native_ZIP_SHA256_pins_verified=true` and `all_four_ZIP_member_names_unique_and_CRC_qualified=true`.

I independently downloaded all four genuine artifacts before adding the new limits. Their actual original ZIP SHA values above match; member populations are **18, 407, 5, 431**, respectively, with no archive directories and with good CRCs. The largest single uncompressed item is under 32 MiB and no entire case exceeds 81 MiB uncompressed, well within these bounds. Synthetic tests specifically test a replacement archive carrying an irrelevant extra file, forged independently rehashed duplicates, symlink/path traversal entries, a bad member CRC despite an updated outer SHA, absent inputs and aliased files.

## Reproduce the genuine script-provenance result without pretending a cold pass

The separately qualified script-only consumer succeeds on the exact four ZIPs and reports a mandatory HOLD for instrumented cold reload and observation timing. The original strict four-ZIP consumer **still rejects** the raw case's changed source replay script SHA.

```bash
python3 tools/qa01_rf062_script_only_provenance.py \
  --baseline /immutable/RF054-12149640496.zip \
  --native /immutable/RF062-12214214743.zip \
  --binaries /immutable/RF062-12215541266.zip \
  --raw-pair /immutable/RF062-12216270293.zip \
  --output /fresh/qa01-four-zip-SCRIPT-provenance-only.json
```

The **archive-only** workflow reopens the four genuine ZIPs, tests malicious fixtures, requires the existing strict forensic consumer to **reject the changed raw script SHA**, then separately executes tools/qa01_rf062_script_only_provenance.py and publishes a compact **source-difference, non-admission** JSON receipt. The original strict admission criterion remains unchanged. It never builds/runs an emulator, launches a research factory, stores a retail ROM or promotes any course. The true native `82:82F0` read `11:C774 → D0` and original RF049 comparison remain bounded positive evidence; RF062's changed helper population **656 → 655**, different source/native binaries and the strict cold-script/provenance failure are preserved as **negative controls**, not normalized away. No original/native clock-domain parity, uninstrumented-baseline preservation, whole-event gameplay fidelity, earned Windows persistence or actual first differing consumed byte follows.

**Admission is unchanged: 0/45 original USA events, 0/12 Windows release QA gates.**

## Raw replay source-script identity is a separate strict boundary

The first archived four-ZIP end-to-end run correctly **failed** the pre-existing strict reviewer at its unchanged input/script SHA assertion. This was NOT failure of the new four immutable ZIP hashes or member CRCs. The original RF054/no-raw native RF062 replay script SHA256 is 1eb3e8416b7fa40935d097c78d281ca98537c9a555e23f1906a99912dcdb2c52; the raw-capture case replay script SHA256 is 92012c94af3a27c54144e34c9d1d7a6cdb97ddf3e519d3f24c375c7c76bf6bc2. These are genuinely different source replay scripts.

An exact literal command comparison independently reopens the archived scripts and identifies a single qualifying textual substitution: after the existing scene-05100 dump, baseline 'wait 20' is split into 'wait 5', dump qa01-frame-005105, 'wait 1', dump qa01-frame-005106, 'wait 1', dump qa01-frame-005107, 'wait 13', followed by the unchanged scene-05120 dump. The waits still sum to 20. Both original Snes9x ref.input and native Baldosa pinned-baldosa.input files remain **byte-identical across these two genuine runs** and their hashes/lengths match each producer's independent controller-file receipts.

The separate ROM-free source-control checker (tools/qa01_rf062_script_only_provenance.py) rejects any additional controller command, changed wait sum, swapped/absent dump, missing input, changed ROM/movie/SRAM seed or guest origin. Critically its true result **does not mean three dumps were behaviorally neutral**. Its machine output explicitly sets strict_original_raw_guest_script_SHA_equivalence_proven=false, cold_process_reload_proven_for_changed_script=false, observer_noninterference_proven=false, native_helper_population_656_vs_655_explained_as_benign=false, and accepted_USA_events=0. It explains the scripts; it cannot prove matching instruction-time behavior.

The archive-only [qualification run 39318682289](https://github.com/gamesbyian/UR-Recomp/actions/runs/39318682289) PASSED by independently validating all four exact original ZIPs, verifying the changed script and unchanged two actual guest controller files, and requiring the **original strict reviewer to fail for precisely the known replay-script SHA mismatch**. The strict rejection remains a mandatory negative control, not a waiver or a gameplay pass. Future native probe on/off attribution still requires equivalent binary family and independently qualified observation phase. **0/45 USA events, 0/12 release QA gates**.
