# QA-12: independent two-artifact native Windows pre/post Records pair admission

**Status: independently rehashed ACTUAL paired pre/post archives from successful exact-head Windows #1550, together with its exact packaged executable; standalone reusable reader awaiting hotfix #1556 merge and exact-current-head CI.** No release gate promotion, current candidate nomination or original USA course census change. Merged Modern producer [#1550](https://github.com/gamesbyian/UR-Recomp/pull/1550) created both stage archives on **one** successful Win32 Actions run 38610654367. Independent QA owns the binary-byte comparison; the producer's own assertions are not enough.

The existing independent [#1548](https://github.com/gamesbyian/UR-Recomp/pull/1548) parser verifies the *post-Records* bounded source ZIP's six original-native processes, real original guest GO/result and fresh viewer receipts, paired run/match internal FNV, matching MIKE/MARTIN source score, raw SRAM, typed mirrors and catalog. [#1549](https://github.com/gamesbyian/UR-Recomp/pull/1549) insists on an exact **whole archive** member allowlist. Keep this ZIP unchanged.

The new **separate** pre-view artifact from #1550 carries precisely three files at archive root: \`manifest.json\`, a canonical \`multiplayer-runs/run-*.urrun\`, and its \`*.urrun.urmatch\` sidecar. The stage manifest asserts \`after-real-play-before-first-records-viewer\`. The reader independently rehashes **both actual ZIPs** against externally recorded complete archive SHA-256 values; checks the exact three members, no links/oversized/extra members or forged release status, and rehashes both raw pre-view files against the exact stage manifest. It then compares the two **actual saved files byte-for-byte** to the post-view files from the independently decoded original-native source ZIP. Corrupt, missing, re-signed modified, redirected/symlinked and mismatched source evidence fails closed.

Usage, **only after downloading actual artifacts** and recording their true SHA-256:

    python3 tools/check_baldosa_win32_pair_pre_post_qa.py \
      --before-zip /tmp/actual-pre-records-pair-actions.zip \
      --expected-before-sha256 <64-digit actual pre ZIP hash> \
      --after-zip /tmp/actual-source-and-post-pair-actions.zip \
      --expected-after-sha256 <64-digit actual post ZIP hash>

The tool returns \`independently_compared_archived_run_and_sidecar_bytes_equal=true\` only after decoding and comparing the real bytes. It intentionally returns \`source_stage_before_first_records_independently_timestamped=false\` and \`same_GitHub_Actions_run_provenance_independently_verified=false\`: the files and producer manifest do not themselves independently prove when they were captured or that a user downloaded both from the same CI run. QA must separately inspect **the exact successful Windows job's step order, run ID, source head, uploaded artifact IDs and SHA256 identities**, rather than combining an old source ZIP with a new pre-view archive and calling that final candidate evidence. A producer-reported \`stage\` string is never independent timing proof.

ROM-free \`tests/unit/test_check_baldosa_win32_pair_pre_post_qa.py\` fixtures exercise positive contracts and adversarial failures, but they are synthetic. This is L2/L3 **source-archival immutability evidence at most**, not OS power-cut durability, same-process live file observation, original/reference emulator complete race equality, two physical controllers, gamepad/audio hardware, or a Windows final release candidate. \`QA-12\` remains unverified L4 until a nominated same-source package and independent evidence establish its gate.

## First independent actual-byte acceptance, scoped to PR-head packaged Windows

Actual green source job [38610654367](https://github.com/gamesbyian/UR-Recomp/actions/runs/38610654367) compiled and ran the exact Modern #1550 head `92e704122a7704c87c75e32f3c362424b51e802f`. Independent QA downloaded all three Actions artifacts through GitHub and computed full archive SHA-256s, then read the actual original guest process logs, raw files, FNV checksums, both 8192-byte SRAM and full Windows candidate member digests:

| Real same-job artifact | Artifact ID | Full ZIP SHA-256 |
| --- | --- | --- |
| Pre-Records pair-only, three members (1,397 bytes) | `11918391750` | `db5377e14b94e110b1c7e59eaeee9552501728de6ecf4ddf940756ae8c2edd4d` |
| Post-Records full 52-member source/archive (59,296 bytes) | `11918271751` | `e06fb7d2ebb2b53ab583fd298197696af90fc004cebd34644e256c3bb277954e` |
| ROM-free Windows package wrapper (5,940,000 bytes) | `11917682149` | `1e8e8cbf4bfc544f7a3ae40ef7ea5659dab373f8ff4c39deee9ba17f0027055a` |

The independently decoded **inner Windows ZIP** SHA-256 is `b0d959041d0f7768bf2a4367dca1bec35a2b5a0a88b1ba738f219395fe152acb`; executable `UniracersSNESRecomp.exe` is 19,750,400 bytes, SHA-256 `b5a6e770446d1df04a46b64695659a721b46f48c7f50d734e39c18950756965a`, authentic AMD64/PE32+ header. Manifest's `project_revision=3fe029090f0058e8fc03495cba370e4e6e5702d5` is a separate Baldosa source input, **not the Modern PR SHA or merged-main release identity**. Four package members only, no ROM or private player save.

The **actual archived pre-view run and sidecar bytes match the actual post-view run and sidecar byte-for-byte**, not merely by producer assertions. Run SHA-256 `346296f664ccf37fd0310666a60d837269a6d1627b4f28162ad051d6c66c8a41`, independently recomputed canonical FNV `01b72ad6fb9b9a2a`; sidecar SHA `e1440b455b617a1726ccf17aa7a2e7dc96af7faabe302d9006693923125259c4`, FNV `d214a7509ef52d81`. Original native result: 2,231 input frames in five input runs, MIKE0 27.61 LOSS, MARTIN2 27.57 WIN. Same artifact contains genuine MIKE/MARTIN two-player process and independent fresh Records logs, plus gamepad-semantic native MIKE→MARTIN selector. Both riders' raw 8KiB SRAM and exact typed mirrors, catalog and final selector independently rehashed. Machine-readable non-sensitive evidence: [analysis/evidence/baldosa-win32-38610654367-created-pair-prepost-review.json](../analysis/evidence/baldosa-win32-38610654367-created-pair-prepost-review.json).

**Proof boundary:** two genuinely downloaded same-GitHub-run **archived bytes** are equal across the producer-named pre/post stages; the source job and probe code support capture order, but no independent OS timestamp or live file-change monitor was captured. The test-owned SDL semantic gamepad is not physical hardware; dummy audio cannot establish audible output. The executable and inner ZIP are exact on the **premerge producer SHA**, not separately rerun as a final merged-main consumer candidate. Original emulator course event strict USA `0/45` remains, and OS power-loss/disk-full/crash-before-receipt cases remain unaccepted. The #1549 archive-wide overrestriction against the genuine 52-member post source ZIP required the follow-up #1556 hotfix to read whole evidence archive while still denying unknown other members.

**Stop rule:** no additional broad factory is required for this specific source gap. Finish independent reader exact-head CI and hotfix #1556, then verify the actual archives through that checked-in command. Preserve run/ZIP/EXE SHA provenance and continue with true merged-main packaged Windows and physical hardware acceptance. No QA-12/L4 promotion.

