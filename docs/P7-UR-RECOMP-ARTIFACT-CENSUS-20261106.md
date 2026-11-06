# P7: complete UR-Recomp Actions artifact metadata census (November 6, 2026)

**Scope:** An actual, full, **read-only** GitHub Actions artifact metadata census of `gamesbyian/UR-Recomp`, completed with the owner's pre-existing authenticated GitHub CLI. This is a separate missing-repository follow-up to [storage issue #3048](https://github.com/gamesbyian/UR-Recomp/issues/3048) under the [November 4 infrastructure plan](CI-COLLECTIVE-QUALIFICATION-INFRASTRUCTURE-PLAN-20261104.md). It does **not** download 6,626 ZIP payloads, authenticate their contents, delete any files, exercise Windows gameplay or establish GitHub billing charges.

## Source and collection integrity

At exploratory inspection the API listed **6,628** artifacts. The listing then changed to **6,626** before the actual complete census started; no mixed-count dataset was accepted. API calls requesting 100 items intermittently failed with `unexpected end of JSON input` (not a proven authorization denial). Smaller **25-item pages** succeeded.

The complete read-only census finished at **2026-11-06T21:41:44.976227Z** after **100.1 seconds**, with **266 complete GitHub REST pages** (25 artifacts/page), four concurrent read-only workers, at most three bounded retries per page, and an independent post-read of page 1. All pages reported the same count, exactly **6,626 unique IDs** were enumerated, the first-page IDs and total were stable across the final readback, and no duplicated/invalid size rows were found. The qualified snapshot is from that **single observation**, not a claim that its object population stays fixed thereafter.

The complete raw **2,388,699-byte** metadata-only JSON report was subsequently preserved without overwrite in the owner's established HP qualification-evidence folder as `P7-NONRELEASE-UR-ARTIFACT-METADATA-20261106T214144Z.json`, exact SHA-256 `d1885356dc060534f5084a97d83faf726320e99f1cfe7643d1ab5fd651bc045a`. The source `%TEMP%\\ur-recomp-p7-census-20261106.json` was independently rechecked for unique IDs and identical bytes. The saved report is an actual artifact-metadata review packet, **not** a verified ZIP archive, credential dump, release artifact or deletion authorization.

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

The repository already owns the read-only [artifact census CLI](../tools/actions_storage_inventory.py) and [account census workflow](../.github/workflows/actions-artifact-census.yml), which had previously completed 16/17 repositories but could not reliably list UR-Recomp. An **unmerged, reviewable** [PR #3218](https://github.com/gamesbyian/UR-Recomp/pull/3218) proposes validated `--page-size 25|50|100`, `--recheck-first-page`, and bounded parallel `--workers 4` **only for UR-Recomp**. Its source retains serial 100-row pages for the other repositories. **Do not describe these proposed changes as installed on main.** If GitHub returns an explicitly recognized transient truncated-JSON CLI error, bounded retries can try again, but no error ever counts as a successful page. Duplicate IDs, missing pages, changed counts and first-page drift still fail closed.

**First exact-head hosted census finding (November 6):** [Run #42299643994](https://github.com/gamesbyian/UR-Recomp/actions/runs/42299643994) **completed its workflow**, but its protected index explicitly reported **16 of 17 repositories** and **`account_wide_complete=false`**. UR-Recomp was excluded after a scoped read failure; the old workflow's limited redacted error vocabulary reported only **`unclassified`**. Neither its completed workflow status nor the 16-repo byte sum proves that the updated UR scanner succeeded. A follow-up narrows the operational gap by recognizing additional *fixed, credential-free* parser/inventory drift error categories (`first page changed`, `incomplete inventory`, `invalid JSON`, and duplication); the raw error is still not displayed. The next exact-head hosted attempt classified the failure; the results are recorded below.

**Second hosted discriminator (Nov 6):** [Run #42300346994](https://github.com/gamesbyian/UR-Recomp/actions/runs/42300346994) completed **16/17** and specifically reported **`artifact count changed during pagination`** for UR. This was an honest rejection of an offset-page race, not a security denial or an inaccurate 17/17 success. The owner's successful manual UR scan had used four concurrent page readers; the original hosted utility was strictly sequential, widening the race window. The same existing tool now proposes **bounded `--workers 4` only for UR**, preserving a default of one for all other repositories. It prefetches only the exact initial count's page bounds (including an empty final page for exact multiples), validates every page and ID against the original total, and re-reads the first page after completion. Synthetic controls reject changing totals, duplicate IDs, truncated/missing final pages and invalid worker counts. The independent real parallel-hosted attempt is recorded below; its result must be read separately.

**Third hosted four-worker attempt (Nov 6):** [Run #42301134055](https://github.com/gamesbyian/UR-Recomp/actions/runs/42301134055) at unchanged proposed source `aa04bf97029fff44116d9b7e8ff0bad14c9b229a` passed the workflow job but again correctly reported **16/17**, UR excluded because **`artifact count changed during pagination`**. The full [four-shard exact-head tooling #42301133844](https://github.com/gamesbyian/UR-Recomp/actions/runs/42301133844) passed (**7,399 discovered, 150 skips, no failed shards**), and [hygiene #42301133866](https://github.com/gamesbyian/UR-Recomp/actions/runs/42301133866) passed. Together the three hosted attempts demonstrate *honest instability detection*, **not** source-accepted simultaneous 17/17 coverage. This is a stop condition: no further repeated full-account scans merely to obtain a green completeness badge, no unreviewed relaxation of counts/IDs, and no new service. The code remains in an **unmerged PR awaiting independent review of whether the extra complexity is justified**.

**Status separation:** The completed 266-page audit above is the manual live evidence; it does **not** pre-authorize code from this PR to run on the owner's HP or establish that the patched hosted workflow has passed. The proposed code has full exact-head tooling and hygiene passes but has **not** demonstrated stable account-wide coverage in any of its three actual hosted census runs. Another ordinary CI "success" cannot confer complete-source status when the index says `account_wide_complete=false`. A concurrent artifact deletion/upload may legitimately invalidate that census, in which case report incomplete rather than guessing.

The older 16-repository snapshot recorded **96,663,401,636 compressed bytes (~90.02 GiB)** around November 2. It is **not contemporaneous** with this November 6 3.044-GiB UR snapshot; adding them would fabricate a current account total or billable GB-hours. Artifacts, cache usage, public-repo billing and acquired test outcomes are different quantities.

**Decision:** no archive deletion or privileged cleanup workflow. Natural expiry already covers **3,771** objects inside seven days. Source-bound quality, QA01 original/native witness and owner-visible GLB/playtest history outrank a small potential storage decrease. If future measured pressure warrants change, select **one** specific upload family, identify its workflow/run/source/consumer/release dependencies and verify a new short-retention candidate before proposing any irreversible deletion. No new scheduler, agent, runner, P1 authorization or P4 task-prompt change follows.
