# Windows beta v2 | day-to-day interval report

**Reviewed upstream source through `c00997af128912297e5cf8bffac54ee0b9f12484` (2026-10-24 18:50 UTC).** This report compares the **previous 47% checkpoint** after merged #2513 at `ff739ca5e1b363ada4db611053f9a06399e571db` with the subsequent four merges, rather than subtracting from the separate historical 50% initial v2 baseline.

| Metric | Prior reviewed source | New reviewed source | Delta |
| --- | ---: | ---: | ---: |
| Provisional Windows product coverage | **47.000%** | **47.000%** | **0.000 pp** |
| Independently audited v2 criteria | 0% | 0% | 0 |
| Complete USA source events | 0/45 | 0/45 | 0 |
| Formal Windows release QA gates | 0/12 | 0/12 | 0 |
| Merged commits in review interval | — | **4** | 2 direct UI + 2 release-risk |

The four observed merges are [#2508](https://github.com/gamesbyian/UR-Recomp/pull/2508), [#2514](https://github.com/gamesbyian/UR-Recomp/pull/2514), [#2515](https://github.com/gamesbyian/UR-Recomp/pull/2515), and [#2510](https://github.com/gamesbyian/UR-Recomp/pull/2510). Their actual contribution is recorded in [the interval manifest](v2-review-interval-20261024T1850.json) and preserved even though none closes the entire wording of a currently unverified v2 requirement. In particular, #2510's VHD cleanup test does *not* retroactively turn the previously failed physical NTFS run green.

## Reproduce

At the repository root:

```sh
python3 tools/progress_interval_v2.py --reviewed-head c00997af128912297e5cf8bffac54ee0b9f12484 --format markdown
python3 tools/progress_interval_v2.py --reviewed-head c00997af128912297e5cf8bffac54ee0b9f12484 --format json
python3 -m unittest discover -s tests -p 'test_progress_interval_v2.py'
```

For the **next progress report**, record another immutable review checkpoint that snapshots all 135 criterion `status` and `audit_state` values plus official QA counts, and provide an interval manifest with **every new main merge** from the prior checkpoint, the source-pinned latest HEAD and exact criterion transitions with evidence. Supply its paths using `--previous` and `--interval`. The report rejects stale HEAD references, missing merge proofs, changed scoring without an explicit transition, duplicate PR IDs, and unsubstantiated gate/event changes.

This helper validates the source receipts *provided* to it; it **cannot prove** that an external GitHub commit was genuinely merged, that the review included every merge, or that a PR's behavior was actually independently exercised. The reviewer must verify exact GitHub main ancestry, execution receipts and source/PR scope. It is not an autonomous certification mechanism.

## Metric semantics

The initial, immutable v2 **50%** and current **47%** represent the net effect of the October 24 negative evidence audit (−4) and real stock Practice rematch closure (+1). The present interval's **0 pp** is not zero engineering work. It means four narrower merged fixes did not finish any additional *currently unmet, frozen* requirement. Avoid granting fractional points based on commit counts. Release gates and USA admissions retain their sole respective authorities.

The remaining highest-impact work is independent full USA event admission, integrated physical Windows candidate and real-player journeys; see [issue #2491](https://github.com/gamesbyian/UR-Recomp/issues/2491).
