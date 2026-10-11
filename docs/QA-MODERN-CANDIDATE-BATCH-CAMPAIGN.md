# Manual Modern candidate batch: one Linux build, multiple suites

Status: **manual component campaign**, not an independent QA release pass. Execution entrypoint: **Modern native heavy router** in GitHub Actions, **Run workflow**. This also retains the existing narrowly scoped pull-request router unchanged in purpose.

## Decision and execution budget

Use when a reviewer needs one complete snapshot of the already-established **legacy SNESRecomp Modern host** from an exact ref, rather than rerunning individual native suites after incremental PRs. Its existing native router generates and uploads the canonical Linux candidate once and reuses it across three established `workflow_call` suites, with their existing internal fan-outs:

- `modern-shared-native-acceptance.yml`: Records/ghost/profile/result/ordinary 2P and related native routes.
- `modern-onboarding-practice-acceptance.yml`: practice, onboarding and tour user-facing routes.
- `native-ui-evidence.yml`: reusable UI capture and inspection routes.
- Optional `windows-native-smoke.yml`: **separate** Win32/ClangCL toolchain, checked portable ZIP, real Win32 scripted smoke. It cannot share a Linux executable and is explicitly represented as another build.

There is no new automatic trigger, runner matrix, cloned evaluator, independent suite-specific compile, or unbounded overnight loop. Running the manual campaign on a ref does not alter PR-change classification. Manual long runs are not cancelled on new dispatches; pull-request supersession may still cancel its own previous run. Observe account-level Actions queue limits before launching multiple campaigns.

## Procedure

1. Select a ref containing this integration and dispatch **Modern native heavy router**, optionally disabling `include_windows` if only Linux diagnostics are needed. Prefer a nominated, integrated commit over a moving development branch.
2. Read the final `campaign-report` Job Summary, then download the 14-day `modern-campaign-report` JSON. It binds source SHA, run ID, each named callee outcome, the **single canonical Linux tarball SHA-256** and (when requested and completed) the exact **Windows portable inner ZIP SHA-256** verified against the repository checksum parser.
3. If a suite fails or is cancelled/skipped unexpectedly, the receipt says `suite_failure` or `incomplete`. A missing, mismatched or malformed identity is `evidence_invalid` and the report job fails while retaining the machine receipt. Read the corresponding suite artifact/log only for the named failure. A green aggregate alone is never the release gate.
4. Promote reproducible regressions to their owning implementation/QA agents with the exact ref/run/metric. Do not copy artifacts to `main`, count unfinished cases, or update `docs/RELEASE-QUALITY-LEDGER.json` without independently satisfying its owning gate.

`component_suites_passed` means these existing *legacy-backend component routes* completed. It never means Baldosa Modern has passed, a complete original/native event matches, an authentic physical 2P player journey has passed, a clean hardware/4K/audio path has passed, or that a Windows release is ready. The separate QA-01 original/native event campaign remains the source-qualified event research route.

## Maintenance/retirement contract

`tools/qa_modern_batch_campaign.py` provides the typed manifest and fail-closed classification. The Windows checksum proof calls the existing `assemble_windows_package.verify_archive_checksum`; no parallel format parsing is introduced. Regression coverage lives in `tests/unit/test_qa_modern_batch_campaign.py` and `tests/unit/test_ci_trigger_policy.py`.

Run the narrow tests locally before editing this batch:

```bash
python3 -m unittest discover -s tests/unit -p test_qa_modern_batch_campaign.py
python3 -m unittest discover -s tests/unit -p test_classify_modern_native_ci.py
python3 -m unittest discover -s tests/unit -p test_ci_trigger_policy.py
```

Retire the manual mode once the single pinned Baldosa Modern Windows candidate supersedes the legacy component route. Never silently re-label these reports as Baldosa acceptance. A later real Baldosa campaign should share that candidate and independent QA authority, not copy this entire legacy workflow.
