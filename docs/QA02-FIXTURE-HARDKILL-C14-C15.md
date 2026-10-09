# QA-02 C09/C14/C15 independent-process kill acceptance

Status: executable native fault harness, pending CI review. **Not** a packaged
Windows game or physical power interruption witness. This is narrower L2
process-death recovery evidence for actual production host-store APIs.

## Why a separate executable matters

The coordinator lifecycle unit test already covered the before/after receipt
state machine, but reloading another coordinator object in the same process
could retain OS state or accidentally share memory. This harness uses a native
binary linked against the real production C++ session, launch, result link,
run, and match stores. Each step starts a separate OS process with no
in-memory state transferred between stages, using one unchanged user-data
root. A child exits using std::_Exit, bypassing normal teardown and therefore
making this a true process-death cut, **not** an OS storage power cut.

## C09: sidecar claimed, public run absent

The multiplayer pair publisher already exposes a test-only callback invoked
after the real final .urmatch no-replace claim, before the corresponding
.urrun public name exists. A first process creates/arms a real event,
publishes a complete pair up to that callback and calls std::_Exit(79).
A new reader sees exactly one orphan public match sidecar, no public run,
no admitted compatible Previous/PB run, no fixture receipt and zero credit.
The private staged run and sidecar remain forensic evidence.

A fresh explicitly retried fixture publishes a new complete pair, commits its
own immutable receipt and restores precisely one genuine victory from a new
process. The original half-pair sidecar is preserved but can never become a
result. This uses a separate root from the C14/C15 cases.

## C14: saved 2P pair, no fixture receipt

An initial process creates a real profile-authorized three-player tournament,
archives the instance, publishes its active pointer, arms the first fixture,
writes a valid checksum-bound .urrun/.urmatch pair via the production
append_multiplayer_match_pair path, confirms no fixture receipt exists, and
exits 77 before calling the result-link commit.

A separately launched binary restores the active event from disk. It must
find no live pending attempt, no invented receipt and zero awarded fixtures.
It repeats the restore. The exact run and match files remain present.
A completed race in ordinary Records alone cannot become a tournament win.

## C15: receipt, stale unretired checkpoint

A new process restores that event, explicitly arms a fresh attempt for the
still-unplayed fixture, publishes another valid 2P saved pair and calls the
same production immutable fixture-receipt publisher. It confirms a creditable
receipt and the still-existing exact pending checkpoint, then exits 78
without invoking the coordinator's normal retirement step.

Three independent fresh-process restores must reconstruct exactly one
credited fixture worth three stock-win points, no live pending capture and
the other two fixtures still unplayed. The immutable receipt and pending
checkpoint bytes must stay identical across reloads.

A deliberately corrupted fixture receipt must cause fresh-process
EvidenceRejected, **not** acceptance of either saved pair, point invention
or deletion. Reinstating the exact old receipt restores the original valid
result. The test never treats an internal Python object as proof of
persistence: it inventories canonical files before and after.

## Remaining acceptance gap

This test is OS-process death, not a full game binary reaching a race or
Windows packaging. It cannot demonstrate storage-controller or directory
metadata persistence under power loss, and its controlled steps are not a
real background opponent racing simultaneously. C04 profile/SRAM
two-artifact crash, active tournament C11/C12, and Windows
same-user-root J-02/J-07/J-08 remain independent unpassed requirements.
QA-02 stays P0 and in_progress. This fixture creates no L4 witness.
