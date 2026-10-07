# Merge, reconciliation and fresh-agent prompts conversation transcript

Captured: 2026-10-05 through 2026-10-06

Source: project conversations covering repeated “merge PRs, rescue orphaned work, then write fresh-agent prompts” sessions.

The user repeatedly asked that open PRs be reconciled into current `main`, useful orphaned branch work be rescued, and intermediate CI not be babysat. The intended operating model was to finish repository integration first, run the final gate against the actual merged state, then use the latest plan/docs to launch fresh non-overlapping agents.

Several sessions stalled during this work. Because the active agents had generally committed small increments and kept their changes on bounded branches, later sessions could recover the useful deltas rather than recreating them from chat memory. The October 5/6 merge trains pulled together Windows package lifecycle, Racer HD measured coverage, regional presentation, Resume/Restart Tour, profile reset, local multiplayer and startup-diagnostics work.

The repeated fresh-agent prompts converged on a common structure: Windows x64 first; refresh main; inspect PRs and branches updated in the last few minutes; avoid active files; read the subsystem's canonical plan/evidence documents; make one production-quality step; preserve stock/game authority; update docs/queue; commit often.

The process worked well for parallel leaf work. Its weakness became visible at integration time: branches that did not overlap in source files could still interact through shared SNESRecomp patches, manifests, generated snapshots and GitHub Actions contracts. October 6 therefore shifted attention from agent-lane overlap to hidden integration coupling.
