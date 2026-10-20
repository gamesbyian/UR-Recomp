# QA01/07: independent RF076 complete native nine-bracket evidence, still HOLD

**19 October 2026. Genuine archive-only adjudication, not a new original/native execution. USA 0/45, Windows QA 0/12.**

This updates the [first USA event missing-witness matrix](QA01-FIRST-USA-EVENT-MISSING-WITNESS-MATRIX-20261019.md) with new authentic evidence beyond RF076's truncated 8,192-event attempt. It does not supersede the [original-course census](ORIGINAL-COURSE-EVENT-CENSUS.md) or [release ledger](RELEASE-QUALITY-LEDGER.json). See [machine-verifiable independent receipt](../analysis/data/qa01-rf076-native-nine-bracket-independent-20261019.json).

## Exact genuine byte identities

* Run [39340150765](https://github.com/gamesbyian/UR-Recomp/actions/runs/39340150765), **original** case artifact [12229745143](https://github.com/gamesbyian/UR-Recomp/actions/runs/39340150765/artifacts/12229745143), SHA-256 `33119ca55e3868981e7760c83e1796daa47b6fc72274c14588f72086b37609e4`, **416 CRC-valid members**.
* Separate real compiled-binary artifact **12229240455**, SHA-256 `68bcdc28dbd2751cf61a9a8206414ea8d63bac10c987877fe30e7471504e0a39`, **9 CRC-valid members**. All three actual executable bytes were independently rehashed against `SHA256SUMS` in both ZIPs: native `ca58d0d8…2799bbfc`, reference Snes9x core `7300d5fa…1dd1684`, `snesref` `5fb3cca1…a3bcc18a`.
* Source **Actions merge checkout** `477d738bad9fd514ad0f11e97c9b1561391f0859`; do not call that the transient #1991 branch head. Original log SHA-256 `f357f876f61b687aae8f42aa10c2505aa81ea8438a266925192dbb318967d308`; native log `eda4004608338d82b7947e942a1f9a9969c2fe6e6d4389382a002ca4d7779421`.
* These original Actions artifacts expire **26 October 2026**. Preserve exact bytes after source qualification, with original inner ZIP digests retained, rather than silently treating any newly packaged wrapper as the original research execution.

## Reproduced independent observations

The new original/native Zoo case has **78 full 131,072-byte paired race WRAM samples**, of which **51 are exactly equal and 27 unequal**, totaling **92 unmasked differing byte occurrences**. Direct recomputation: `7E:01ED=20`, `01EE=25`, `01EF=20`, `01F0=20`, `01F1=5`, `0063=2`. All **97 retained named 8,192-byte original/native SRAM samples** are equal. The first sampled unequal WRAM pair occurs at relative +1: original five stack bytes `26 f0 d4 82 26`, native `81 97 00 55 26`. These are **sampled stack values**, not a same-instruction read or proof of the first causally consumed differing byte.

The native RF047 source log genuinely supplies **47,853 contiguous sequence IDs** without the earlier overflow marker, including **45,103 selected decoded opcode markers, 2,705 recorded stack-helper reads and nine complete** `entry → resume_origin → after_push → compiled_rti → handler_return` brackets at native host labels 1017–1025. Independent source-local cross-check recovers each latest scheduler `deadline_unwind` assignment to `82D4EE`, followed by the first **observed selected tier-AOT** post-handler marker `82D4EE`. This materially upgrades **native-local** NMI provenance. It does **not** prove an independent literal opcode ROM bus fetch or equal original/native intraframe instruction phase: only selected AOT sites were marked, with source/native clocks distinct.

**New adversarial transport caveat:** direct scrutiny of the complete genuine native physical log found **75 lines containing an RF047 marker preceded by a partial, interleaved RF044 log prefix**. By RF047 stage: **73 `read`, two `compiled_rti`**. Their complete RF047 suffixes and monotonically sequenced IDs are recoverable, so this does not retract the bounded nine-bracket finding, but an **atomic, fully isolated native physical event stream is not proved**. Do not treat those interleaved original/native diagnostic strings as reliable proof of first exact byte consumption or zero observer interference. Record source event transport contamination explicitly; Agent 1 owns optional producer correction.

## Time-bounded original research archive preserved

The source-only [independent qualification run 39344364860](https://github.com/gamesbyian/UR-Recomp/actions/runs/39344364860) **passed**, including 72 ROM-free tests, independent reopening of both original ZIPs and all 78 raw 128-KiB WRAM pairs, nine authentic native brackets and the **75 interleaved physical log rows**. The two original source provider artifacts expire **2026-10-26**.

The qualified run retained the *original ZIP bytes* for 90 days in [artifact 12230088756](https://github.com/gamesbyian/UR-Recomp/actions/runs/39344364860/artifacts/12230088756), outer wrapper SHA256 `b041dace391e3cbcc5cf02862515617e122aec23364ec2970fb951c31d48a66e`, expiring **2027-01-17**. Its actual `case.zip` nested bytes hash `33119ca55…` and `binaries.zip` nested bytes hash `68bcdc28…`, each exactly matching the original provider artifact. The existing QA archive-only workflow now checks this new wrapper **and both original inner SHA pins** and compares them byte-for-byte against current provider objects before expiry. If either original expires, only the same already-qualified inner bytes may be substituted; the new wrapper is never misidentified as the original research execution. The actual expiry/fallback branch has not yet been triggered in hosted CI.

## Adjacent 2014 Bowl original-source preservation

The separately genuine 2014 Bowl evidence archive from [run 39168164480](https://github.com/gamesbyian/UR-Recomp/actions/runs/39168164480), original artifact **12151357791**, expires **2026-10-25 21:38 UTC**. QA independently downloaded and CRC-checked its **62 source ZIP members**, outer SHA256 `2924534f2700714c655647b43e2453c54d4e76f0e258566bcf500439d962ea79`, separately from both RF076 Zoo epochs.

The existing archived-source CI successfully preserved its original bytes in 90-day [artifact 12231290433](https://github.com/gamesbyian/UR-Recomp/actions/runs/39345167503/artifacts/12231290433), wrapper SHA256 `1a3f11c178c5c0f6eb170b97c1ff7336e548e3d80b452d135dfcb1a64babe9b1`, expiring **2027-01-18**. Its sole inner `genuine-bowl.zip` has exactly the original `2924534f...` digest. The workflow now verifies both wrapper and inner original SHA before comparing current-provider bytes, with **exact-inner-only** fallback after expiry. This is an archive continuity improvement, not a newly qualified gameplay case; the Bowl's historical WRAM/SRAM differences, bounded source result and **0/45** remain unchanged.

## Exact admission rule after this result

**Native-local nine NMI brackets: positive, bounded. Original/native equivalent NMI phase and first actually consumed differing byte: still missing.** The 75 mixed physical lines are separately negative evidence about source log transport, not a gameplay fault by themselves. Original-side *actual fetched opcode and NMI-wake* markers were **not present** in this case, even though original post-getter returns were recorded. Reusing older original RF072 readings or translating frame labels from RF054/RF062 is prohibited.

For the **next smallest discriminating case**, pair actual original opcode fetch + NMI-pending/entry semantics against native source-local ordinals at the *same new executable/input epoch*. Preserve unmasked raw stack memory and record first read/overwrite on both sides. Only then can independent QA test whether the 92 nonzero bytes affect guest logic; separately qualify continuous unsampled frames, result/progression, source-earned persistence and exact Windows PE disk restart before promoting any event.

**Verdict: HOLD, 0/45 USA, 0/12 Windows.**
