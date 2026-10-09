# QA-02: Completed-run and multiplayer-pair data durability

Status: proposed prepublication OS file flush for immutable evidence;
**not** an atomic multi-file transaction or physical power-loss acceptance.

## Observed source gap

The Modern completed-run publisher saved a staged `.urrun` through a
`std::ofstream` codec and then published the final filename with atomic
no-replace semantics. The multiplayer publisher staged a checksum-bound
`.urmatch` sidecar and then claimed its public sidecar name before the
associated run. Both correctly detected reported stream close failures,
but neither asked the OS to durably flush its staged bytes first.
`ofstream::close` and `fflush` are not equivalent to `fsync` on POSIX or
`FlushFileBuffers` on Windows.

Consequently, a newly visible run or authoritative match sidecar could
lack durable contents after a power interruption despite correct
no-clobber publication. This is a source-confirmed durability deficiency,
not evidence that such corruption has already occurred in a shipped build.

## Correction

`detail::sync_closed_staged_file(path)` reopens only the owned closed
staging file, using `_wfopen(..., L"rb+")` for Unicode Windows paths or
`fopen(..., "rb+")` for POSIX; it requests the same explicit storage
flush used by profile/catalogue saves and verifies close. The extra
reopen is necessary because the existing record codecs own and close their
`ofstream` handles.

- Standalone `.urrun`: complete codec save, explicit staged data flush,
  then no-replace public filename claim. Failure before claim leaves
  no visible run. Directory metadata flush is attempted after success.
- Bound multiplayer pair: the nested run append already flushed its
  bytes. The separately staged `.urmatch` receives its own data flush
  **before the sidecar is claimed**, then the run name is claimed. On
  collision or later error the original scoped pair rollback remains.
  After both names exist, the directory metadata is best-effort synced.
- Any flush/open/close error before publication fails closed with a
  specific diagnostic and private staging cleanup. We do not report a
  successful public claim as an uncommitted failure simply because an
  after-publication directory sync is uncertain.

`test_run_match_staged_durability_contract.py` checks ordering and
platform path behavior. Existing record, pair, and no-replace tests remain
the actual behavioral coverage; CI and packaged Windows tests are still
required.

## What this does not prove

A kill after the sidecar but before the run's public name is still an
intentionally incomplete pair, not a completed record. A kill after both
but before a tournament fixture receipt also remains a separate C14
window. The durability of a directory entry can remain uncertain after a
successful POSIX hard link (best-effort postpublish sync), and physical
controller/cache failures cannot be ruled out in code. A journal spanning
`.urrun`, `.urmatch`, optional `.urghost`, the immutable fixture receipt
and `pending.urlaunch` does not yet exist. QA-02 P0 and exact Windows
C09/C14/C15/J-07/J-08 remain open.
