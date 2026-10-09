# QA-02: Protect newer ghost sidecars against downgrade

Status: proposed C17 persistence fix, not an upgrade/downgrade packaged
Windows witness or a new ghost presentation feature.

## Source-confirmed hazard

The optional world/pose ghost sidecar is intentionally replaceable so a
supported trace can be repaired. Unlike immutable .urrun/.urmatch records,
an old executable previously replaced any existing regular .urghost file,
even if its checksum-protected header declared a newer schema. A player
rolling back to an older build could thus erase valid future ghost
presentation evidence merely by finishing the corresponding race or
regenerating the trace.

## Narrow correction

The writer now acquires a persistent per-sidecar OS handle mutex and
rechecks destination type under that lock before writing. A versioned
existing trace is decoded through the bounded loader. If the header and
checksum identify UnsupportedVersion, the writer refuses to replace it,
reporting a specific diagnostic. The per-path lock remains held through
private staging, explicit OS data flush and atomic final rename, protecting
this read/replace decision from cooperating concurrent processes.

Replacement of a supported valid trace remains allowed. Repair of a
same-era damaged trace remains possible under the existing design; this
change guards specifically the positively recognized newer schema.
Malformed/future-looking bytes without a valid checksum still cannot
be conclusively distinguished from a damaged current trace, so this does
not constitute a blanket guarantee against all forward-version data loss.
An old binary predating this lock is not a cooperating writer.

The native trace test synthesizes a **valid sealed schema version 2**
ghost, confirms the loader marks it unsupported, tries to save a valid v1
replacement and verifies the existing v2 bytes and header survive. It
then explicitly removes that test artifact before the existing same-v1
replacement, corruption, device-destination, and fresh-target reload tests.
A source contract enforces lock, version check and publication order.

## Acceptance remaining

C17 still needs a pinned newer/older executable pair and existing user
data root exercised across upgrades and downgrades. The optional trace
does not authorize a run, PB, or tournament receipt. Group durability
and live two-window J-07/J-08 fault tests remain P0, with no L4 witness.
