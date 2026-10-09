# Claude branch handoff audit (2026-10-08)

This audit was performed after Claude reached its weekly usage limit. Compare source: live `main`, open pull requests, and all `claude/*` branches. **Branch ahead count is not proof of missing functionality.** Do not merge historical divergent branches merely because their commits are absent from main; apply an individual change only after confirming that the current implementation lacks it.

## Immediate integration disposition

- GitHub reports **one open PR**, [#988](https://github.com/gamesbyian/UR-Recomp/pull/988), a CI Pause-capture optimization owned by the active CI-speed lane. Its PR description requires fresh-head green native capture and tooling gates; **leave to that owner**, do not merge opportunistically.
- Recent tournament QA fixes [#981](https://github.com/gamesbyian/UR-Recomp/pull/981), [#982](https://github.com/gamesbyian/UR-Recomp/pull/982), [#984](https://github.com/gamesbyian/UR-Recomp/pull/984), [#985](https://github.com/gamesbyian/UR-Recomp/pull/985) and build repair [#986](https://github.com/gamesbyian/UR-Recomp/pull/986) are not open. Their current outcomes and residual release gates are already reflected in `WORK-QUEUE.md`; do not revert to older QA-02/03 claims.
- No Claude branch is approved for wholesale merge in this audit. The branch candidates below are **unreconciled**, not validated missing features.

## Claude branches requiring evidence-driven recovery review

All below were compared against the current `main` on October 8. Ahead/behind is *commits*, relative to `main` at audit time. The large behind counts are a strong warning against raw merges.

| Branch | Ahead / behind | Potentially useful scope | Next action |
| --- | ---: | --- | --- |
| `claude/queue-reconcile-2026-10-08` | 1 / 238 | Tournament/records queue and semantic status | Read the three doc diffs; transplant only still-correct status not covered by merged QA work. |
| `claude/host-input-release-latch` | 1 / 238 | Input release suppression | Compare with current P2 guest-word filtering and modern modal latch; regression-test an actual remaining edge before recovery. |
| `claude/multiplayer-match-summary` | 1 / 237 | Player-visible match summary | Check current tournament/results UI; isolate any still-missing semantics rather than replacing the current host. |
| `claude/finish-snapshot-time` | 1 / 216 | Run completion timestamp and results | Compare current `.urrun`/results schema and verified finish frame; keep authoritative timing. |
| `claude/paused-overlay-present` | 2 / 222 | Actual held pause presentation | Verify against current pause rendering/toolchain patches before touching shared toolchain metadata. |
| `claude/main-menu-modal-hold` | 6 / 159 | Modal frame hold | Compare with merged #763 and current navigation; likely overlapping historical work. |
| `claude/malformed-sram-containment` | 5 / 159 | Corrupt-save isolation | Independent high-value QA-02 candidate; compare existing fail-closed recovery and promote only with fresh-process corruption fixture. |
| `claude/records-text-fit` | 3 / 151 | Records readability/layout | Evaluate current 4:3 and 16:9 UI with concrete overflows; avoid duplicating text layout. |
| `claude/split-delta-occurrence` | 2 / 159 | Split/result statistics | Verify current completed-run presentation and recording schema before selective port. |
| `claude/quit-confirm-panel` | 2 / 159 | Quit modal | Compare shipping exit confirmation behavior and mapped controller close. |
| `claude/help-pauses` | 1 / 159 | Help pause interaction | Verify if existing first-run/pause Help retains unintended racing; recover bounded test if needed. |
| `claude/pause-restart-resumes` | 1 / 204 | Pause/restart transition | Exercise restart → resume vs new race in Modern and Authentic. |
| `claude/main-menu-row-guard` | 1 / 220 | Tour/practice routing | Check current root integration and stock entry contracts. |
| `claude/two-player-join-identity`, `claude/two-player-join-disconnect`, `claude/two-player-join-fit` | 2–4 / 420 | P2 setup, seat identity and disconnect | Old parallel revisions on same files; compare as *one* feature family, do not stack or merge all three. |
| `claude/boost-speed-probe` | 10 / 122 | Mechanics/research probe | Audit against current physics findings; research-only recovery if it yields new evidence. |
| `claude/jumpover-freeze-anchor`, `claude/jumpover-native-fixture` | 2–3 / 238–145 | Jumpover fallthrough regression | Preserve genuinely unique emulator/native evidence after reconciling the two fixture revisions. |
| `claude/stunt-boundary-probe` | 3 / 118 | Stunt boundary probe | Compare latest race physics proofs and only import an unrepresented discriminator. |
| `claude/racer-hd-p2-0578-0ec3` | 5 / 238 | Broader P2 HD fallback | Graphics owner must verify asset hashes, native acceptance and superseding palette/pose registrations. |
| `claude/fix-run-date-link` | 1 / 407 | Run date linkage | Compare persisted run-date path with current product host. |

Branches observed with **zero** unique commits relative to main include `claude/audio-volume-option`, `claude/catalog-render-scale-mp-note`, `claude/controls-accessibility-status`, `claude/controls-text-fit`, `claude/density-contract-tests`, `claude/durable-recent-course`, `claude/next-event-route`, `claude/pad-glyphs`, `claude/recent-course-menu-entry`, `claude/recent-ignore-attract`, `claude/tour-entry-acceptance-ci`, `claude/tour-pad-y` and `claude/vibration-feedback`. No recovery work is indicated by those branch tips. This is a Git ancestry observation, not independent functionality QA.

## Recovery policy and release truth

Prioritize QA-02 malformed-SRAM containment and QA-03 actual P2 held input, then high-value player-visible results, 2P joining and modal correctness. Each selective recovery needs current-main repro, evidence that the feature is not already merged under a successor PR, current-main test, untouched ownership from the active CI agent, and independent review of host / toolchain conflicts. Do not promote QA-01/02/03/04 to release-passed based on narrow component acceptance. The main source of truth stays `WORK-QUEUE.md`, `SEMANTIC-SUFFICIENCY.md`, `RELEASE-QUALITY-LEDGER.json` and the modern shipping-status documents.

## Follow-up: content-level reconciliation (2026-10-08)

A further review compared **exact blob SHAs** on current `main` versus the historical Claude branch tip; this supersedes the speculative candidate ranking above where noted. An ahead count reflects distinct Git ancestry, not necessarily distinct content.

| Workstream | Source blob comparison | Disposition |
| --- | --- | --- |
| Malformed SRAM | `native/product/clean_stock_sram.cpp` and `tests/native/malformed_sram_containment_test.cpp` **identical** | Do not transplant existing implementation/test; independently validate the remaining QA-02 end-to-end recovery requirements. |
| Host input latch | `modern_host_input_release_latch.hpp` and its native test **identical** | Already present. Separate P2/tournament guest-word acceptance still required. |
| Match summary | `multiplayer_match_summary.cpp` and its native test **identical** | Already present; verify player-visible routing rather than recopy algorithm. |
| Two-player join | `local_multiplayer_seat_text.hpp` and its native test **identical** to `claude/two-player-join-fit` | Existing seat labels/layout authority present; actual disconnect/rejoin journey remains a QA case. |
| Split delta | `completed_run_presentation.cpp` **identical** to `claude/split-delta-occurrence` | No algorithm transplant warranted. |
| Records text | `completed_run_browser_host.cpp` differs; current main is 76,473 bytes vs historical branch 71,151 | Do not revert or merge older host. Compare current screenshot/overflows against acceptance and isolate defects before changes. |

These comparisons establish content presence for the **named files**, not entire-branch equivalence or passing native runs. This review did not execute a Windows build or claim full recovery QA. The highest-priority action is to test current-main behavior; cherry-picking old branches is explicitly deprioritized.

## Second pass: remaining source-content checks (2026-10-08)

More candidate branches were compared using the exact blob hashes from their tips and latest main. The following are **identical at the named evidence seam**, so their older commits should not be transplanted without a new reproduction:

- `claude/finish-snapshot-time`: `native/title/uniracers_run_data.cpp` identical.
- `claude/paused-overlay-present`: `tools/check_paused_overlay_dump.py` identical.
- `claude/quit-confirm-panel`: `tests/unit/test_pause_subview_panel_contract.py` identical.
- `claude/help-pauses`: `tests/unit/test_help_pauses_race_contract.py` identical.
- `claude/pause-restart-resumes`: `tests/unit/test_pause_restart_resumes_contract.py` identical.
- `claude/main-menu-row-guard`: `native/product/modern_tour_continue.hpp` identical.
- `claude/jumpover-native-fixture`: `tools/probe_jumpover_fallthrough_native.py` identical.
- `claude/boost-speed-probe`: `tools/probe_boost_speed.py` identical.

Two later-main divergences merit **focused review, not reverse merge**:

- `claude/records-text-fit`: `tests/unit/test_modern_overlay_text_fit.py` differs (main 8,351 bytes; old branch 7,981) and the production browser host differs. Check current native acceptance and real 4:3/16:9 clipped records before editing.
- `claude/racer-hd-p2-0578-0ec3`: `native/presentation/racer_hd_presenter.hpp` differs (main 116,242 bytes; old branch 115,969). Graphics owner should compare exact pose admission and hash-proven mixed P1-HD/P2-stock evidence, not replace a newer presenter.

**Audit limitation:** Equality is established for specified blobs only, not all files in each branch. There has been no local Windows runtime or full integration suite execution in this pass. All quality gates retain their prior statuses.
