# Modern Local Tournament: durable active-session definition

Status: active-session persistence is integrated into the Windows Local Tournament product route. A packaged one-fixture create/restore has passed (#946/#964), while completed multi-leg/3+ events and cross-process recovery remain QA-02/QA-03 work. This layer introduces active tournament identity, not result authority or a second profile database.

## Contract

The host creates a LocalTournamentSessionDefinition only after explicit selection of 2–8 profile IDs from its authoritative Modern catalog and a nonempty ordinary-Race course pool. The caller must generate a unique 32-character lowercase hexadecimal instance token independently of gameplay, run artifacts, or filenames. The session uses the canonical round-robin schedule.

The canonical, bounded (4 KiB) UR-LOCAL-TOURNAMENT-SESSION/1 file (or `/2` for a multi-leg event, which inserts exactly one `legs N` record, N = 2–3, after the instance line; single-leg events keep the original v1 bytes) persists only the independent instance token, ordered profile IDs, ordered course pool, and immutable schedule fingerprint. It never contains a fixture outcome or points. On load, the exact entrants must still occur in the authoritative profile catalog; the deterministic schedule is reconstructed and its digest and byte representation revalidated. Unknown versions, duplicate/unsupported entrants, duplicate/non-Race courses, changed fixtures, truncated/oversize bytes and profiles no longer in the catalog fail closed. The host supplies a path under its existing per-user data root. No new root, guest/SRAM write, frontend state or retrospective match association is introduced.

The product files native/product/local_tournament_session_store.hpp and .cpp now reserve separate `.pending-urtournament-*` staging directories per writer, so concurrent saves cannot truncate each other's bytes before atomic replacement (Windows replace/write-through, POSIX rename). A rejected candidate never replaces a valid session. **Replacement is still last-writer-wins**; concurrent independent event-creation/End Event sessions are not transactionally coordinated, and power-loss/fsync durability is not proven. Missing is distinguishable from Rejected or I/O failure.

The existing launch checkpoint is the complementary attempt-scoped authority. Existing receipt and batch restore contracts are the only points-awarding authority: an explicit fixture receipt plus independently admitted saved ordinary-2P pair. Neither this session definition nor a launch checkpoint can award points.

## Remaining release-quality acceptance

1. Complete QA-03 actual best-of-three and 3+ entrant tournament races across multiple process restarts and check exact standings/seat orientation.
2. Complete QA-02 dual-process event create/replace/retire fault injection, including stale checkpoint read/compare/remove, incomplete staged files, read-only/full disk and upgrade.
3. Prove proper per-user root permissions, fail-closed status and actionable recovery on the exact packaged Windows candidate. Never infer a fixture result from general Records rather than an explicit verified receipt.

The native filesystem test exercises actual save/reload and bounded rejection. It does not prove live fixture routing, native Windows boot or a player-visible Local Tournament.
