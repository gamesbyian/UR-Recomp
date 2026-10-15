# Independent real Win32 Modern Options and Practice source audit (2026-10-15)

**Scope:** bounded read-only independent release QA of two original, unmodified, successfully completed **Windows-native** workflow dispatches on distinct PR revisions of Modern #1648. This is positive **functional** evidence, not a merged-main release-candidate nomination, strict original/native complete-event result, physical device acceptance, save/disk-fault durability claim or public prerelease.

## The two same-run, mutually consistent source and package receipts

| Provenance | Earlier Windows run | Later Windows run |
| --- | --- | --- |
| Real workflow | [38701860728](https://github.com/gamesbyian/UR-Recomp/actions/runs/38701860728) | [38703695304](https://github.com/gamesbyian/UR-Recomp/actions/runs/38703695304) |
| Exact head/source | `43d813b4988357ff4839cf600442d341d1efb4cc` | `ac822712ec4eacec7085185562f20aa6987b6e7f` |
| Fixed Options/Practice 17-member Actions artifact ID | `11956823094` | `11958820226` |
| Full evidence-wrapper SHA256 | `75c4f0315df29f603129c65029f531fd65355abdd5c0983561eb914cf28ccac8` | `a95b32fdb6d020f8d1e99d210b9631138d3bcf4d1b6786bdda84216246fbf346` |
| Candidate wrapper ID | `11957476804` | `11957947995` |
| Candidate inner ROM-free ZIP SHA256 | `a2e733498d67318d8d847343d3328ec1ff55e4e03a8c5e37f75e6a6f2141f962` | `80b00c5965b1324fdab9bfd20d52e881ac5ece2305df66c3bacc366a6614f5aa` |
| Windows PE32+ EXE SHA256 | `fd3ebba5f1e75820a98d4e78114378dc6ba20785ab9c58ad4c550904c5ef3c4d` | `a90026ac3d438c6a4bfae3cd6360b433867e50589282efbf1bfe8a585daedd0f` |
| Candidate binding artifact ID | `11956947730` | `11957808156` |

The precise outer ZIP and binding-wrapper hashes, all 15 full per-log event hashes and negative claims are in [the structured evidence receipt](../analysis/evidence/qa-win32-modern-options-practice-two-real-runs-20261015.json). The release-quality ledger remains authoritative. Neither run is an exact integrated `main` build or the latest Modern PR head, and a **green PR/branch build** cannot be substituted for the exact packaged user-facing Windows candidate.

## Independently observed original Windows process chain

The archived evidence contains exactly 17 files per run: two producer reports and **fifteen real native Windows process logs**. Actual archive bytes, externally sourced Actions wrapper digest, Windows PR head, in-report source+EXE identity, separate candidate ZIP and source/executable binding receipts were verified against one another; the immutable candidate ZIP has four ROM-free files including the actual PE32+ game executable.

The Options process sequence independently exhibits:
1. Fresh boot: `WINDOWED`, `VSYNC=ON`, volume 100; controller-semantic root input changes Display to `BORDERLESS`, VSync to `ADAPTIVE`, volume to 90 and exits the Controls help.
2. A **fresh native process** boots with those restored values, selects Defaults and reports `WINDOWED/ON/100`. The separate Options file digest changes from the previous stage.
3. A fresh process loads Defaults without changing the Options file digest.
4. A deliberately damaged Options file is reported, quarantined under `.damaged` on the explicit new change, and rebuilt. Its bounded manifest records 34 original invalid bytes, although **the actual raw settings bytes are not archived**, so this remains a producer byte receipt plus independent source log, not raw-file QA approval.
5. A read-only `config.ini` on the real Windows runner is **enforced**, so an attempted volume reduction remains at 100 with `NOT APPLIED`, **not `SAVED`**.

The Practice chain independently exhibits **ten** separate native processes with exact source-order `practice_opened`→requested course→`practice_entered` (correct original `course+1`)→SRAM sandbox restoration. The tested sample spans Dragster, Bowl, Jumps, Short Cut, East, Wobble, Last One, Down+Up, Vertical and 123 Jump. It tests five of the initial 20 and five of the tier-2 40 available courses, **not all 20 or 40 entered on Win32**. The original game course identity is decoded in the source log. Every case uses semantic controller edges but reports **zero detected physical gamepads** and dummy audio. Practice sandbox and no-earned-result are source-reported and the producer checks saves internally; no independent pre/post 8 KiB files were retained in this artifact.

## Cross-run repeatability and cost

For each of the **15 exact matching process paths**, select in original order every log line containing `UR_BALDOSA_` or beginning `script f=`; compute SHA256 over UTF-8 lines separated by LF and ending LF. This yields **1,358 original source/gameplay events in each independently built Win32 run, identical per-log hashes on all 15 paths**, despite different source revisions and executable SHA256. This requires no new CI job or research factory. The claim is **event-sequence repeatability**, not executable byte-for-byte reproducibility or graphical/pixel/source-original parity.

### Minimal manual independent reproduction

Download the three original artifacts (fixed-source archive, candidate ZIP+sidecar, binding JSON) from **the same** successful workflow run. Compute their original Actions wrapper SHA256 independently; verify against the structured receipt. Use a ZIP reader to require exactly the 17 fixed archive filenames, reject duplicate/extra members, compare source and EXE identities in **both** reports against the packaged executable SHA256 and the separate binding JSON, require no ROM or mutable saves in the candidate and inspect the source events rather than trusting the producer's `true` flags. A minimal cross-run event-hash check is:

```python
import hashlib, json, zipfile
from pathlib import Path

receipt = json.loads(Path("analysis/evidence/qa-win32-modern-options-practice-two-real-runs-20261015.json").read_text())
for run_id, artifact_path in [(38701860728, "earlier-actions.zip"), (38703695304, "later-actions.zip")]:
    actual = next(r for r in receipt["runs"] if r["workflow_run_id"] == run_id)
    raw = Path(artifact_path).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == actual["options_practice_artifact"]["sha256"]
    with zipfile.ZipFile(artifact_path) as z:
        assert set(z.namelist()) == {e["name"] for e in receipt["events"]} | {
            "native_options/report.json", "native_practice_courses/report.json"}
        for entry in receipt["events"]:
            text = z.read(entry["name"]).decode("utf-8")
            events = [line for line in text.splitlines()
                      if "UR_BALDOSA_" in line or line.startswith("script f=")]
            assert len(events) == entry["events"]
            assert hashlib.sha256(("\n".join(events) + "\n").encode()).hexdigest() == entry["sha256"]
```

This snippet checks original downloads and event reproducibility; it is **not sufficient by itself** for native chronology, binary provenance or physical-durability acceptance. The fuller independent offline consumer additionally checked fixed population, per-case source order, all 15 native starts, exact native menu entry and same-run bound EXE+ZIP metadata and rejected malformed/tampered imports.

## Negative boundaries and decision

- **QA-09/10:** real native Options/Practice UI functionality has substantially improved, but unverified physical pads, proper audible volume, monitor/window transitions, 4K and display output remain. The source report alone cannot prove actual OS fullscreen change on a real player's monitor.
- **QA-02:** settings digests, name-preserving quarantine and ordinary source sandbox restoration are useful controls, **not** independent raw-file crash/cold-process OS save recovery. Genuine disk-full, power loss and cross-process CAS recovery remain open.
- **QA-01/07:** no fully complete scored original/native USA event has been independently compared by this campaign; strict 0/45 stays intact.
- **Release:** 0/12 accepted release-quality gates; nominated `candidate.commit_sha` and `candidate.zip_sha256` remain `null`. No prerelease publication.

**Next cheapest action:** Agent 3 should finish the existing #1648 lane and have Agent 6 reconcile it only with exact-head source/Windows checks. Once integrated, initiate the already-existing manual `Manual ROM-free Windows technical playtest` on the **then-current merged main** in `verify_only` mode, and independently verify the exported four-file owner artifact using merged [#1644's consumer](../tools/check_baldosa_owner_playtest_download_qa.py). Do **not** run `publish_provisional_preview` without explicit owner approval. Retain future physical player screenshots/observations against that exact ZIP SHA, not a prior PR ZIP.