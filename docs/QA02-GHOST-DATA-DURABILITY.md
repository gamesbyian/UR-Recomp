# QA-02: Ghost trace staged-byte durability

Status: proposed bounded host artifact hardening; **not** a power-loss
release witness or cross-artifact atomic commit.

The `.urghost` optional pose/world trace is published through a privately
reserved same-directory `.pending-urghost-*` stage and a final atomic rename.
Previously its `std::ofstream` was closed and errors checked before
publication, but the staged bytes were not explicitly flushed to persistent
storage. Under an abrupt power loss, the final sidecar filename could become
visible without durable contents. Its association with `.urrun` checksum
prevents unrelated run credit, but corrupted or lost ghost presentation is
still a player-visible defect.

The writer now reopens its **private closed** `trace.tmp` with write access
(`_wfopen` with native wide path on Windows, `fopen` on POSIX), calls the
shared `detail::sync_staged_file` OS durability primitive and checks close
before renaming. Any failure leaves the old canonical ghost intact and
cleans only the unsuccessful private staging directory. After a successful
rename the POSIX parent-directory sync is attempted best effort. A failure
at that point cannot safely be reported as an uncommitted write, since the
new trace is already visible. The same limitations documented for staged
host-profile metadata durability apply.

`test_ghost_trace_data_durability_contract.py` guards the actual
write/close/OS-sync/rename ordering and Windows Unicode path. Existing
codec, bound checksum and atomic replacement tests still govern behavior.

This **does not make the optional ghost part of an atomic transaction**
with `.urrun`, `.urmatch`, or tournament receipts. A crash after the
run but before the ghost may leave a valid completed run without an optional
trace; presentation must retain its documented Original fallback. A dying
device/controller that ignores flush commands also lies outside CI proof.
QA-02 C09/C10 and Windows J-07/J-08 L4 remain open.
