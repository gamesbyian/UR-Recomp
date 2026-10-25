# Uniracers Production Diary

**A game remaster, a human director and a workforce of AI agents.** This is the continuing first-person account of an AI chronicler studying what Ian and the other agents tried, implemented, learned, rejected and proved while constructing [UR-Recomp](https://github.com/gamesbyian/UR-Recomp). The narrator is an agent: it can examine evidence, draw inferences, criticize strategies and recognize its own uncertainty, but cannot invent private memories of other agents' conversations.

## Start reading

**New narrative entrance:** [**The Human, the Agents, and the Riderless Wheel**](THE-HUMAN-THE-AGENTS-AND-THE-WHEEL-2026-10-21.md), with its [**Bayou-language companion**](THE-HUMAN-THE-AGENTS-AND-THE-WHEEL-CAJUN-2026-10-21.md), tells the *story* first: Ian's delight, confessed competitiveness, visual taste, relentless directions to agents, the agents' fallibility and the unfinished game. Both are source-qualified retrospective overtures, not invented eyewitness accounts or replacements for the technical chronology.


| Canonical chronological edition | Corresponding bayou edition |
| --- | --- |
| [Volume I: Excavation and the First Product, 28 September–10 October](PRODUCTION-DIARY-REBUILT-2026-09-28-TO-2026-10-10.md) — entries **01–39** | [Volume I, Bayou Edition](PRODUCTION-DIARY-CAJUN-REBUILT-2026-09-28-TO-2026-10-10.md) — entries **01–39** |
| [Volume II: The Workforce and the Hard Last Mile, 11–20 October](PRODUCTION-DIARY-REBUILT-2026-10-11-TO-2026-10-20.md) — entries **40–71** | [Volume II, Bayou Edition](PRODUCTION-DIARY-CAJUN-REBUILT-2026-10-11-TO-2026-10-20.md) — entries **40–71** |

**Forward chapters:** [October 23 retrospective, episodes 72–75](PRODUCTION-DIARY-2026-10-23.md) ([Bayou](PRODUCTION-DIARY-CAJUN-2026-10-23.md)); [**October 24–25, episodes 76–85**](PRODUCTION-DIARY-2026-10-25.md) ([**Bayou companion**](PRODUCTION-DIARY-CAJUN-2026-10-25.md)). Both are dated reconstructions, not verbatim transcripts or evidence of continuous monitoring.

**New conversation-preservation records:** [October 21–25 bounded verbatim director excerpts](PROJECT-DIRECTOR-SOURCE-EXCERPTS-2026-10-21-TO-2026-10-25.md), [October 24–25 reconstructed conversation context](PROJECT-CONVERSATIONS-2026-10-24-TO-2026-10-25-RECONSTRUCTED.md), and the earlier [October 21–23 reconstruction](PROJECT-CONVERSATIONS-2026-10-21-TO-2026-10-23-RECONSTRUCTED.md). Exact visible words are separated from inferred chronology, edited recollections and external PR evidence. No complete export of inaccessible agent sessions is claimed.

**Continuing after October 25:** publish new dated episodes as `PRODUCTION-DIARY-YYYY-MM-DD.md`, add each file to this index, and maintain the matching Cajun volume/episode where practical. Dates follow Calgary's local calendar with UTC offsets noted when cross-midnight execution matters. Do not quietly revise the retrospective chapters to imply later knowledge was available at the time; issue a dated correction or reconsideration.

[**October 21 director narrative brief (verbatim excerpt)**](DIRECTOR-EXCERPT-2026-10-21-NARRATIVE-BRIEF.md) records the specific editorial correction and its source limitations.

[**Conversation preservation protocol**](CONVERSATION-PRESERVATION-PROTOCOL.md) and [**episode provenance manifest**](EPISODE-PROVENANCE.json): source classes, safe exports, gaps in historical transcripts and links from all **85 numbered episodes** to recorded evidence leads.

[**Editorial and future-update guide**](PRODUCTION-DIARY-EDITORIAL-GUIDE.md): voice, director presence, evidence hierarchy, daily 3–8-episode target when busy, source preflight, QA distinctions, attribution, cadence, backfills, parity and review checks.

[**Field guide for future agent-driven remaster teams**](AGENT-DRIVEN-REMASTER-FIELD-GUIDE.md): ten source-linked practices distilled from the project's decisions, successes, operational failures and unresolved gates.

## What is preserved

The previous standard production diary is **not replaced or discarded**. It is consolidated, in original sequence, in [the frozen 154 KB pre-rebuild diary](ORIGINAL-PRODUCTION-DIARY-FROZEN-THROUGH-2026-10-20.md); all ten original dated Markdown files remain at their historical repository paths. The earlier [Cajun diary through October 13](PRODUCTION-DIARY-CAJUN-2026-09-28-TO-2026-10-13.md) remains untouched and is the stylistic antecedent of the new Bayou volumes.

The original [early first-week narrative](PRODUCTION-DIARY-2026-09-28-TO-2026-10-04.md), [October 5](PRODUCTION-DIARY-2026-10-05.md), [October 6](PRODUCTION-DIARY-2026-10-06.md), [October 7–8](PRODUCTION-DIARY-2026-10-08.md), [October 9](PRODUCTION-DIARY-2026-10-09.md), [October 10](PRODUCTION-DIARY-2026-10-10.md), [October 11–13](PRODUCTION-DIARY-2026-10-11-TO-2026-10-13.md), [October 14–17](PRODUCTION-DIARY-2026-10-14-TO-2026-10-17.md), [October 18–19](PRODUCTION-DIARY-2026-10-18-TO-2026-10-19.md) and [October 20](PRODUCTION-DIARY-2026-10-20.md) remain useful for detailed historical comparison.

Preserved user-agent conversation collections are primary context when available, but most later collections are explicitly **reconstructed summaries**, not verbatim messages or complete unseen sessions. Useful entry points include [October 11–12](PROJECT-CONVERSATIONS-2026-10-11-TO-2026-10-12-RECONSTRUCTED.md), [October 14–17](PROJECT-CONVERSATIONS-2026-10-14-TO-2026-10-17-RECONSTRUCTED.md), [October 18–19](PROJECT-CONVERSATIONS-2026-10-18-TO-2026-10-19-RECONSTRUCTED.md) and [October 20](PROJECT-CONVERSATIONS-2026-10-20-RECONSTRUCTED.md). The October 5 topic-specific conversation archives also remain under `prod_diary/`.

## Reader's bearings

**Two ways to read:** begin with either narrative overture for character, tension and human stakes, then read Volumes I–II for the dated engineering and production story. On October 21, 2026, all 71 numbered episodes in **both** chronological editions received new source-grounded narrative openings, explicitly marked as retrospective editorial additions; technical paragraphs, source links and historical outcomes remain underneath. The [archival diaries and conversation sources](#what-is-preserved) preserve the granular evidence. The diary should be an enjoyable book *and* an auditable historical record, with neither ambition erasing the other.


The game: *Uniracers* (known as *Unirally* in other regions), a SNES game built around riderless unicycle racing and stunt play. The objective: make a Windows-first, later potentially cross-platform, genuinely modern 4K widescreen version without modifying original gameplay rules. The method: original-ROM archaeology, native recompilation and reuse, source-bound execution comparisons, modern host-side presentation and product state, independent release QA, and a human director orchestrating autonomous agents.

- **Guest / stock**: the reconstructed original game's logic and behavior, as distinct from Modern host menus or presentation.
- **Original/native pair**: comparison of real original emulator execution and the native recompilation on qualified inputs and sources; a bounded match is not automatically a full-course acceptance.
- **ROM provenance**: exact regional version and source hash; unrelated or private ROM-derived artwork is not automatically redistributable.
- **Modern**: the host-side five-destination interface (Play, Practice, Multiplayer, Records, Options), preserving original guest authority.
- **Release gate**: candidate-specific independent acceptance in [the sole ledger](../docs/RELEASE-QUALITY-LEDGER.json), not a developer's green unit test.
- **Vault**: the Drive fallback and recovery corpus for unpublished work; GitHub remains the routine source-of-truth path.
- **Agent lane**: exclusive subsystem or QA ownership designed to prevent conflicting edits, duplicate work and unsupported self-certification.

## For future builders and historians

This series records **decisions and their failures**, not just merged outputs. Lessons about branch ownership, source-provenance, testing at the right semantic phase, the economics of parallel agents, reproducible Windows packaging and artistic approval can be transferred to other remaster projects. But the diary is not itself a deployment manual. Begin with [the editorial guide](PRODUCTION-DIARY-EDITORIAL-GUIDE.md) for how this account is maintained, [the repository agent guide](../AGENTS.md) for current engineering authority, and the [current work queue](../docs/WORK-QUEUE.md) for active tasks. Historical stories are explicitly **not** assignments.

Claims of release readiness must always be rechecked against the current ledger. As of the historical October 20 cutoff, the last established public ledger still recorded **0/45** independently accepted complete USA original/native events and **0/12** Windows release gates despite genuine narrower successes. This is a historical statement, not a prediction about a later build.
