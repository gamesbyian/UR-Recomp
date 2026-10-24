# Initial atomic Windows-beta v2 evidence-screening review

**Reviewed:** October 24, 2026, against repository `main` at `7f8f882820feb6d2b9d46b16f5e90e46dd0544f3`. This is a PR-description, original project QA and cited-witness assessment of the **initial 50 provisional claims**, not a new independent Windows package run, physical QA session or original/native course admission. Machine-readable [all 50 criterion decisions](v2-screening-audit-20261024.json) preserve the prior receipt and current verdict.

| Measure | Initial v2 frozen screening | After evidence review | Net change |
|---|---:|---:|---:|
| Provisional bounded product checks | 50/90 | 46/90 | **−4** |
| Provisional v2 coverage (incl. 45 USA event slots) | 50.000% | **46.000%** | **−4.000 pp** |
| Independently audited criterion points | 0.000% | 0.000% | 0 |
| Original/native complete USA events | 0/45 | 0/45 | 0 |
| Official Windows QA release gates | 0/12 | 0/12 | 0 |

The historical subjective 60% and historical v1 maturity 48.5% are **different metrics**, neither a prior v2 score nor an assertion of QA readiness. No scope or weight was changed.

## Withdrawn claims (no silent rewording of frozen criteria)

- **MENU-01 (−1 point):** Criterion requires a **physical controller** traversing five Modern destinations. Its cited [#1648](https://github.com/gamesbyian/UR-Recomp/pull/1648) explicitly excludes physical-pad testing; Linux/Xvfb and synthetic input cannot satisfy the frozen wording. Reopen only with same-source real-pad navigation evidence for all destinations.
- **UX-04 (−1 point):** Criterion requires **two real players** to create/identify distinct profiles. [#1510](https://github.com/gamesbyian/UR-Recomp/pull/1510) proves separate identities and real native Win32 processes driven by scripted controller semantics, **not two humans**. Require witnessed human 2P onboarding; retain TWO-01/TWO-02's narrower script-backed product evidence.
- **DATA-05 (−1 point):** Criterion says native file paths preserve **Windows Unicode names**. [#2405](https://github.com/gamesbyian/UR-Recomp/pull/2405) explicitly reports only Linux UTF-8 fixtures and source assertions; a real Windows runtime/NTFS exercise was pending. Source implementation is valuable, but the narrower Linux proof cannot close this Windows-specific requirement. Do not confuse with distinct Windows-2022 UTF-8 *tournament coordinator* proof [#2450](https://github.com/gamesbyian/UR-Recomp/pull/2450), which remains credited as DATA-06.
- **TWO-05 (−1 point):** The criterion promises keyboard+pad **product admission rejects seat churn**. [#2455](https://github.com/gamesbyian/UR-Recomp/pull/2455) changed the QA runner's **negative evidence classifier only**, without altering or proving production input admission. A stricter test is valuable risk reduction but cannot earn product-completion credit by itself. Reopen upon an actual native host product witness of correct seat ownership through stock GO.

No unverified item was promoted merely to offset these withdrawals.

## Evidence re-linked (no score inflation)

- **WIN-01, WIN-02:** Added direct [hosted Windows integrated build/boot receipt #39822833034](https://github.com/gamesbyian/UR-Recomp/actions/runs/39822833034) to the [#1648](https://github.com/gamesbyian/UR-Recomp/pull/1648) code evidence. This supports bounded host/packaging claims but never clean-machine/physical release acceptance.
- **WIDE-01:** Replaced unrelated Modern Options/Practice PR pointer with actual source-world [#1082](https://github.com/gamesbyian/UR-Recomp/pull/1082), compositor [#1092](https://github.com/gamesbyian/UR-Recomp/pull/1092), and [342×224 moving native PPU receipt #38004162535](https://github.com/gamesbyian/UR-Recomp/actions/runs/38004162535). There is genuine widened tile material, not stretch, but no approved HD racers or complete original parity.
- **WIDE-02:** Switched to independent [#1210](https://github.com/gamesbyian/UR-Recomp/pull/1210), [native PPU fixed/342 centre witness #38083079741](https://github.com/gamesbyian/UR-Recomp/actions/runs/38083079741), reporting 0/57,344 source-centre pixel differences in both split bands. That is a bounded Original-mode parity observation, not a release-wide visual approval.

The other **42 screened claims** retain their prior PR-linked classification **without new independent acceptance credit**. They still warrant separate code/path and exact-source testing. In particular, simulated GPU-reset handling, source-only menu layout, Linux input/UTF-8 fixtures, and snapshot/profile guards must not be described as independently verified real-device behavior.

## Work effectiveness decision

The first outcome audit's 57 commits were classified by *intent*: 11 directly product-related, 19 release-risk, 20 enabling, 7 other/deferred. This review identified a concrete case (#2455) of **useful QA tooling mistakenly counted as completed player-product behavior**. The right response is to maintain separate product-closure vs risk-reduction accounting and attach a specific outcome/dependency to further tooling work. It is not defensible to label the remaining 20 enabling commits wasted without effort and downstream evidence.

## Process for subsequent updates

Maintain the original [50-point v2 snapshot](windows-beta-v2-baseline.json) unchanged. Run:

```sh
python3 tools/atomic_progress_v2.py --format markdown
python3 tools/atomic_progress_delta.py --format markdown
python3 tools/progress_yield_audit.py --format markdown
```

When reviewing a new source, supply `--reviewed-head` with an explicitly reviewed 40-character upstream SHA; a stale inventory must fail closed. Add new source-bound acceptance receipts only when the *criterion wording*, not a nearby improvement, is actually satisfied. A newly proved Windows beta criterion gains 1.0 point; a newly independently accepted and uniquely identified USA event adds 0.222 point. Record retractions as negative deltas. Acceptance authorities remain the official QA ledger and course-event census.

**Follow-up:** [#2491](https://github.com/gamesbyian/UR-Recomp/issues/2491) retains independent re-execution and review of the remaining 46 screening claims and the four withdrawn requirements. This documentary screening pass does not close that issue.
