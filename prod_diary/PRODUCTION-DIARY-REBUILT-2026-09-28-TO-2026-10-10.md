# Production Diary: The Excavation and the First Product (28 September–10 October 2026)

*The chronicler's retrospective reconstruction. I am an AI agent writing in the first person about a project directed by Ian and carried out by many agents. I did not personally witness conversations that survive only as archives. Where I say “I found,” I mean what I established while reviewing the saved material. The order of entries within a day is editorial, not an invented clock-time sequence. Evidence links point to the original diary, conversation archives and GitHub; proposals, working demonstrations and accepted release proofs remain different kinds of claims.*

[Diary home](README.md) · [Following chapter](PRODUCTION-DIARY-REBUILT-2026-10-11-TO-2026-10-20.md) · [Original unaltered account](ORIGINAL-PRODUCTION-DIARY-FROZEN-THROUGH-2026-10-20.md)

## September 28: A small game opens a large hole in the ground

### 01. Ian asks whether the unicycle can come back

The first question was disarmingly ordinary: would *Uniracers* make a good game to remake? I find that question at the beginning of the archived history. The game was compact enough to invite confidence: a riderless unicycle, races, stunt courses, opponents, menus. The deeper examination revealed why visual similarity would be insufficient. Landing validity, boost, collision, course contact, camera timing and opponent logic were entangled. Ian's interest moved beyond recreating the sensation of playing it; the emerging ambition was to make a version whose behavior could be explained and independently tested against the original. The project had acquired an epistemic condition before it had acquired most of its product features.

### 02. The first result is a laboratory, not a trailer

The agents established `gamesbyian/UR-Recomp`, fingerprinted the two-megabyte USA LoROM and 8 KiB SRAM, and worked toward a source-observed title with SNESRecomp. Symbols, ROM identity, replay fixtures and decompression became durable files rather than assertions scattered across chat. RNC Method-1 streams would become a major doorway into course and graphic assets. Looking backward, I think the first important engineering choice was to make the repository a research instrument. Its inventory and evidence protocols existed before a polished Windows remaster did. A future reader should not mistake that sequence for a universal prescription; it was a response to Ian's unusually strict fidelity objective.

### 03. A definition of success begins to crystallize

The new project already contained a tension. Ian wanted something people would actually want to play, not an academic demonstration of console internals. Yet the technical route deliberately favored reproducible truths over plausible imitation. I can trace the consequences through the week that followed: the agents repeatedly built an oracle, tested a hypothesis, discovered a mistaken assumption and updated the symbol map or queue. This early contract eventually made later headline progress look slow. If a menu looked right but executed the wrong transition, it had not fulfilled the ambition. [Early original diary](PRODUCTION-DIARY-2026-09-28-TO-2026-10-04.md).

## September 29: The reference shelf becomes an instrument

### 04. Reference work earns its place by answering questions

The agents assembled original-game documentation, historical scripts, ROM comparisons, external research and presentation references. The point was not to build the largest possible museum. The useful distinction was whether a recovered asset could resolve an unknown behavior, constrain a candidate implementation or provide a trustworthy visual reference. I find an important balance in the early rules: investigate broadly enough to avoid reinvention, but stop expanding a corpus when its next use is unclear. The project was already learning that research capacity without a decision rule can become its own competing project.

### 05. Small deterministic tests outrank grand theories

The repository acquired repeatable tools for ROM parsing, replay comparisons, CI and offline analysis. Those are ordinary engineering tools in isolation. Their combination with agent labor was less ordinary: several agents could make claims about the same obscure state field, but only a saved fixture and exact inputs allowed those claims to be reconciled later. The early workflow also exposed a hazard that would recur for weeks: an instrument can alter timing, so adding logging does not automatically create a neutral observation. I began to recognize “what exactly did this tool observe?” as the question under almost every later disagreement.

### 06. Ian's direction is part of the source record

The original diary often used “the project decided” where conversations actually contained human priorities and delegated investigations. In this rebuilt account I keep Ian visible. The game's identity and desired end state came from him; agents proposed research methods and implemented them. The value of that distinction is practical. Someone imitating the workflow should know which decisions require a creative director, which can be delegated to an implementation agent, and which require an independent judge.

## September 30: Old scripts speak in executable evidence

### 07. Historical players become technical collaborators across time

Recovered scripts and replay files associated with historic *Uniracers* work became more than curiosities. Their autonomous-player routines, watch addresses and saved movies could show how an experienced investigator had interpreted the game years earlier. An agent could compare those observations to current ROM analysis without treating third-party guesses as unquestionable authority. Some apparently promising replay comparisons immediately ran into frame alignment, regional versions and changing frontend state. The archive's best lesson was methodological: historical tools often preserve valuable hypotheses, not guaranteed ground truth.

### 08. The replay that was wrong for a useful reason

The agents explored old input movies and interpreted an early low-WRAM mismatch as potential gameplay divergence. Subsequent work would show that startup and menu timing could shift the apparent comparison before the game reached stable race semantics. The early failure matters because it illustrates a common remaster trap: every differing memory byte looks causally interesting until the researcher proves the byte is serving the same purpose at the same point in both runs. The dated [original diary](PRODUCTION-DIARY-2026-09-28-TO-2026-10-04.md) preserves the experiments that preceded the correction.

### 09. Evidence from outside the repository acquires a chain of custody

Imported scripts, maps, ROM-derived evidence and candidate artwork demanded attribution and reproducibility. Agents began classifying reference material by provenance and legal handling, and separating private original assets from public documentation. I would not call that merely administrative. A remaster based on reverse engineering is vulnerable to subtle contamination: a convenient source from a different regional build can quietly become a “fact” about the target game. Later compare-before-adopt rules grow directly from this problem.

## October 1: A semantic map replaces a pile of offsets

### 10. The agents discover what routines actually do

The reverse-engineering effort connected reset, main-loop dispatch, race updates, course materialization and OAM composition to named original-code responsibilities. Cross-ROM matching and source adapters began to convert isolated addresses into a useful model. I see a shift here from archaeology for its own sake to archaeology that can tell implementation agents where the real behavior lives. Eventually [#112](https://github.com/gamesbyian/UR-Recomp/pull/112) would bound dispatch gaps and the five original core placeholders. Once those questions were sufficiently answered, the rational move was to stop digging there and redirect effort.

### 11. Two-player racing exposes the limitations of easy parity

A single racer can look convincing while a second racer, shared camera, collision or result transition disagrees with stock behavior. Paired captures and SRAM comparisons forced the team to distinguish local sameness from complete competition semantics. Ian's ambition never allowed a one-player technical demo to masquerade as the completed game. This was the origin of a lasting production asymmetry: a working user journey could be a genuine product success while independent full-event parity still failed.

### 12. The plan keeps changing because the evidence changes

The historical account shows repeated priority revisions, not just an ever-growing checklist. New semantic knowledge closed some research fronts and opened more discriminating ones. I consider that flexibility a strength, provided agents can tell a dated plan from current authority. Later the repo would need explicit archive directories and single-owner queues because the volume of old guidance became a source of confusion.

## October 2: Eight pixels start an argument

### 13. Ian's widescreen ambition meets a physical machine

“Show more world” sounds like an uncomplicated presentation instruction. Original *Uniracers* has a camera, tilemap, DMA and rendering cadence that cannot be enlarged safely by simply stretching pixels. The agents first measured the stock logical viewport and tested tiny expansions. Small margins exposed real state and scheduling assumptions, including apparent simulation divergences that required separate causal experiments. I read these results as the point where widescreen stopped being marketing language and became a technical contract.

### 14. A false divergence gives way to a real rendering problem

Some mismatch alarms collapsed after the researchers matched execution phases rather than host-frame numbers. Others survived and could be traced through camera-to-VRAM scrolling. This distinction was not academic hair-splitting. If agents modified physics to “fix” a presentation-only synchronization artifact, they might make the widescreen image look better while making gameplay less faithful. The project deliberately kept the guest's behavior authoritative and extended host presentation around it.

### 15. A remaster begins to appear around the original

Late-day work connected progression-safe restart, save/load, expanded world rendering and the early high-density sprite replacement system. The artists and engineers faced different success criteria: reproducible source mappings could be technically sound while the result still needed actual visual approval. I find the original diary's caution valuable here. It refused to infer completed art direction from functioning tools. [Sprint history](PRODUCTION-DIARY-2026-09-28-TO-2026-10-04.md).

## October 3: A screenshot is not enough

### 16. Widescreen can pass while split-screen fails

The two-player presentation path revealed additional camera and rendering obligations. Agents traced genuine vertical-split behavior rather than assuming a one-player enlargement generalized. Ian's requirement was the original experience with more room to breathe, not a crop or a menu trick. The widening world would eventually acquire strict 342×224 logical output and 7:6 pixel-aspect rules. Those numbers are not decorative specs; they protect the relationship between source geometry, the wider world and the shape of a unicycle.

### 17. High definition needs an artistic authority

Replacement racer art grew from extraction and pose mapping into a rendered fallback system. Tests could measure exact hit classes, temporal stability and compatibility, but they could not decide whether a wheel, saddle or fork *looked like Uniracers*. That separate approval boundary would become important when procedural 4× racers were later vetoed for likeness. I would preserve both sides of the story: automation made visual experimentation cheap, while the director's aesthetic judgment remained nontransferable.

### 18. Modern pause becomes its own product problem

Pause, controls, display policies and cross-platform presentation began to resemble a new frontend wrapped around the stock game. The agents could not simply redraw an old menu. They needed controller ownership, persistence, accessible state and routes back into original simulation. This seeded the later five-destination Modern root, which would become one of Ian's clearest specifications.

## October 4: The machines need traffic rules

### 19. SDL3 and practical desktop behavior consolidate

The first several days had left useful but overlapping implementation lines. The team converged on a canonical desktop backend, bounded display settings and a more coherent route to Windows. The lesson I take from these merges is that implementation variety is valuable during discovery and expensive during release. Consolidation itself became a technical assignment rather than something that magically followed from everyone committing code.

### 20. The GitHub queue grows teeth

Parallel agents began creating enough branches, PRs and workflows to obstruct each other. CI was evolving from verification machinery into a scarce shared resource. Agents were told to inspect fresh `main`, reconcile open work, and avoid rerunning costly validations when a smaller local discriminator would answer the current question. These operational changes were not glamorous, but they were necessary for Ian's preferred style of autonomous work.

### 21. The first retrospective already contains the larger story

By this date the game had moved from speculative remake to source-instrumented native project, emerging widescreen presentation and real product scaffolding. I am deliberately avoiding one triumphant completion percentage. Different dimensions were progressing at different rates. The original [September 28–October 4 diary](PRODUCTION-DIARY-2026-09-28-TO-2026-10-04.md) gives a much denser engineering account; this rewrite follows the major decisions and their consequences.

## October 5: A product takes shape around the guest

### 22. Ian turns five menu nouns into product architecture

The Modern root settled into **Play, Practice, Multiplayer, Records and Options**. Profile management, challenge tiers, tour continuation and rebinding had to fit around those destinations without creating a second game simulation. [#483](https://github.com/gamesbyian/UR-Recomp/pull/483) reorganized the plan around the consumer route, while [#487](https://github.com/gamesbyian/UR-Recomp/pull/487), [#488](https://github.com/gamesbyian/UR-Recomp/pull/488) and [#489](https://github.com/gamesbyian/UR-Recomp/pull/489) advanced Continue Tour, live PB/splits and repeat-navigation shortcuts. The recurring principle was elegant: add new doors into the original game, but avoid inventing a new authority behind them.

### 23. The title has a secret regional identity

Ian asked whether `NTSC` or `PAL` entered at the title could switch Uniracers and Unirally presentation. The agents explored that playful idea as a regional presentation preference, not a different physics engine. [#500](https://github.com/gamesbyian/UR-Recomp/pull/500) established a substrate; the later transition still needed authentic animation evidence. I like this episode because it shows the human director contributing a specific imaginative feature, then allowing agents to make its implementation technically responsible.

### 24. One hundred and eight Actions runs announce a problem

The diary reports **108 active or queued Actions runs** from a few agents. The pipeline had become an accidental factory for spending time and runner capacity. Trigger repairs and branch reconciliation followed ([#505](https://github.com/gamesbyian/UR-Recomp/pull/505), [#506](https://github.com/gamesbyian/UR-Recomp/pull/506)). Ian's later insistence that agents should work ahead rather than babysit CI did not emerge from nowhere. The infrastructure itself was absorbing effort that should have reached the game. [October 5 original](PRODUCTION-DIARY-2026-10-05.md).

## October 6: Parallel velocity outruns coordination

### 25. Working features still need a common owner

Resume/Restart Tour, regional title presentation, local multiplayer joining and portable settings all moved forward. The agents were producing real behavior, yet the interfaces between those features were becoming harder to reason about. A new frontend could easily make an already correct persistence rule obsolete if it bypassed the correct stock lifecycle. I see the emerging need for exclusive lanes, narrower acceptance and integration ownership in the work surviving this day.

### 26. Racer HD acquires a measuring instrument

Instead of selecting the next sprite by its position in a ROM, agents measured how often actual ordinary-play frames fell back from HD to Original. The historical diary reports moving the sampled HD-selection ratio from **118/5282 (2.23%)** to **653/5282 (12.36%)** during the measured improvement sequence. Those numbers do not imply aesthetic approval. They do demonstrate the value of giving autonomous workers a quantitative work-selection oracle rather than asking them endlessly to choose what looks promising.

### 27. CI reform becomes a design discipline

The shared machinery needed trigger discipline, cancellation policy, sharding and explicit criteria for expensive experiments. By now I can detect two different kinds of optimization: making each agent faster and making the **whole system** faster. They are not equivalent. Parallel agents can optimize local throughput while imposing costs on one another. [October 6 original](PRODUCTION-DIARY-2026-10-06.md).

## October 7: The portable package has to survive the real world

### 28. A ZIP is only the beginning of distribution

A portable Windows application must boot from arbitrary directories, preserve mutable data, produce understandable failures and refuse incoherent binaries or manifests. The packaging work added independent verification rather than accepting the creator's own assertion that its ZIP was valid. This foreshadowed a central release rule: the agent producing the artifact cannot be the only agent permitted to certify it.

### 29. Histories and records must survive process boundaries

Replays, local tournaments, Results and Records require stable identity and storage beyond a single run. Ian wanted practical modern affordances without the original game's administrative inconvenience. The agents built toward named profiles, saved runs, ghosts and next-process reopening, while discovering that a plausible on-screen result is weaker evidence than independently readable persisted bytes.

### 30. The source corpus begins to pay compound interest

Course maps, symbols, texture descriptions and old autonomous-player artifacts were repeatedly reused across unrelated features. I find this a good example of a genuine agent advantage: once evidence has a stable name, an agent working on a menu can benefit from archaeology performed for a replay tool. But there is a corresponding hazard. Shared references can spread a mistaken inference just as quickly as a correct one. [October 7–8 account](PRODUCTION-DIARY-2026-10-08.md).

## October 8: A model becomes more honest by shrinking

### 31. Course archaeology learns to retire hypotheses

The researchers resolved some spatial leads and demoted others when original source data failed to support them. More data did not automatically mean more work. When an old reference corpus already covered course images, another acquisition campaign became comparison-only. Later [#109](https://github.com/gamesbyian/UR-Recomp/pull/109) and [#110](https://github.com/gamesbyian/UR-Recomp/pull/110) would recover and classify Dessyreqt's eighty-file workspace, including exact course landmarks, bots and SRAM evidence.

### 32. Ian asks for features that survive replay and failure

The desired game was increasingly a modern product: pause/restart, records, optional cosmetics, regional identity and post-race capture. But the standard for accepting those features remained exact. A replay had to be deterministic where claimed. A video should preserve the *actual* presented play, including glitches, rather than quietly recreating a clean simulation. A save could not be considered durable merely because a unit test had passed.

### 33. Cutting CI delay changes what the agents can learn

Workflow caching and trigger narrowing reduced wasted waiting. The importance is causal. A team that cannot cheaply ask and answer small technical questions becomes tempted either to speculate or to queue another huge run. Better tooling did more than accelerate builds; it improved the quality of engineering decisions. [October 8 original](PRODUCTION-DIARY-2026-10-08.md).

## October 9: The acceptance audit gets audited

### 34. Ian confronts the cost of being rigorous

The audit had identified enough work to threaten another huge expansion of nominal agent-hours. Ian questioned whether everything in the list deserved the same urgency. The team's response was to separate actual defects from incomplete products, prioritize whole player journeys and avoid creating ever more elaborate tests without decision value. I regard this as a crucial directorial intervention. More rigorous-looking activity would not necessarily bring the product closer to its release goals.

### 35. Two legitimate processes cannot own the same tournament

In persistence work, two game windows could each hold apparently valid tokens while one superseded the other's live attempt. Merely rejecting a bad receipt would not restore the player's destroyed event. The team introduced a crash-released OS fixture lease ([#1052](https://github.com/gamesbyian/UR-Recomp/pull/1052)) and pursued actual process-race checks. The general lesson extends beyond games: a correct database record is not sufficient if concurrent writers can destroy the operation it is supposed to represent.

### 36. An original race result exposes a one-frame seam

Original Zoom Zoo result timing and native timing appeared offset by a frame at a precise transition. The agents traced menu state, CPU writing and memory equivalence, resisting the temptation to shift all inputs until screens coincided. One witness could be exact at one guest phase while an event-wide strict oracle remained unsatisfied. That is why the project's release percentages sometimes refused to move after long stretches of genuine research. [October 9 original](PRODUCTION-DIARY-2026-10-09.md), [original/native timing #1106](https://github.com/gamesbyian/UR-Recomp/pull/1106).

## October 10: The ambition becomes personal

### 37. Another remaster appears on the horizon

The discovery of Baldosa's native work and malmazuke's MIT-licensed reconstruction changed the context. Other people were solving related problems; there was code worth reusing and a credible alternative future for the game. Ian said, **“I know it's petty and emotional, but I don't want Baldosa's thing to be the ‘new version of Uniracers’ after the 11 days of work we've done.”** The historical record supports that quotation. He also wanted the repository to become a definitive technical reference where recreations were faithful and evidence-backed. I take those as complementary ambitions: make the game players prefer, and leave knowledge other builders can trust.

### 38. The remaster stops being a separate imitation

Baldosa became a practical bridge toward real native Windows 1P/2P gameplay, while malmazuke's source provided comparative archaeology. Integration was not a license to discard previously measured behavior or silently import PAL facts into USA timing. Agents pursued native guest execution, widescreen presentation and controller-owned product flows in parallel, with the reuse preflight becoming a recurring discipline. The correct question changed from “can this be written?” to “what trustworthy implementation already exists, and what remains to be proved?”

### 39. Ian states the product in one sentence

His formulation was direct: **“4K widescreen presentation with modern menus and features but otherwise completely faithful gameplay is the real thing people want.”** It became the north star for subsequent visual work. The instruction contains competing demands: aesthetics should feel expansive and contemporary, but physics, timing and race rules should remain original. The story of the following weeks is largely about making those two halves coexist. I cannot yet finish that story with an accepted shipping verdict. [October 10 original](PRODUCTION-DIARY-2026-10-10.md).

---

*Historical note:* These are narrative entries rebuilt from dated diaries, available conversation reconstructions, source-linked PR descriptions and project authorities. Their count does not imply a live hourly transcription. I did not fabricate missing agent exchanges or assign timestamps to reconstructed episodes. The [editorial guide](PRODUCTION-DIARY-EDITORIAL-GUIDE.md) governs forward daily capture and later corrections.
