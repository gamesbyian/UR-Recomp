# QA-12: independent two-artifact native Windows pre/post Records pair admission

**Status: consumer implemented, genuine pre/post source not yet independently observed.** No release gate promotion, current candidate nomination or original USA course census change. Modern producer [#1550](https://github.com/gamesbyian/UR-Recomp/pull/1550) owns creating the two stage archives on **one** Win32 Actions run. Independent QA owns the binary-byte comparison; the producer's own assertions are not enough.

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

**Stop rule:** Do not run broad QA factories or build another native harness for this specific gap. First require the exact-head real Windows result and *both original downloaded archives* from #1550, then apply the existing two-source-archive reader on those hashes. If either artifact is absent/ambiguous, record missingness and leave gate unchanged.
