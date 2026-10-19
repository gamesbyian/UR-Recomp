# QA01 case artifact upload-root compatibility (19 October 2026)

**Scope: transport only.** The completed RF062 same-binary ON/OFF [genuine run 39315208102](https://github.com/gamesbyian/UR-Recomp/actions/runs/39315208102) built the exact original/core and native executable, ran the original/native Zoom Zoo case, and uploaded the complete per-case evidence as Actions artifact **12219402017**. That case archive contains *both* `qa01-case/` (primary data) and `qa01-rf062-ab/` (additional ON/OFF inputs and logs). Actions preserves the common ancestor, so the primary receipt becomes `qa01-case/case-result.json` instead of `case-result.json`. The aggregate job looked only for the flat member and incorrectly recorded `missing_evidence`, then failed. The **actual case job succeeded**. This is not a game result and cannot promote a USA event or excuse independent acceptance.

To prevent future evidence loss, `tools/qa01_event_campaign.py` provides **one shared, fail-closed** `exact_case_artifact_root` helper. It accepts exactly one of two layouts beneath the downloaded `qa01-campaign-case-<id>/` directory:

1. Existing original flat layout `case-result.json`, `producer-report.json`, `SHA256SUMS`, `work/` ...
2. Legitimate multiple-root layout `qa01-case/case-result.json`, `qa01-case/producer-report.json`, `qa01-case/SHA256SUMS`, `qa01-case/work/` ... with separate `qa01-rf062-ab/` evidence.

It **rejects ambiguous mixed flat+nested receipts, symlinked primary roots, missing per-case files, unexpected cases, mismatched plan/source SHA or any contradictory producer report**, and keeps zero release admissions. The independent primary-artifact auditor now resolves the *same* exact evidence root before recomputing source/ROM/movie/controller/core checksum and classification. Neither path exists as an alternative original movie or gameplay clock; no data are changed or rebased.

ROM-free adversarial tests validate a nested genuine-shaped case, primary producer re-hashing and immutable original/controller routing, and dual-root rejection. There is no new CI dispatch, source/native emulator instrumentation, pacing, memory mask, input shift, Windows product change or event credit. **QA01 accepted complete USA events remains 0/45.**

The full authentic RF062 ON/OFF result is independently preserved in [PR #1965](https://github.com/gamesbyian/UR-Recomp/pull/1965) and [the immutable case reference](../analysis/data/qa01-rf062-same-executable-on-off-20261019.json) once that evidence-consumer PR is qualified. The aggregate transport correction does not retroactively turn the historical failed Actions summary green; it enables independent reproduction of the genuine case from the already downloaded artifact without rerunning emulators.
