# Modern Local Tournament: durable active-session definition

Status: Windows-compatible persistence adapter and native filesystem tests, not yet a playable tournament. This layer introduces active tournament identity, not result authority or a second profile database.

## Contract

The host creates a LocalTournamentSessionDefinition only after explicit selection of 2–8 profile IDs from its authoritative Modern catalog and a nonempty ordinary-Race course pool. The caller must generate a unique 32-character lowercase hexadecimal instance token independently of gameplay, run artifacts, or filenames. The session uses the canonical round-robin schedule.

The canonical, bounded (4 KiB) UR-LOCAL-TOURNAMENT-SESSION/1 file persists only the independent instance token, ordered profile IDs, ordered course pool, and immutable schedule fingerprint. It never contains a fixture outcome or points. On load, the exact entrants must still occur in the authoritative profile catalog; the deterministic schedule is reconstructed and its digest and byte representation revalidated. Unknown versions, duplicate/unsupported entrants, duplicate/non-Race courses, changed fixtures, truncated/oversize bytes and profiles no longer in the catalog fail closed. The host supplies a path under its existing per-user data root. No new root, guest/SRAM write, frontend state or retrospective match association is introduced.

The product files native/product/local_tournament_session_store.hpp and .cpp atomically publish a canonical session through a same-directory temporary file using the existing platform approach (Windows replace/write-through; POSIX rename). A rejected candidate never replaces a valid session. Missing is distinguishable from Rejected or I/O failure.

The existing launch checkpoint is the complementary attempt-scoped authority. Existing receipt and batch restore contracts are the only points-awarding authority: an explicit fixture receipt plus independently admitted saved ordinary-2P pair. Neither this session definition nor a launch checkpoint can award points.

## Remaining production integration

1. Host create/load/continue this session from an explicitly selected roster. Choose an unfinished fixture and persist its distinct launch attempt before stock 2P routing.
2. Bind confirmed live P1/P2 profile identities and observed course to that fixture. Pass the retained attempt ID through the real 2P capture owner, never infer an attempt from general Records history.
3. After transactional .urrun/.urmatch publication, validate the exact persisted pair, commit the matching attempt, persist its receipt/reference, and retire the launch checkpoint. Fresh-process continuation must restore completed fixtures from those explicit receipts.
4. Expose fixture selection, ordinary 2P route/continuation, standings and completed-tournament presentation using original League visual grammar through the owning Modern UI work.

The native filesystem test exercises actual save/reload and bounded rejection. It does not prove live fixture routing, native Windows boot or a player-visible Local Tournament.
