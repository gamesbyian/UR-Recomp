# UR-Recomp Production Diary — 2026-10-05

**Project:** UR-Recomp  
**Repository:** `gamesbyian/UR-Recomp`  
**Continuation of:** `PRODUCTION-DIARY-2026-09-28-TO-2026-10-04.md`

This daily continuation is synthesized from October 5 project conversations and the PRs that survived reconciliation. As before, PRs remain the authority for exact diffs and CI evidence; the diary records why the work moved where it did.

---

## October 5 — The project turns decisively into a Windows product

The first week ended with most architectural risk already burned down. October 5 therefore looked different from the preceding excavation sprint. The central question was no longer whether the game could be reconstructed faithfully. It was how quickly the proven substrate could be converted into a coherent Windows x64 product without letting parallel agents rebuild the same systems twice.

### Planning gets compressed around product decisions

PR #483 was the hinge. The project plan and work queue were rewritten around the current Windows consumer path rather than the historical fidelity → Widescreen → HD ladder. Old completed archaeology and stale “future work” claims were removed from active planning surfaces. Several questions that already had enough evidence were reclassified as product-policy choices and actually decided.

That produced a clearer Modern frontend policy: Play / Practice / Multiplayer / Records / Options; simultaneous local multiplayer setup; canonical racers without invented personalities; selectable Bronze/Silver/Gold challenge tiers; resumable tours; a unified Records browser; modern text entry; and deferred advanced cosmetics/photo/replay-editor/mod work.

PRs #482 and #484 were then reconciled down to the non-duplicated pieces that still mattered: a shared PPM validator and hardened Internal Render Scale acceptance. PR #485 repaired a test whose assumptions had become stale after the policy cleanup. PR #486 turned the day's CI failures into explicit agent guidance rather than another pile of local fixes.

### Three product lanes immediately become real features

The next agent batch produced three of the most obviously player-facing features yet.

PR #487 added a profile-safe Modern Continue Tour path. It preserves authoritative profile/SRAM ownership while restoring the transient tour state that stock rider selection normally clears. The acceptance story is fresh-process and fail-closed: valid resumable state reaches stock TRACK_SELECT with the expected tour row restored; stale or mismatched state does not.

PR #488 added authoritative live timing, PB comparison, signed deltas and split presentation, while also advancing the first unified Records surface. It reused completed-run records rather than creating a second timing database.

PR #489 removed repeated menu traversal with Rematch, Repeat Practice and Recent Course shortcuts. These routes reuse existing stock/Quick Practice/Restart machinery and are explicitly progression-safe. A speculative Next Event shortcut was left out until its semantics are equally well proven.

The pattern is becoming consistent: expose a modern shortcut or surface, but route it into the same authoritative game machinery instead of cloning game rules in the host.

### Product breadth expands around the same ownership rule

Earlier October 5 work had already added first-run help and authoritative Quick Practice (PR #466 plus the later 45-course routing probe), giving ordinary users a compact way to learn controls and enter real stock-initialized practice without contaminating progression, records or ghosts.

Packaging also crossed an important threshold. PR #493 established a validated Windows x64 portable ZIP/folder package that boots correctly from an unrelated working directory. PR #504 later rescued the startup-diagnostics contract. The next packaging lane is therefore lifecycle work, not “make a ZIP”: mutable user data needs a clean durable home outside immutable package contents, and diagnostics/settings/profile/run persistence must continue to work after ordinary consumer relocation and relaunch.

Local multiplayer took a similar contract-first route. Separate conversations established deterministic P1/P2 assignment, duplicate rejection, reconnect/reassignment rules, launch eligibility and stock 2P authority. The useful pieces were rescued into PR #503.

Controls rebinding followed the same pattern. PR #498 landed the framework-authoritative rebind model. A later product-integration pass opened PR #512 to wire that model through the visible Modern Controls surface using SNESRecomp's actual keybind/save authority.

### Modern progression moves from policy to stock-authoritative implementation

Challenge tiers were deliberately treated as a Modern policy layer around the stock generator rather than a replacement progression engine.

PR #491 locked the Bronze/Silver/Gold policy. PRs #492, #496, #499 and #501 progressively identified and wrapped the real stock challenge-generation/writer/award seams. PR #502 then rescued the selected-tour challenge-completion lifecycle into main.

This is the same architectural discipline seen elsewhere in the project: host-side product logic may choose, present and persist policy, but canonical gameplay state transitions should remain the guest's job whenever the stock game already owns them.

### Uniracers / Unirally becomes a presentation feature instead of a second game

A new conversation asked whether typing `NTSC` or `PAL` on the title screen could switch between Uniracers and Unirally presentation. The idea expanded into a secret controller-accessible switch with persistent regional preference where platform storage allows it.

PR #500 added the regional presentation substrate. PR #508 documented a stock-style animated transition, preferring the game's own horizontal title movement vocabulary and keeping the effect presentation-only rather than rebooting or retiming the guest.

The scope remains intentionally narrow: preserve one authoritative simulation and switch the player-visible regional presentation where the retail versions actually differ.

### Racer HD work changes its selection rule

The first Racer HD family is no longer being expanded by sprite adjacency or generic archaeology. The new instruction is empirical: measure Original↔HD fallback frequency during representative ordinary play, rank unsupported states by actual player-visible burden and implement the highest-value missing presentation family first.

This is a meaningful maturation of the HD pipeline. Semantic selection, equivalence, temporal coherence, review packets and shipping-readiness machinery now exist. The question is no longer “what sprite comes next?” but “what missing state is the player actually seeing most often?”

At the moment this diary was first captured, that measured-coverage lane had only just started and had not yet produced a new PR.

**Retrospective, October 6:** the selection rule worked. The lane produced a sequence of bounded, review-gated additions chosen by observed fallback burden rather than ROM adjacency, moving the broader ordinary-play census from 118/5282 HD selections (2.23%) to 653/5282 (12.36%) by the 01B9 slice. The useful process result was not merely the extra art. Once the agent was given a quantitative work-selection oracle, it stopped spending context on deciding what looked promising and could iterate through measure → author → review → hash-bind → remeasure with comparatively little supervision.

### CI briefly becomes the product's biggest scalability bug

The day's ugliest symptom was 108 active or queued Actions runs from only a few agents.

The first pass fixed trigger overfire and reconciled useful stranded work. PR #505 stopped planning/deferred-platform changes from waking expensive validation. PR #506 fixed a stale framework patch digest that could poison many native workflows at once.

The user then explicitly asked for an aggressive second pass: not merely “are these workflows coded correctly?” but “do they still deserve to exist automatically?”

PRs #507, #509 and #510 pruned or manualized completed research, deferred Switch work, closed Widescreen probes, archaeology/reference jobs and other obsolete automatic workflows. Native UI acceptance was collapsed around shared build work where possible. The repository stopped treating every historical experiment as a permanent regression service.

PR #511 made that cleanup durable by updating agent and CI/operations/hygiene guidance with creation, trigger, maintenance and retirement rules.

This is an important production lesson. In an agent-heavy repository, CI is a shared compute product. A workflow can be perfectly implemented and still be wrong to run automatically.

### End-of-day state

By late October 5, the repository had no meaningful orphaned work left from the CI reconciliation sweep, and current `main` had reached `74040131...` after PR #511. PR #512 then opened for full player-facing Controls rebinding.

### Overnight follow-through and a warning from the next day

Several October 5 “next lanes” became merged product work within hours. Resume/Restart Tour moved from policy into a player-facing confirmed flow; the regional secret gained its first exact retail Unirally title consumer; local multiplayer gained an independent source-aware join overlay; portable state moved into a durable per-user root; and Racer HD began climbing its measured fallback ranking.

That velocity came with a sharp caveat. The repository had become capable of generating changes faster than its integration machinery could cheaply validate them. Session stalls were survivable because agents had been told to commit often, update owning docs and leave bounded branches that another session could rescue. CI stalls were more dangerous because shared framework patches, generated snapshots and broad workflow assertions turned otherwise independent work into hidden coupling. The October 6 cascade would make this the next major engineering problem.

The project has crossed another boundary. The major remaining Windows work is now recognizable consumer-product work:

- finish the visible Controls rebind lifecycle;
- turn portable packaging into a durable user-data/update lifecycle;
- continue Racer HD by measured fallback burden rather than archaeology;
- keep filling the Modern root/progression/multiplayer/records surfaces using stock-authoritative state transitions;
- continue pruning CI whenever a completed research lane tries to fossilize into a permanent tax.

The most striking change after one week is that the repo no longer needs a single serial “critical path.” The hard-won semantics are strong enough that multiple product leaves can proceed in parallel, provided each agent respects ownership boundaries and the CI machinery remains small enough to let that parallelism breathe.
