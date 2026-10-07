# Windows package lifecycle conversation transcript

Captured: 2026-10-05

Source: October 5 packaging conversations, including the current **durable consumer package lifecycle** agent prompt.

Windows x64 remained the primary deliverable. The first packaging milestone was a validated portable extracted-folder/ZIP contract that boots correctly from an unrelated working directory; that work landed in PR #493, **Add validated Windows x64 portable consumer package**.

The next conversation deliberately did not reopen package design or introduce an installer. It narrowed the next step to durable consumer lifecycle concerns: moving mutable user data cleanly away from immutable package contents, preserving product/profile/settings/run persistence semantics, and making startup diagnostics useful in a normal installed/extracted consumer environment. PR #504 separately rescued the Windows startup-diagnostics contract.

At archive time this lifecycle lane had just been assigned and had not yet produced a new dedicated PR beyond the existing portable-package and startup-diagnostics foundations.

## Follow-through captured 2026-10-06

The lifecycle lane subsequently landed a durable Windows per-user state root, transactional migration from legacy package-local state, destination-wins/idempotent upgrade behavior and atomic host-product-state publication. Startup diagnostics were closed around stable ROM/save/runtime/video/audio failure codes and one bounded per-process log.

This lane also supplied several of the day's most expensive CI lessons. Small mechanical defects in framework patch hunks, pinned SHA-256 values, archive newline assumptions and second-run fixtures repeatedly turned into full native-workflow failures. None of those mistakes were conceptually hard. Their cost came from delayed feedback and broad fan-out. The later CI hardening work therefore treats fast local/mechanical validation of patch bytes, manifests and fixtures as part of feature development, not housekeeping after the feature is “done.”
