# QA-02: Immutable fixture receipt data durability

Status: prepublication file-flush hardening, **not** Windows packaged
power-failure acceptance or complete cross-artifact atomicity.

## Why this matters

A tournament receipt is the authority that turns an ordinary saved 2P
run/match pair into one credited fixture. Its previous publisher used private
same-directory staging and a no-replace final pathname, but called only
`fflush` and `fclose` before publishing. Neither API requests that the OS
push staged receipt bytes to durable storage. The existing no-replace rule
avoids racing writers overwriting each other's receipts, but it does not
prevent a power failure from exposing a new receipt name whose contents
were never persisted.

## Correction

The fixture link writer now uses the same cross-platform
`detail::sync_staged_file` as mutable profile and catalog publication:
Windows `FlushFileBuffers`, POSIX `fsync`. A short write, `fflush`,
storage flush, or close failure blocks the no-replace visibility transition
and cleans up only that writer's reserved private staging directory. The
same OS-level durability request precedes the Windows
`MoveFileExW(MOVEFILE_WRITE_THROUGH)` or POSIX atomic hard-link claim.

After successfully claiming the canonical fixture name, the writer attempts
the same best-effort POSIX parent directory `fsync` as other host stores.
The operation does **not** return an uncommitted failure when a directory
sync cannot be guaranteed after publication. The existing status model
cannot distinguish committed-but-uncertain durability from never-committed;
a false failure invites a damaging compensating result or duplicate replay.

`test_local_tournament_receipt_durability_contract.py` guards the
production write/flush/sync/close/no-replace ordering. Preexisting native
fixture-link tests remain responsible for no-replace contention, exact
receipt/pair admission and restoration.

## Limits and next witness

This is not a guarantee that Windows storage controllers honor every flush,
nor proof of a real power outage. The run/match evidence files have their
**own** durability contract and require separate inspection. A kill between
published `.urrun`/`.urmatch`, fixture receipt publication, and
`pending.urlaunch` retirement must still recover deterministically across
processes. Receipt+pair+checkpoint group commit remains unimplemented.
QA-02 stays P0 until exact-archive Windows C09/C14/C15/J-07/J-08 fault
acceptance is recorded.
