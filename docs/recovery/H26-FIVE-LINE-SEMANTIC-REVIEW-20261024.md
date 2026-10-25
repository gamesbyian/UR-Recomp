# Original H26 five-line research: source-to-main dispositions

**Boundary:** This is a scoped audit of the **five top-level candidate JSONs** in the first-party H26 recovery ZIP, Drive `142bXAi_4D-928Wz7FntyRbVzTYvt_sJZ` (SHA-256 `601d6131f90b427f29c53d0cee5be69cb4bacde467fda45e45b8144d5b18be00`). **It does not close its nested 177 source-like occurrences or independently certify all H26 ZIP members.** Exact candidate/member SHA-256s, current path/blob and owner appear in [the deterministic register](H26-FIVE-LINE-SEMANTIC-REGISTER-20261024.json).

The original archive was independently downloaded from authenticated Drive, full SHA verified, 33 outer ZIP entries read with CRC success. Its test suite was safely extracted without path traversal or permission changes and rerun: **9/9 normal, 9/9 Python `-OO`**. These tests use archived source and synthetic data, not a fresh Windows native program or game ROM.

| H26 line | Source comparison | Disposition | Who owns anything further |
| --- | --- | --- | --- |
| QA01: sparse transition priority | `tools/qa01_opposite_state_probe_priority.py` has the same bounded 4→8 probe frame 5 and 16→32 onset probe frame 17, refusing monotonic first-divergence promotion | **Semantically superseded** | Existing CPU original/native phase evidence, no new H26 PR |
| QA08: chromatic candidate | `tools/qa08_probe_robustness.py` evaluates the 12 permutation/brightness hypotheses, selects `6b16` and explicitly documents ±1 measurement ambiguity | **Semantically superseded** | Existing held QA08 #1996 |
| QA06: source-free 1px shift | `tests/unit/test_qa06_original_block_consistency.py` demonstrates that a 1-source-pixel-shifted 512×448 screenshot still passes block consistency | **Semantically superseded** | Independent genuine source-frame pixel oracle / art review |
| Knowledge: transitive H25 nested ZIP | H26 independently verified 23/57/29 declared members and proved one nested Agent3 ZIP identical to standalone Agent3. No proof of independently reproduced three-manifest code on main is claimed | **Historical provenance / dedupe evidence** | Agent 1 retains; Agent 3 intake consumer only if new gap |
| Records exporter: final check → publish | Recovered synthetic fixture changes the underlying source after final reread, just before no-replace publish. Current main explicitly admits this race in its source comment; #2483 complete namespace reread and #2486 cross-process no-replace do not freeze source generation | **Distinct conditional release-integrity discriminator, not confirmed shipping defect** | Agent 2 current-main reproduction / producer freeze or immutable snapshot; Agent 3 and independent NTFS QA |

## Narrow Windows/Records discriminator

On currently inspected `main`, `tools/export_baldosa_earned_1p_run.py` rereads `report.json` and the source-earned `.urrun` after staging, checks the complete portable namespace, then calls `_publish_directory_no_replace(staging, destination)`. Its own comment correctly acknowledges that rechecking **narrows but cannot eliminate** writes by another process after that check. The H26 test demonstrates the missing implication under a synthetic change injected inside precisely this window: a published artifact may be internally consistent with the earlier source while no longer matching the live source generation.

This is different from (a) no-replace **destination** collisions, (b) final **namespace** contents, (c) per-file mutation during reads, or (d) a physical Windows/NTFS test. Before declaring a real engineering bug, Agent 2 must establish whether a producer-freeze, process-lifecycle or generation-identity contract already excludes such writes, and then reproduce a current-main negative independently. If it remains relevant, derive a fresh solution with an immutable source snapshot or stable producer generation plus an adversarial regression. No replay of older safety-denied source writes, no unfounded Windows exploit claim.

## Accounting and stopping rules

Three source candidates are semantically covered; one is preservation/provenance only; **one remains an actionable qualification question**, not an authorized source candidate. The entire recovered H26 archive remains preserved. Counts here are **five historical candidate manifests**, not five new open implementation PRs, not five missing files, and not five accepted gameplay events. Physical Windows gates, QA08 raster identity, UHD art and P2P WAN acceptance retain separate independent owners and evidence.

The 37 existing vm1 member decisions are unchanged by this audit; the original H26 direct-child Drive ID is already in the 224-item six-folder register. This report adds scoped child candidate meaning without double counting either denominator.
