# Open-work integration register (2026-10-08)

This register records a read-only reconciliation of currently open pull requests against `main`. It is an **integration gate**, not evidence that unexecuted acceptance passed. Keep `docs/PROJECT-PLAN.md`, `docs/WORK-QUEUE.md`, and `docs/SEMANTIC-SUFFICIENCY.md` authoritative for product policy. Do not call a feature shipped solely because its model or unit test exists.

## PR dependency groups and merged status

| PR | Area | Integration disposition |
| --- | --- | --- |
| #891 | CI Circuit unpaced native capture | Await full six-shard native UI + aggregate acceptance; the matched-root byte proof is documented in PR but final native gate was still required. |
| #894 | CI settings persistence shard move | Explicitly stacked behind #891; rebase after #891 and measure all native UI shards. Do not infer actual times from projections. |
| #898 | Graphics partial P1-HD / stock-P2 native pixel proof | Candidate capture is disabled by default; same-frame visual witness remains required. Reconcile with #899 before accepting predicate-based admission. |
| #899 | Graphics inactive small-OBJ ninth-X handling | **Merged** in ebf29e3; #898 retains native raster acceptance before feature enablement. |
| #798 | Replay presentation parity | Heavyweight manually dispatched fresh-process native gate still required according to PR description. |
| #814 | Replay ESC/B cancel | **Merge conflict on current main** after #820/#821. Selectively reconcile code and validate cancellation with selection retention and Retry rearm; do not force stale merge. |
| #820 | Local Runs selection retention | **Merged** in a6516e0; retain targeted acceptance at final integration gate. |
| #821 | Cancelled-replay Retry rearm | **Merged** in 389c0f2; final 1P and ordinary 2P acceptance still required. |
| #815 | Tournament pre-armed fixture capture | Originally stacked on #808; reconcile against already integrated 2P and tournament authority, then exercise a real joined stock race. |
| #826 | Tournament completed-history restoration | Requires strict fresh-process archived-instance and checksum-bound receipt acceptance; presentation of history remains separately incomplete. |

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
