# Open-work integration register (2026-10-08)

This register records a read-only reconciliation of currently open pull requests against `main`. It is an **integration gate**, not evidence that unexecuted acceptance passed. Keep `docs/PROJECT-PLAN.md`, `docs/WORK-QUEUE.md`, and `docs/SEMANTIC-SUFFICIENCY.md` authoritative for product policy. Do not call a feature shipped solely because its model or unit test exists.

## PR dependency groups and merged status

| PR | Area | Integration disposition |
| --- | --- | --- |
| #891 | CI Circuit unpaced native capture | **Merged** as ac3697a; final native six-shard and aggregate validation still required. |
| #894 | CI settings persistence shard move | **Merged** as 61d3d90 after #891; projected timing improvements are not yet verified. |
| #898 | Graphics partial P1-HD / stock-P2 native pixel proof | **Merged** as aa6d6e6; actual mixed-raster witness still requires final native acceptance. |
| #899 | Graphics inactive small-OBJ ninth-X handling | **Merged** in ebf29e3; #898 retains native raster acceptance before feature enablement. |
| #798 | Replay presentation parity | **Merged** as a7c132a; fresh-process presentation parity gate remains to be executed. |
| #814 | Replay ESC/B cancel | **Merge conflict on current main** after #820/#821. Selectively reconcile code and validate cancellation with selection retention and Retry rearm; do not force stale merge. |
| #820 | Local Runs selection retention | **Merged** in a6516e0; retain targeted acceptance at final integration gate. |
| #821 | Cancelled-replay Retry rearm | **Merged** in 389c0f2; final 1P and ordinary 2P acceptance still required. |
| #815 | Tournament pre-armed fixture capture | **Merged** as 1aaa105; real joined 2P tournament end-to-end acceptance remains required. |
| #826 | Tournament completed-history restoration | **Merged** as 341912e; historical standings acceptance remains required. |

## Branch hygiene and recovery

The repository has many retained `agent/*` and `chatgpt/*` topic branches. Branch existence alone is not evidence of unfinished work. For each recovery candidate, compare against current `main`: `ahead_by=0` means no unique commits to carry, even when the branch remains listed. Diverged branches may contain obsolete changes; inspect their exact file deltas and merged successors before cherry-picking.

Sampled comparisons on this date: `agent/records-2p-production-capture-v5` is 0 ahead / 273 behind and requires no replay; `agent/replay-browser-refresh-preserve-selection-20261008` is 2 ahead / 64 behind; `agent/replay-cancel-retry-rearm-20261008` is 2 ahead / 61 behind; `agent/physics-stunt-boost-evidence-reconcile-20261008` is 2 ahead / 11 behind and docs-only. Those unique commits must be checked against successor work, not automatically merged.

## Final reconciliation gate

1. Refresh `main` and recent branch/PR activity immediately before integration. Respect other active owners and avoid overwriting moving work.
2. Resolve dependency stacks by reviewing changed files, original intent, current production integration, conflicts, and targeted native reference evidence. Preserve authenticity and Modern-host ownership seams.
3. Integrate independently proven changes in small coherent units; update the relevant primary contracts and source-of-truth roadmap only for *merged* functionality. Label incomplete real Windows product routes as incomplete.
4. Defer GitHub Actions observation until the final merge pass if doing a batched reconciliation. Before declaring completion, verify the required gates against the final `main` SHA and record any remaining failures.
5. Do not close or describe open PRs as merged until GitHub confirms the merge commit.

## Reconciliation checkpoint

Merged since initial register: #899 (graphics X-high alias), #820 (Local Runs selected artifact retention), #821 (cancelled-replay Retry rearm). Attempting #814 after those merges returned GitHub HTTP 405 merge conflicts, so it remains open and must be resolved against current Modern host code. None of these merge acknowledgments substitutes for the final native acceptance pass.

## Subsequent integration checkpoint

Additional squash merges confirmed: #826 (341912e), #815 (1aaa105), #798 (a7c132a), #898 (aa6d6e6), #891 (ac3697a), #894 (61d3d90). #894 was promoted from draft after its prerequisite #891 merged. #814 remains open because GitHub reported an actual merge conflict. These are merge receipts only; mandatory native gates on the resulting main are not yet marked passed.

## Replay cancellation current-main recovery

Original #814 is conflicted against the merged Records/replay host. Replacement #901 selectively ports its Escape/mapped-B replay cancel sequence onto current main, with a native flow cancellation test and a host-source contract test; the original branch's stale Records presentation was deliberately not carried forward. **#901 is still open pending native keyboard/controller replay acceptance and combined-main validation.** Retain #814 for provenance until #901 is validated and merged; then close #814 as superseded rather than blindly merging it.

Additional divergent branch samples: audio status reconciliation (3 ahead/20 behind, docs-only), physics stunt/boost evidence reconciliation (2 ahead/26 behind, docs-only), Windows release queue reconciliation (1 ahead/74 behind), CI runtime parallelism metrics (2 ahead/36 behind), and atomic completed-run publication (6 ahead/130 behind). Each requires exact successor comparison, because later main may have already superseded its intended behavior.

## Final replay conflict disposition

#901 merged as `6c7af19325e1804db4a1469245f84997ee72de97` after selective current-main reconciliation. Original #814 was closed as superseded. Tooling run 37828346181 failed on a stale two-argument call to `load_completed_local_tournament_history` in the tournament native test; #902 merged as `5968aaded3e4e2effa056395e8fcde9ded070b60` to match the production one-argument API. Previous native boot smoke and Modern router on #901 passed; tooling rerun and combined-main end-to-end evidence remain separate validation requirements.
