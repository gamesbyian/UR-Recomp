# P7: complete UR-Recomp Actions artifact metadata census (November 6, 2026)

**Scope:** An actual, full, **read-only** GitHub Actions artifact metadata census of `gamesbyian/UR-Recomp`, completed with the owner's pre-existing authenticated GitHub CLI. This is a separate missing-repository follow-up to [storage issue #3048](https://github.com/gamesbyian/UR-Recomp/issues/3048) under the [November 4 infrastructure plan](CI-COLLECTIVE-QUALIFICATION-INFRASTRUCTURE-PLAN-20261104.md). It does **not** download 6,626 ZIP payloads, authenticate their contents, delete any files, exercise Windows gameplay or establish GitHub billing charges.

## Source and collection integrity

At exploratory inspection the API listed **6,628** artifacts. The listing then changed to **6,626** before the actual complete census started; no mixed-count dataset was accepted. API calls requesting 100 items intermittently failed with `unexpected end of JSON input` (not a proven authorization denial). Smaller **25-item pages** succeeded.

The complete read-only census finished at **2026-11-06T21:41:44.976227Z** after **100.1 seconds**, with **266 complete GitHub REST pages** (25 artifacts/page), four concurrent read-only workers, at most three bounded retries per page, and an independent post-read of page 1. All pages reported the same count, exactly **6,626 unique IDs** were enumerated, the first-page IDs and total were stable across the final readback, and no duplicated/invalid size rows were found. The qualified snapshot is from that **single observation**, not a claim that its object population stays fixed thereafter.

A detailed JSON report is present under the owner's HP `%TEMP%\\ur-recomp-p7-census-20261106.json`. It is temporary analysis data, not a committed source-identity manifest, a verified ZIP archive or a proposed deletion manifest.

| Actual snapshot dimension | Value |
| --- | ---: |
| Listed artifacts, with complete enumeration | **6,626** |
| Current compressed metadata bytes | **3,268,726,171** |
| Equivalent binary GiB | **3.044** |
| Distinct artifact name families | **286** |
| GitHub-reported artifact digests present | **6,626/6,626** |
| Workflow run IDs present | **6,626/6,626** |
| Already expired in the snapshot | **0** |
| Scheduled to expire within seven days | **3,771** |
| Scheduled to expire after seven days | **2,855** |

**Recorded ages at collection:**

| Age of artifact | Count | Compressed bytes |
| --- | ---: | ---: |
| Under 7 days | 2,080 | 1,925,945,564 |
| 7–14 days | 2,979 | 280,195,349 |
| 14–30 days | 656 | 1,015,142,279 |
| 30–90 days | 911 | 47,442,979 |

## Preservation-aware cost ranking

The largest named families are *review categories*, not deletable datasets. Distinct uploaded artifacts may differ in source, run, provenance, purpose, or actual bytes despite sharing a name.

| Family | Count | Approx. GiB | Review posture |
| --- | ---: | ---: | --- |
| `windows-native-smoke` | 237 | 0.554 | Examine producer and exact-source Windows acceptance dependencies |
| `ur-atlas-mobile-browser-smoke` | 166 | 0.397 | Protect visual source and reviewer-facing evidence until consumer audit |
| `ur-experimental-model-review-actual-glbs` | 118 | 0.265 | Preserve unique actual racer GLBs, particularly owner art comparisons |
| `qa01-rf076-immutable-case-independent-raw-verdict` | 31 | 0.239 | **Protect original/native scientific witness** |
| `qa01-rf076-nine-nmi-exact-source-and-independent-verdict` | 25 | 0.210 | **Protect source parity proof** |
| `qa01-dragster-next-zoo-original-native` | 12 | 0.157 | **Protect real QA01 game evidence** |
| `qa01-rf076-original-fetch-source-and-binary-original-bytes` | 17 | 0.153 | **Protect original binary evidence** |
| `ci-tooling-unit-result` | 1,435 | 0.026 | Numerous tiny receipts; a count-only cleanup is low yield |

The largest single item is source-family `ur-graphpaper-recruitment-80s-27s-and-plates` (44,540,376 bytes, artifact **#12250119778**); its size alone does not make it expendable. Also preserve the independently authenticated [physical playtest ZIP](HP-PLAYTEST-ARTIFACT-PRESERVATION-20261106.md) and the exact four [schema-3 P2 Windows archives](CI-COLLECTIVE-P2-TRUSTED-MAIN-FANOUT-PILOT-20261106.md#p7-preservation-of-the-exact-schema-3-artifacts), which have already been separately byte-audited and retained on the HP.

## Follow-through without a second inventory system

The repository already owns the read-only [artifact census CLI](../tools/actions_storage_inventory.py) and [account census workflow](../.github/workflows/actions-artifact-census.yml), which had previously completed 16/17 repositories but could not reliably list UR-Recomp. The accompanying scoped source change adds explicit validated `--page-size 25|50|100` and optional `--recheck-first-page`. The existing workflow uses `--page-size 25 --max-pages 400 --recheck-first-page` **only for UR-Recomp**, leaving the other repositories at their existing 100-item page semantics. If GitHub returns an explicitly recognized transient truncated-JSON CLI error, bounded retries can try again, but no error ever counts as a successful page. Duplicate IDs, missing pages, changed counts and first-page drift still fail closed.

**Status separation:** The completed 266-page audit above is the manual live evidence; it does **not** pre-authorize code from this PR to run on the owner's HP or establish that the patched hosted workflow has passed. Qualify the new code's synthetic tests, full exact-head tooling and hygiene, then observe a real hosted artifact census before claiming the installed automated inventory covers 17/17. A concurrent artifact deletion/upload may legitimately invalidate that census, in which case report incomplete rather than guessing.

The older 16-repository snapshot recorded **96,663,401,636 compressed bytes (~90.02 GiB)** around November 2. It is **not contemporaneous** with this November 6 3.044-GiB UR snapshot; adding them would fabricate a current account total or billable GB-hours. Artifacts, cache usage, public-repo billing and acquired test outcomes are different quantities.

**Decision:** no archive deletion or privileged cleanup workflow. Natural expiry already covers **3,771** objects inside seven days. Source-bound quality, QA01 original/native witness and owner-visible GLB/playtest history outrank a small potential storage decrease. If future measured pressure warrants change, select **one** specific upload family, identify its workflow/run/source/consumer/release dependencies and verify a new short-retention candidate before proposing any irreversible deletion. No new scheduler, agent, runner, P1 authorization or P4 task-prompt change follows.
