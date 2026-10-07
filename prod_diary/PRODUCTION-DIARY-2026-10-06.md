# UR-Recomp Production Diary — 2026-10-06

**Project:** UR-Recomp  
**Repository:** `gamesbyian/UR-Recomp`  
**Continuation of:** `PRODUCTION-DIARY-2026-10-05.md`

October 6 was the day the project's extraordinary parallel throughput finally outran some of the infrastructure built to contain it.

The useful work did not stop. Windows x64 continued to gain real product behavior: Resume/Restart Tour became a complete player flow, the regional Uniracers/Unirally preference gained an exact retail title consumer, local multiplayer gained an independent join surface, portable state became upgrade-safe, startup diagnostics closed into a release-facing contract, Racer HD coverage expanded by measured burden, and presentation-density policy was bounded for Modern overlays.

But most of the human attention went somewhere less glamorous: GitHub Actions.

## Product lanes kept landing

Several October 5 lanes crossed from plan to product overnight.

The unfinished-tour work is now a coherent Modern flow rather than a hidden persistence trick. Resume and Restart both travel through stock menus; only Resume may restore the narrow validated continuation; Restart waits until stock itself proves it performed the historical wipe before retiring host continuation state. The implementation is transactional around host profile and SRAM publication and fails closed on context changes or route failure.

Regional presentation also became visible. The Europe setting can present the exact verified Unirally title raster on the admitted idle-title surface while NorthAmerica remains the live canonical Uniracers raster. Authentic mode and guest machine state remain untouched. The animated stock-style transition is still open, which is the correct outcome: the evidence supports the title substitution, not yet the flourish around it.

Local multiplayer moved from a deterministic assignment model to an actual source-aware join overlay. The framework still owns device-to-seat assignment and the stock game still owns rider selection. The host surface only decides whether two valid sources have joined. A later parity failure showed why these narrow authority descriptions matter: controllerless deterministic routes were accidentally entering the new overlay until the runtime gate was tightened to require a real connected source.

The Windows package stopped behaving like a clever ZIP and started behaving like a durable consumer application. Mutable config, bindings, saves, profiles, run data and related state now have a per-user home outside the package. Legacy package-local state migrates transactionally and idempotently, destination state wins, and host-state publication is atomic. Startup failures now have stable release-facing codes and a bounded log rather than depending on a developer watching stderr.

## Racer HD finds a scalable rhythm

The measured-fallback rule introduced on October 5 paid off immediately.

Instead of browsing adjacent ROM registrations and deciding what looked like the next animation family, the tooling ranked unsupported states by actual player-visible fallback burden. The agent then worked through bounded P1 contexts one at a time, retaining stock raster evidence, temporal witnesses, authored geometry, review artifacts and hash-bound approval.

By the `01B9` slice, broader ordinary-play coverage had moved from 118/5282 HD selections to 653/5282. Measured coverage rose from 2.23% to 12.36%, removing 535 baseline Original fallback frames.

The deeper win is procedural. Art expansion is one of the easiest places for an autonomous agent to wander because almost every neighboring asset can be argued to be useful. Giving the agent a machine-generated priority queue turns taste-adjacent work into a reproducible optimization loop. It also gives later agents an exact place to resume after a stalled session.

## The CI repair loop

The day's dominant story was a chain of red workflows that repeatedly appeared to be fixed and then revealed another failure.

Some defects were tiny: malformed patch hunk counts, stale SHA-256 registrations, shell continuation mistakes, CRLF-versus-LF comparison, second-run migration fixtures retaining read-only state. Others were architectural: workflows encoded assumptions about exact hook shapes; a new multiplayer UI changed deterministic presentation routes; Native UI evidence rebuilt essentially the same candidate multiple times; aggregate validators ran after prerequisites had already failed; expensive product journeys lived inside a nominal smoke gate; historical specialist workflows still carried broad triggers.

The frustrating property of these bugs was their cost function. Most took minutes to understand and seconds to patch, but the answer often arrived only after another long remote run. An AI agent's ability to produce a quick local fix is actively unhelpful when the dominant latency is ten or fifteen minutes of CI and each run exposes only the next hidden assumption.

The successful move was to stop treating the latest red as the unit of work.

PR #563 audited and hardened the CI architecture itself. Native build/boot smoke was refocused into a bounded fast gate with an approximately four-minute target and an eight-minute timeout. Long product journeys went back to focused owner workflows. Native UI evidence now builds one candidate and fans that exact artifact across five capture shards instead of compiling five copies. Aggregate validation is gated on successful prerequisites. Structured diagnostics replace order-sensitive log greps. Specialist workflows have narrower triggers and toolchains. Evidence writers that mutate retained reports are serialized. Mechanical tests now reject several of the fragility patterns that caused the day's failures.

The result matters more than whether one particular run is green. The repository now has fewer ways to convert an unrelated product change into fifteen minutes of opaque integration roulette.

## A note on agent coordination

The project passed roughly 471 nominal agent-hours during its first week, based on PR open-to-close intervals plus a small per-PR allowance. That number is not a meaningful measure of human labor, but it describes the shape of the project accurately: enormous parallel machine effort compressed into a few days of wall-clock time.

The repository architecture is what makes that remotely useful.

The good parts of the AI-driven process are clearest when work can be turned into independent evidence-rich leaves: one exact regional raster consumer, one progression policy seam, one measured Racer pose, one package migration rule. Agents are very effective at exhausting those bounded problems, especially when acceptance can be run mechanically.

The weak parts appear in shared implicit infrastructure. Framework patches, generated snapshots, manifests, workflow contracts and broad host integration seams can couple agents that never touch the same source file. Prompting agents to “avoid overlap” helps, but it cannot solve invisible coupling. The durable answer is to make those shared contracts explicit, cheap to validate and narrow enough that failures identify their owner.

Session stalls supplied a related lesson. They were annoying rather than catastrophic because agents had been committing frequently and leaving durable docs/branches. Work that exists only inside one conversational context is fragile. Work that is committed in small, semantically named increments can be rescued by another agent with very little ceremony.

## End-of-day state

By the end of October 6, UR-Recomp was more obviously a modern Windows product than it had been twenty-four hours earlier, but the larger advance was operational.

The project now has a clearer separation between fast integration confidence and slow specialist acceptance; host-owned product policy and guest-owned game behavior; measured player-visible priorities and open-ended archaeology; recoverable repository state and ephemeral agent context.

That separation is likely to matter as much to the remaining remaster work as any rendering or reverse-engineering breakthrough. The project has already shown that AI can generate changes at startling speed. October 6 was the day the repository learned that the harder problem is making those changes compose.
