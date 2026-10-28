# Windows playable beta v3: release-quality signoff separated

**Status (October 28, 2026): source-reviewed snapshot projection only, not a new beta announcement or independent release decision.**

The owner explicitly separated (a) original-game **semantic fidelity** and playable Windows beta functionality from (b) the three-dissimilar-environment/two-physical-PC and all-gates signoff required for **release quality**. Applicable *individual* physical beta tests remain mandatory. The 45 unique original/native USA events, source-authoritative gameplay, robust storage and art requirements also remain beta requirements under this existing scorecard.

The frozen [135-criterion v2 inventory](windows-beta-v2-inventory.json) contains one non-beta criterion: **QA-09**, which requires independent QA to sign off **every mandatory release gate**. That is a release-quality milestone. The new [versioned beta-v3 scope manifest](windows-beta-v3-scope.json) excludes **QA-09 only**, leaving **134** criteria and **4,455** evidence units. No other QA row is excluded. It derives recorded status, independent audit evidence and event identities directly from the already independently reviewed **v2** source snapshot, and it validates the entire frozen v2 inventory plus the authoritative release ledger **before** scoring any v3 projection.

| Measure | Frozen historical v2 | Playable Windows beta v3 projection |
|---|---:|---:|
| Total criteria | 135 | 134 |
| Denominator (evidence units) | 4,500 | 4,455 |
| Provisionally bounded, as reviewed through `88056d49…` | 2,385 (53.000%) | 2,385 (53.535%) |
| Independently audited, same review | 495 (11.000%) | 495 (11.111%) |
| Accepted complete USA events | 0/45 | 0/45 |
| Formal release quality gates | 0/12 | still tracked independently: 0/12 |

**The 0.535 percentage-point change is entirely a denominator reclassification, not newly built functionality, independent evidence or earned engineering progress.** These percentages **must not be compared as sequential day-over-day performance**. For time-series progress, compare snapshots under the same version and denominator, and distinguish newly engineered features from retroactive evidence admission.

The prior independent TWO-05 hosted Win32 virtual-pad evidence added +1.000pp to frozen v2 (51%→52%). The immutable QA-01 Windows package nomination adds a separate retroactive +1.000pp (52%→53%), with zero new gameplay engineering or physical-release credit. The beta-v3 percentage difference below remains purely the QA-09 denominator reclassification.

The review authority for this projection remains [`current-v2-review.json`](current-v2-review.json), whose recorded source is `88056d491c77cc7bb14ef1635d81892ca0d70305`. Later merged source commits, including these process changes, **are not automatically reviewed product evidence**. To project a later accepted inventory snapshot, update the existing v2 inventory/review pointer through its independent evidence process, then rerun this **read-only** v3 calculator. Never simply stamp today's `main` SHA onto the older evidence.

```sh
python3 tools/atomic_progress_beta_v3.py
python3 tools/atomic_progress_beta_v3.py --format json
# Strict source-epoch check when a specific independently reviewed SHA is known:
python3 tools/atomic_progress_beta_v3.py --reviewed-head 88056d491c77cc7bb14ef1635d81892ca0d70305
```

The calculator fails closed for changes to the original v2's 135 IDs/text/weights, to the 45-event ledger cross-check, to the reviewed source epoch, to the v3 projection fingerprint, to the 134/4,455 denominator, or to the explicit **single QA-09 exclusion**. It never writes an acceptance, reclassifies a physical test or changes a gate. See `tests/unit/test_atomic_progress_beta_v3.py`.

## Beta versus release in practice

A beta tester's real PC may independently qualify the scoped `QA-02` (clean physical Windows boot), `QA-03` (actual P1), `QA-04` *v2 criterion* (actual two-pad race), `QA-05` (audible output), or `WIDE-03/06` (physical display) only when that criterion's actual evidence and independent review requirement are satisfied. Note that frozen **v2 `QA-04`** (physical two-controller race) and official **release-ledger `QA-04`** (three-environment cross-machine qualification) are **different named requirements in separate namespaces**. Do not infer one from the other.

Later release-quality verification retains exactly the separate ledger's full `QA-04` three-environment matrix, final `QA-09` human/independent signoff, and all other remaining release gates. No beta result grants a release gate. Semantic-equivalence exceptions in the USA event census still require full independent causal and adversarial proof, not convenient byte masks.

This projection makes the owners' milestone decision operational without diluting the genuine game or pretending administrative reweighting has accelerated actual development.
