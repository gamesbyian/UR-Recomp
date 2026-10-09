# QA-02: Single-file staged write durability

Status: proposed bounded hardening, **not** full power-failure acceptance.

The shared `write_host_replace_staged` primitive owns mutable Modern
`host-profile.txt`, `profiles-v1.txt`, host settings and mutable tournament
session and launch checkpoint saves. These writers already reserve private
same-directory staging directories, flush/close their staged payloads, then
atomically replace the canonical pathname. Previous behavior did not issue
a storage-layer data flush: `fflush`, `fclose` and POSIX `rename` alone
never promise persistence through abrupt power loss.

The storage primitive now requires the operating system to accept an explicit
file-content durability flush before the visibility transition. POSIX uses
`fsync(fileno(...))` after C stdio flush; Windows uses
`FlushFileBuffers` on the CRT-owned handle. If staged writing, fflush,
the storage flush or close fails, the previous canonical file stays intact,
the private staging directory is cleaned up, and the caller sees failure.
A test-only sync override forces this exact point to fail and asserts the
last good launch/profile state survives a subsequent process.

After a successful POSIX rename, a directory `fsync` is attempted as
best-effort metadata durability. It cannot be a definitive success/failure
in the current boolean API: by that point the replacement is **already
visible**, so claiming the whole save failed may cause higher-level callers
to attempt harmful compensating writes. The directory attempt's result
therefore does not change the publication return value. Windows currently
uses `MoveFileExW(MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH)`
after its prepublication file flush, but no physical power-loss evidence
has validated the full Windows I/O stack.

### Release blockers not closed

- Directory durability and crash recovery require a distinguishable
  `CommittedDurable` / `CommittedUncertain` / `NotCommitted` API if
  parent sync failure is to be acted upon safely.
- The transaction across framework `save.srm`, Modern profile state,
  catalog membership, `.urrun`, `.urghost`, `.urmatch`, fixture
  receipts and launch checkpoints is still **not atomic**.
- Separate immutable run/match and optional ghost publishers have their
  own file durability policies. This change does not silently certify them.
- False durability after a controller/storage-cache reset cannot be proven
  away by software-only CI. Test on the exact packaged Windows candidate.
- The future supported storage media and Windows/macOS filesystem semantics
  must be measured before a user-facing power-loss guarantee is made.

Focused tests: `tests/native/local_tournament_atomic_replace_test.cpp`
and `tests/unit/test_host_persistence_process.py`. Run each on an actual
candidate. QA-02 remains P0 until L4 J-02/J-07/J-08 acceptance.
