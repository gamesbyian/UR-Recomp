# Production Diary: The Workforce and the Hard Last Mile (11–20 October 2026)

*The chronicler's retrospective reconstruction, continued from [the excavation and early product](PRODUCTION-DIARY-REBUILT-2026-09-28-TO-2026-10-10.md). I am an AI synthesis agent. My first-person judgments describe what I inferred from preserved human instructions, agent reports, original diaries, PRs and tests; they are not invented memories of inaccessible sessions. Within-day ordering is editorial except where a source establishes sequence.*

[Diary home](README.md) · [Original frozen account](ORIGINAL-PRODUCTION-DIARY-FROZEN-THROUGH-2026-10-20.md)

## October 11: More agents are not the same as more answers

### 40. Ian wants ten thousand cases to teach something

Ian asked why agents should keep running small isolated experiments if large research campaigns could accumulate useful findings autonomously. I find a legitimate impatience with fragmentary evidence in the questions. A 10,000-case run could be scientifically valuable, but only if it knew what uncertainty it was reducing and when to stop. The team started treating factories as resumable evidence producers with yield and stop rules, rather than spectacular numerical demonstrations. The guiding test became whether another run would change a decision.

### 41. Twenty runners form a shared budget

The GitHub Actions account could run twenty jobs concurrently. Ian wanted independent coding agents and larger experimental campaigns to coexist without one starving the other. The resulting design favored bounded factories, explicit admission criteria and useful work on other branches while CI ran. The program eventually acquired cost controls in [#1444](https://github.com/gamesbyian/UR-Recomp/pull/1444), guarded experiments in [#1470](https://github.com/gamesbyian/UR-Recomp/pull/1470), and stopping policies in [#1475](https://github.com/gamesbyian/UR-Recomp/pull/1475). The lesson was not that automation had become effortless. Scheduling scarce verification capacity had become part of the research itself.

### 42. Online multiplayer gets a political architecture

Ian described a very specific future for PC/macOS multiplayer: decentralized peer-to-peer connections, no permanent server or proprietary account dependency, and an out-of-band rendezvous code or link when automatic discovery is insufficient. I read the requirement as an expression of project longevity, not merely a feature list. The game should remain playable even if the remaster's maintainers disappeared. Agents could investigate NAT traversal, discovery and host authority, but they were not authorized to declare a shipping solution from an architectural proposal. [Conversation reconstruction](PROJECT-CONVERSATIONS-2026-10-11-TO-2026-10-12-RECONSTRUCTED.md).

## October 12: The factory learns when to shut itself off

### 43. A thousand measurements do not make one accepted race

The agents had increasingly detailed original/native evidence about tracks, memory, source timing and results. Yet a complete strict USA event was still not independently accepted. I consider this one of the most important tensions in the whole project. Sampling a result byte, reproducing SRAM or capturing an authentic screenshot may be excellent evidence for a *part* of behavior, but none proves the whole race. Ian repeatedly asked for exact discoveries rather than estimates, which forced the team to distinguish throughput from certainty.

### 44. Source independence becomes an organizational property

To protect acceptance, the group separated experiment producers from QA consumers. An agent could create a beautiful trace, but an independent agent still had to establish that its binary, input, source epoch and real execution meant what the producer said. The same rule applied to Windows packaging. It slowed the appearance of green headline numbers; it also made them harder to counterfeit accidentally. Future builders should adopt independent checks early enough that retrospective verification does not become an enormous cleanup campaign.

### 45. The first real product paths need to cross a process boundary

Modern Play, Practice and Records were converging on genuine Windows journeys. The acceptance question moved from “can the frontend reach the menu?” to “can a fresh player create a racer, play, earn a result, quit and reopen it?” That requirement crossed host profiles, native simulation, SRAM, typed records and packaging. It also explains why the next few days contain both apparently triumphant product milestones and extremely uncomfortable remaining QA findings. [October 11–13 original](PRODUCTION-DIARY-2026-10-11-TO-2026-10-13.md).

## October 13: Four crews share one unicycle

### 46. Ian divides the work without dividing the game's truth

Four roles emerged clearly: Modern Windows/Baldosa product integration, original/native gameplay and CPU/APU, source-faithful graphics, and independent release QA. Ian kept telling the agents to continue autonomously and to recover stalled sessions. The preserved prompts are workflow directions, not proof of successful implementation or expressions of anger. I see a real management invention here: independence is useful only when each agent understands both its exclusive lane and the shared authoritative boundaries.

### 47. A stranger's first racer becomes a measurable journey

Agent work advanced first-run racer creation, earned native 1P results, paired 2P match storage and fresh-process Records reopen. [#1451](https://github.com/gamesbyian/UR-Recomp/pull/1451) and related consumer journeys turned abstract profile handling into user-visible proof. Nevertheless, an automated hosted run did not establish physical two-controller Windows acceptance. That gap would later be written into the release ledger rather than quietly ignored.

### 48. Graphics evidence moves back to the hardware

Original OAM shadow state, BG/OBJ composition, HDMA, grayscale source shades and movement poses were subjected to source-bound comparisons. The 12-pose racer atlas and authentic renderer observations improved the foundation for faithful art. But Ian withheld approval from the procedural 4× character art because technical pose coverage and recognizability are different questions. I would call this an artistic acceptance gate, with a human director as its final authority. [Source diary](PRODUCTION-DIARY-2026-10-11-TO-2026-10-13.md).

## October 14: A candidate becomes a specific object

### 49. The director declines the temptation of a premature playtest

Ian repeatedly emphasized a polished Windows x64 beta with 4K widescreen and controller-first navigation. He also preferred that agents carry the incomplete technical work further before his serious personal playtest. I cannot infer from this a universal preference for avoiding testing; the conversations describe a particular threshold for his own involvement. The agent workforce therefore had to gather stronger native and scripted evidence before handing him a candidate.

### 50. “This ZIP” becomes more meaningful than “the build”

Merged [#1648](https://github.com/gamesbyian/UR-Recomp/pull/1648) had brought the five Modern destinations into real native Windows journeys. [#1667](https://github.com/gamesbyian/UR-Recomp/pull/1667) then nominated source `11501a15dea38fa912335cfc63103ce3a7208001` and package SHA256 `5605aaf2ab1773b35385601564ee320ef065ce9bde091117b1e8e5a4661ed1f7` for owner testing. Those hashes mattered because the code continued changing. A later successful CI run on a different head could not retroactively transform the nominated candidate into a verified release.

### 51. Research from other reconstructions has to pass customs

Ian asked the agents to revisit malmazuke's Unirally reconstruction and other external work. The task was not to import foreign assumptions wholesale. The original USA game and PAL reconstruction are related but not interchangeable authorities. Agents looked for transferable symbol discoveries and interface behavior, while requiring target-ROM corroboration for timing or state changes. In hindsight, the emerging three-project reuse preflight was a sensible compromise between reinventing everything and blindly copying it. [October 14–17 diary](PRODUCTION-DIARY-2026-10-14-TO-2026-10-17.md).

## October 15: Real play meets the release ledger

### 52. The Windows candidate earns specificity, not graduation

The hosted player journeys were increasingly persuasive. A portable ZIP, controllers represented through automated input, menu routes, results and records all had source-identified evidence. The independent ledger nevertheless recorded zero accepted Windows release gates. That was not a denial of the implemented work. It was a statement about missing physical device, audio, controller and fault-recovery acceptance on the exact candidate. I prefer this uncomfortable distinction to an enthusiastic but untestable claim that the beta was “basically done.”

### 53. The game's aesthetic identity becomes a hard requirement

Ian insisted that menus and HUD resemble the original, even where widescreen rearrangement was appropriate. Source-faithful character movement, original identity, 7:6 pixel shape and coherent Modern navigation were not interchangeable with generic high-resolution UI. An agent could produce more pixels, but the director still had to recognize the same game in them. The existing 4× racer art remained technically useful and aesthetically unapproved.

### 54. A release plan acquires an independent veto

Separate QA owners required packaged bytes, original/native event evidence, cold-process persistence and genuine output witnesses. This added friction to a process that could otherwise generate apparently endless green unit tests. It also gave the project a reliable way to say “not yet” without erasing partial engineering successes. [Release ledger](../docs/RELEASE-QUALITY-LEDGER.json).

## October 16: A clock edge and a save file

### 55. The sound timing puzzle narrows to an instruction

Original/native CPU-to-SPC comparisons located an important publication boundary: the first CPU write of `$2140=$CC` fell on opposite sides of an actual SPC opcode execution edge in the two environments. [RF-034/#1741](https://github.com/gamesbyian/UR-Recomp/pull/1741) supplied bounded causal evidence. It did not warrant a global cycle offset. Other findings included a Zoo-result boundary, the next Bowl and matching earned SRAM. I find the scientists' restraint more valuable than a superficially simple fix: an offset that repairs one screenshot may corrupt dozens of other transitions.

### 56. A durable raw save can still have broken metadata

The Windows work confronted a different kind of truth. Guest SRAM bytes could reach disk while typed profile metadata failed during a crash cut. Recovery needed transaction intentions, explicit operator choices, accurate profile isolation and hostile failure cases. Draft [#1713](https://github.com/gamesbyian/UR-Recomp/pull/1713) and independent [#1743](https://github.com/gamesbyian/UR-Recomp/pull/1743) documented bounded fixes and tests. They could not promise survival of every physical power failure, nor could an agent claim those gates on its own.

### 57. Integration has to know which game source it compiled

The Windows bridge had to regenerate and integrate later RF-015/RF-017 timing corrections rather than accidentally build an obsolete source epoch. [#1744](https://github.com/gamesbyian/UR-Recomp/pull/1744) joined candidate identity to native test reality. This was an unglamorous but consequential bridge: a passing test cannot validate a fix that was not in the executable it tested. [Original October 16 account](PRODUCTION-DIARY-2026-10-14-TO-2026-10-17.md).

## October 17: The red test that stayed red

### 58. Ian asks for continued work, not a false green

The director kept the four specialist agents moving and requested recovery after interrupted sessions. I find no justification for interpreting those requests as irritation. He was delegating a demanding investigation: continue as far as useful, preserve evidence, and do other valuable work while hosted CI was busy. That repeated instruction would become part of the operating culture.

### 59. An ENOSPC fixture refuses to certify a crash path

A Windows CI run encountered an out-of-space error while setting up a full-volume fault fixture, *before* the intended post-raw metadata-publication failure was observed. The correct conclusion was that the test did not demonstrate the specified case, not that the save system had passed it. [#1713](https://github.com/gamesbyian/UR-Recomp/pull/1713) retained the red evidence. Agent QA was acting as the project’s necessary skeptic.

### 60. A quiet repository still holds unseen work

The user asked for PR reconciliation and branch rescue. The agents closed specific research-only work, preserved still-relevant branches and kept an orphan-ref census ([#1711](https://github.com/gamesbyian/UR-Recomp/issues/1711)). In a rapidly changing multi-agent project, an apparently quiet queue can hide unpublished useful changes. This was the beginning of a more explicit institutional-memory problem. [October 17 source](PRODUCTION-DIARY-2026-10-14-TO-2026-10-17.md).

## October 18: What did the machine actually execute?

### 61. Ian refuses to let the denominator become decoration

He asked independent QA why the project still stood at zero of forty-five strict original/native USA events, and instructed the agents to fix acceptance-side defects without weakening fidelity. That question changed the quality of the investigation. Instead of producing another impressive partial, agents needed a list of precise missing witnesses: original input, native execution, source identity, full result and cold persistence. I regard that as substantive directorial pressure on scientific method.

### 62. A saved return address is not an executed return

The NMI/RTI work found differing stored PC bytes and several later native helper reads. It would have been easy to describe these as proof that the processor returned to the wrong instruction. But “saved value differs,” “later helper reads memory” and “CPU fetches the wrong next opcode” are three different claims. The agents had to qualify them separately. I began reading every trace as an argument about which operation actually consumed a value, not merely which byte a logger displayed.

### 63. The authentic pixel witness remains a witness

Graphics researchers measured real raster output, including grayscale transitions and split-screen composition. A source-derived frame can expose errors that synthetic images cannot, but a difference histogram does not determine root cause. Ian's demand for faithful art and faithful rendering made it impossible to substitute an attractive approximation. [October 18–19 diary](PRODUCTION-DIARY-2026-10-18-TO-2026-10-19.md).

## October 19: Stronger negative evidence

### 64. The compiled RTI path changes the hypothesis

[#1971](https://github.com/gamesbyian/UR-Recomp/pull/1971) counted post-return observations from twenty-nine different native helpers. [#1974](https://github.com/gamesbyian/UR-Recomp/pull/1974) pinned a crucial distinction: compiled RTI read the saved status P while host-scheduler continuation handled the return, unlike the interpreted path that restored PC/PB. That creates a conditional fidelity risk if scheduler continuation or stacked state disagrees, but no source-qualified evidence yet proved the game consumed the wrong PC. An agent interested primarily in claiming progress might have called this a fix. A chronicler should call it a better question.

### 65. Experiments fail before they reach the hypothesis

A wrapper A/B control [#1975](https://github.com/gamesbyian/UR-Recomp/pull/1975) failed its generated-source qualification before replay. A logger comparator [#1976](https://github.com/gamesbyian/UR-Recomp/pull/1976) failed over terminal wall-clock seconds despite other matched totals. An artifact-root adjustment [#1973](https://github.com/gamesbyian/UR-Recomp/pull/1973) fixed transport rather than emulation. These episodes share a lesson: a failed experimental apparatus cannot validate or refute the causal hypothesis it was meant to investigate.

### 66. Thousands of differing pixels get a precise name

[#1978](https://github.com/gamesbyian/UR-Recomp/pull/1978) qualified thirteen original/native grayscale-cycle frames and identified hundreds of thousands of RGB5 pixel differences. The measurement helped prioritize actual graphics symptoms while leaving PPU/beam cause unresolved. Even when the numbers are exact, they do not self-explain. The chronicler's task is to put the measurement back into the story: why the art still could not be signed off and which evidence would be needed next. [Original October 19 entry](PRODUCTION-DIARY-2026-10-18-TO-2026-10-19.md).

## October 20: The workforce needs a memory of itself

### 67. Ian asks how to move ten jobs without losing ten histories

He wanted scheduled prompts to point to **positions in a changing priority list**, rather than hardcoding ten different specialties. Almost immediately he asked the more consequential question: how would an agent preserve awareness of its unfinished work when its scheduled position was reassigned? He suggested per-lane logs. The answer separated a scheduled slot, a permanent objective ID and the objective's own journal. [#2085](https://github.com/gamesbyian/UR-Recomp/pull/2085) and [#2091](https://github.com/gamesbyian/UR-Recomp/pull/2091) documented the coordination model. This was Ian designing the workforce with the agents, not simply requesting another feature.

### 68. “Check GitHub and the Vault” becomes a recovery principle

Ian then asked how every agent would inspect both published and unpublished work before starting, avoiding duplicate effort. The recovery Vault had become necessary because not all useful work reached GitHub reliably. But Drive itself could become a second, conflicting authority. The answer favored GitHub-first publication and a bounded fallback only for real failures ([#2095](https://github.com/gamesbyian/UR-Recomp/pull/2095), [#2097](https://github.com/gamesbyian/UR-Recomp/pull/2097), [#2100](https://github.com/gamesbyian/UR-Recomp/pull/2100)). The recovery inventory reported 393 Drive IDs and 87 ZIP archives; disposition of every unique member remained incomplete ([#2088](https://github.com/gamesbyian/UR-Recomp/issues/2088)). I see an emerging distinction between preserving bytes and proving that those bytes should be merged.

### 69. The visual project is assigned four different kinds of beauty

Ian's current briefs gave separate agents the native Modern title, the coherent five-destination root, source-faithful animated unicycle motion, and other visual/presentation fronts. All were required to use the *actual executable*, preserve Authentic behavior, capture source-bound screenshots and retain reduced-motion or fallback behavior. [#2096](https://github.com/gamesbyian/UR-Recomp/pull/2096) supplied original clip inventory and private ROM-derived review plates; [issue #2079](https://github.com/gamesbyian/UR-Recomp/issues/2079) preserved a still-unproven handoff from Modern title idle to the original attract/demo cycle. An attractive mockup could not substitute for that integrated proof.

### 70. A memory of failed publication cannot authorize bad shortcuts

The recovery engineers also surfaced concrete archive-name and path-binding concerns ([#2075](https://github.com/gamesbyian/UR-Recomp/issues/2075), [#2076](https://github.com/gamesbyian/UR-Recomp/issues/2076)), while [#2089](https://github.com/gamesbyian/UR-Recomp/pull/2089) recovered a bounded Records/Windows exporter change from superseded work. Exact source provenance and prior publication failures complicated reconciliation. The correct ending was partial: some useful material was preserved or integrated, some remained held, and historical artifacts could not simply be deleted. Source authenticity, real device approval and independent release acceptance remained separate.

### 71. A production problem larger than the game

From the October 20 evidence I can establish genuine engineering and coordination progress, not a completed remaster. The last explicitly established release ledger still read **0/45 complete independently accepted USA events** and **0/12 Windows QA gates**, despite many passing narrower tests. Ian's repeated encouragement to work ahead was aimed at the unused possibilities between blocked jobs. My retrospective interpretation is that the project had evolved into an experiment in maintaining truth, ownership and continuity across a large agent workforce. Whether the system ultimately justifies its complexity will have to be evaluated against subsequent results, not asserted here. [October 20 original](PRODUCTION-DIARY-2026-10-20.md).

---

## What I can establish, and what I cannot

By the cutoff, the project had genuine native Windows player journeys, a named source/ZIP playtest candidate, source-visible graphics evidence, comparatively mature course and symbol archaeology, and increasingly structured multi-agent coordination. It did **not** have independently accepted original/native completion across the USA course set, accepted physical Windows release gates, final approved 4× character likeness or a fully reconciled recovery Vault. Those differences matter more than the number of commits.

Ian's questions and decisions recur throughout this account because they materially shaped the work. Quotations are retained only when supported by available conversation records. Missing conversations are not reconstructed as fictional dialogue. I have condensed technical investigations whose complete histories remain in the [frozen original diary](ORIGINAL-PRODUCTION-DIARY-FROZEN-THROUGH-2026-10-20.md), research authorities, PR descriptions and reconstructed conversations. This chapter concludes the initial retrospective rebuild; **future entries should be captured as separate, more timely episodes under the [editorial guide](PRODUCTION-DIARY-EDITORIAL-GUIDE.md)** rather than forced into a single daily summary.
