# Local Tournament completed-event history

Status: backend persistence and read-only history loader, native disk-backed acceptance. It does not add a player-visible Records archive screen.

## Why per-instance plans matter

The first durable Local Tournament coordinator stores the active session definition under the host-owned tournament root and fixture receipts beneath an instance-ID-specific directory. Without a retained copy of the immutable roster and course pool inside that instance directory, replacing the active tournament would leave old fixture receipts on disk but make their schedule impossible to reconstitute reliably. Matching stored run history by profile, course or date would be an invalid substitute.

New tournament creation now publishes the exact canonical session definition under the unique instance's `session.urtournament` path **before** publishing the active-session pointer. Each saved fixture still uses the unchanged exact receipt link to a previously admitted `.urrun` + `.urmatch` pair. A failed active-pointer write can leave only an inert archive; it cannot silently reassign old match results to the new active tournament. Fresh-process active restore cross-checks its canonical definition against that exact per-instance archive. Existing old-format active definitions without an archive are migrated by saving their validated canonical definition; this migration never attributes a new result.

## Read-only completed history

`load_completed_local_tournament_history` enumerates at most 256 canonical 32-hex tournament instance directories under the configured per-user tournament root. It loads only their own validated immutable definition and exactly indexed receipt-linked saved 2P pairs. Only tournaments with every explicit scheduled fixture successfully restored become **completed** history entries, with the already-established win/draw/points and ranking rules. Incomplete instances and unavailable/corrupt evidence are counted but never promoted into completed standings; failed directory scans report unavailable rather than silently returning an authoritative empty history. Random instance-ID order is deterministic only, not a claim of chronological ranking.

The loader neither scans generic Multiplayer Records for a convenient opponent/course pair nor promotes an old unbound match into an event. A tournament with corrupt archived definition, mismatched instance directory or missing evidence cannot appear as completed, even if all underlying general Records matches remain individually valid.

## Shipping boundary

A strict C++17 filesystem test creates a three-fixture tournament from real checksum/course-bound stored run+match pairs, completes it, starts another tournament, restores the original's three results and standings through the new archive API, and demonstrates fail-closed behaviour for misplaced/corrupted session definitions. It does not exercise an actual Windows controller/race or a visual Records archive. The owning Modern UI still needs a history destination, active fixture selector, standings/completed-tournament presentation and fresh-process native acceptance.
