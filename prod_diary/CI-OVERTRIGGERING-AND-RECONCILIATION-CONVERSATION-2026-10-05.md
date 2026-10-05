# CI overtriggering and repository reconciliation conversation transcript

Captured: 2026-10-05

Source: project conversation **Analyze GHA Overtriggering**.

The user observed 108 active or queued GitHub Actions runs while only three agents were working and asked whether the load was genuinely necessary. The conversation moved from identifying immediately cancellable runs to preventing recurrence, then to reconciling open PRs and orphaned branch work without babysitting intermediate CI.

The resulting work merged CI-trigger hardening and rescued useful branch work, including Windows startup diagnostics, local multiplayer setup and selected-tour challenge-completion work. PR #505 stopped planning/deferred-platform changes from waking expensive workflows; PR #506 repaired the SNESRecomp title-gamepad patch digest. PRs #507, #509 and #510 then aggressively pruned obsolete or redundant automatic workflows, including deferred Switch, closed Widescreen, archaeology/reference and similar research lanes, while narrowing Native UI work to one shared build where appropriate.

The user then asked for workflow-governance documentation so future agents would not recreate the same trigger sprawl. PR #511 codified workflow creation, maintenance and retirement rules in `AGENTS.md` and the CI/operations/hygiene documentation. At that point current main was `74040131...` and no useful work remained to harvest from the superseded `chatgpt/modern-challenge-tier-policy-2026-10-05` branch.
