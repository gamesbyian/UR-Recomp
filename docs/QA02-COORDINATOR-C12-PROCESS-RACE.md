# QA-02 C12: Full coordinator two-process creation race

Status: proposed native process-level integration fixture, pending CI.
This is neither a packaged Windows candidate nor physical power-fault proof.

The initial source-level active.urtournament CAS test raced the *storage
primitive* from two separate processes. It did not prove that the complete
coordinator's multi-step create flow, which publishes a per-instance archive,
a fixtures directory and then the active event pointer, actually resolves
simultaneous user sessions consistently.

This test compiles the real production coordinator and stores into one
executable. For each of five independent roots, two OS processes reach
an explicit file barrier while proposing **different valid tournament
instances and different canonical schedules**. Both then call
create_local_tournament_coordinator on the same user root. The accepted
outcome is exactly one Created and one AlreadyExists. Neither StorageFailed
nor two Created outcomes are accepted.

Two fresh verifier processes restore only the single canonical active
winner, verify the active pointer's full bytes agree with its archived plan,
refuse all invented fixture results or pending guest launches, and verify
that any losing inactive archive remains tied to its own identity and
cannot masquerade as a completed result. The number of visible archival
directories may be one or two, depending on when the loser detected the
active incumbent. The fixture never deletes a losing archive or treats
the absence of an inactive archive as proof of transaction rollback.

This concretely exercises the complete C12 coordinator path against the
race scenario, beyond the earlier single-file CAS probe. It does not
establish a power-safe journal across archive and active pointer, nor
permission to automatically activate a stranded event after process
death. Two live game windows remain capable of contending for future
fixture ownership. Exact packaged Windows same-root J-07/J-08 and
power interruption remain QA-02 P0 L4 requirements.
