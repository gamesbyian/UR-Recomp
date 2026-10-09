# QA-02: Active tournament create/replace concurrency

Status: proposed store + coordinator correction, with process-level acceptance
awaiting execution. **QA-02 remains P0.**

### Confirmed lost-update path

The tournament coordinator previously preflighted
`active.urtournament` with `exists()`, constructed a new instance and
archived its immutable schedule, and then unconditionally called a mutable
last-writer-wins session-file save. Two processes could both pass the
preflight and publish different active tournaments, silently replacing one
another's chosen event. A process explicitly replacing a known older active
session could also erase a different event created in the meantime.

The immutable per-instance archives and receipts prevent direct destruction
of previous game files, but do not preserve the correct *active event
selection*, next fixture or pending attempt for a live process. A malformed
active pointer could previously be overwritten when explicit replacement
was requested.

### Contract

`save_local_tournament_session_definition_if_current` now holds the
persistent OS-handle `.urmutex` lock across historical canonical load,
comparison and staged publication of `active.urtournament`. Expected
`nullopt` is create-only. An explicit replacement must carry the full
canonical definition observed at the beginning of creation. If another
process has replaced it, return `Conflict` rather than accepting the new
pointer. Malformed/unsupported disk bytes cannot satisfy a valid expected
state and are never silently reset. The coordinator maps conflict to
`AlreadyExists`, preserving its existing explicit replacement pathway
while requiring a fresh user decision after a conflicting writer.

New native process tests seed an original event, have two child processes
load the same initial definition, release a synchronization barrier and
race distinct successor events. Exactly one must return `Saved`, one
`Conflict`; fresh disk load must identify one complete winning event.
A corrupt active pointer must survive failed create-only publication
unchanged. The existing coordinator's lifecycle test still exercises
actual archive/session/receipt behavior.

### Remaining P0 work

This fix serializes **active pointer publication only**. It does not
provide atomicity across archive directory creation, the mutable
`active.urtournament` pointer, `pending.urlaunch` launch checkpoints,
`.urrun`/`.urmatch` pairs, immutable fixture receipts or profile
identity changes. A crash may leave a valid archived but inactive event.
Completing and restoring a tournament across multiple processes with
storage faults and exact packaged Windows acceptance remain required.
