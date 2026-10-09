# QA-02: Immutable tournament archive create-only publication

Status: proposed two-process namespace-race correction; exact packaged
Windows L4 and multi-file transaction remain unverified.

The tournament coordinator intentionally preflights whether its new
32-hex instance-ID directory already exists, creates a fixtures subdirectory
and archives the canonical immutable session plan *before* publishing
`active.urtournament`. That sequence is not exclusive across processes:
two creators forced to use the same instance ID can both pass the initial
`exists()` check before the first creates the directory. Previously the
subsequent archived `session.urtournament` write used unconditional
last-writer-wins replacement. A losing creator could replace the winner's
archived plan while the active pointer still referred to the winner and
even after the winner had persisted fixture receipts.

The archived plan now uses the existing OS-handle-locked
`save_local_tournament_session_definition_if_current(path, nullopt, next)`
create-only primitive. It holds the per-archive mutex from the historical
canonical load through publication. The second claimant returns
`Conflict`, which the coordinator reports as `AlreadyExists`; invalid
or unreadable existing archives also fail closed instead of being overwritten.
No active pointer is published by the archive loser. The existing
`active.urtournament` typed CAS remains the separate second stage.

The native coordinator lifecycle fixture attempts to overwrite a
preexisting valid archive with another *different valid schedule* using
the create-only store and confirms the original complete plan survives.
A separate production source contract ensures new coordinator creation
uses this same store entrypoint rather than the old unconditional writer.
Its exact cross-process lock mechanism has already been tested for the
active-session path; a simultaneous forced-same-ID coordinator race on a
Windows packaged candidate remains an L4 witness to capture.

This is a safe per-instance publication barrier, not multi-file atomicity.
A crashed or losing creator may leave a receipts directory without an
archive, or a valid inert archive when the active pointer CAS loses.
Neither may be credited or autoactivated without independent authority;
the canonical active pointer and receipt-bound records remain distinct.
QA-02 P0 remains `in_progress`.

## Historical active-session archive migration (2026-10-09)

A separate restore-time race existed after new-instance archive creation was
fixed. Older installations can contain `active.urtournament` without the
later per-instance `session.urtournament`. On restore, the coordinator
observed a missing archive and then unconditionally wrote its own bytes. A
second process could create a different existing archive between that
observation and the write. Last-writer-wins migration would silently erase
that file.

Migration now reserves the historical instance archive using the **same
create-only typed CAS** as new tournament creation. If another process wins
the exact same migration, the loser reloads the historical archive and
accepts it **only if every canonical byte agrees** with the active pointer.
If a foreign, unsupported or corrupt archive is present, restore rejects
with `EvidenceRejected`, preserving the evidence for future salvage.
Storage failures remain `StorageFailed`; no fallback reinitializes
standings or the original global active pointer. Normal same-plan concurrent
restores still succeed.

The native coordinator lifecycle fixture removes an archived plan to model
an old build, restores it, validates canonical bytes, verifies a second
restore, and tests foreign-valid and corrupt archive rejection. A source
contract protects this migration call from regressing to unconditional save.

This closes a bounded restore-time overwrite, not an atomic
`active.urtournament`/archive transaction. Sudden power loss between them,
and Windows two-instance recovery acceptance, remain QA-02 P0.
