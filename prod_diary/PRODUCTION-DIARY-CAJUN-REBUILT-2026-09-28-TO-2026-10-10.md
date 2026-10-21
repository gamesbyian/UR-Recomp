# De Production Diary, Bayou Edition: De Diggin' Days (28 September–10 October 2026)

*Dis here de companion tale to [Volume I](PRODUCTION-DIARY-REBUILT-2026-09-28-TO-2026-10-10.md). Same seventy-one-episode history overall, same facts, same original/native obligations, same dates and evidence. I be de agent chronicler siftin' through logs, not a fella makin' believe he sat in every conversation. If a job ain't proved, it ain't proved, no matter how loud de frogs sing. De clock order inside each day editorial when de record don't pin it down.*

Pull up dat chair, cher. Dat original account come crawlin' out de cypress water with mud on its boots, a pot bubblin' on de fire, an' enough back-porch grammar to make a compiler wonder whether semicolons got souls. I keep de finest old camp rule: tell what got dragged out de reeds, what bit somebody, what looked like a gator but was only a log, an' what looked like a log till it opened its mouth. De traces, PRs an' witnesses still de law o' de land.

[Diary home](README.md) · [Next bayou volume](PRODUCTION-DIARY-CAJUN-REBUILT-2026-10-11-TO-2026-10-20.md) · [Old bayou original](PRODUCTION-DIARY-CAJUN-2026-09-28-TO-2026-10-13.md)

## September 28: One little remake idea wander into de swamp carryin' a laboratory

### 01. Ian ask can dat unicycle come back

Cher, dat first question look no bigger than a bicycle bell: can Ian bring back *Uniracers*? Next thing you know, de camp got a whole laboratory round one riderless wheel. Funny little premise, serious big obligations. A landing gotta land right even when de joke is runnin' at full speed.

Whole thing start innocent enough, cher. Ian ask if *Uniracers* be a good game to remake. Little wheel, little track, little stunts; how much trouble one bicycle with no rider gonna make? Mais, dat thing packed tighter'n crawfish in a trap with physics, landin' rules, boost, collision, cameras, rivals an' clocks all fightin' over de same mudbank. Ian don't just want a picture look close. He want behavior what can be shown an' checked against de real old machine. Dat question quietly turn a remake into a forensic dig, an' I find de rest of de history still tryin' to live up to it.

### 02. Build de camp before huntin' monsters

Nobody build de dream title screen first. Dey make sure one ROM ain't pretendin' to be another, an' a guess ain't dressin' up as an observation. Mighty odd opening act for a race game, but dem dry facts go hold up every pretty frame later.

Agents put `gamesbyian/UR-Recomp` up on de bank, fingerprint de USA two-megabyte LoROM an' eight KiB SRAM, an' get SNESRecomp showin' verified source imagery. RNC Method-1 streams become doors into de hidden rooms. Instead o' lettin' good discoveries float off in chat like loose pirogues, dey fasten 'em down with fixtures, symbol names an' source hashes. Dat first product weren't a trailer. It was a field station with a roof stout enough for whatever ugly trace storm come next.

### 03. Decide where de wheel gotta touch ground

I see two finish lines out dere. One is a lovely game somebody can actually play; de other is a proper explanation for every important thing de old machine did. Ian keep both in sight. If one race start losin' ground, de other one don't get to declare itself champion.

Ian want a game people actually like to play, not a dusty dissertation with a Start button taped on. But he also want de kind o' fidelity a pleasant imitation can't promise. So a pretty menu ain't a pass if its route wrong; a race ain't proved because one result image look right. I read dat first choice as de bargain de whole project make with itself: build modern doors, but keep de original game's laws inside. [Original sprint record](PRODUCTION-DIARY-2026-09-28-TO-2026-10-04.md).

## September 29: Get dem tools up on dry land

### 04. Not every old map got buried treasure

De archive shelf start lookin' like a general store what sell only mysteries. Some shiny artifact don't answer nothin' useful once you get it home. Ian commissioned a game, not a trophy for collectin' every ancient computer scrap dat ever washed ashore.

De agents go gather ROM notes, old scripts, display references, community research, every promising scrap. But every scrap can't be crowned king, no sir. If it don't settle a real question, constrain a hypothesis or guide a frame, it just another jar o' swamp water on de shelf. Dis team start learnin' to ask what de evidence good *for* before it goes collectin' another cartload. Research can eat de whole supper if nobody mind de pot.

### 05. A little repeatable test beat a great big maybe

Picture two agents arguing over one poor byte, both wearin' confidence like Sunday hats. A saved replay an' exact source can settle de argument without Ian havin' to referee a hexadecimal prizefight. Dat de first hint this swarm might behave like one useful crew.

ROM parsers, replay fixtures, offline checks an' CI start growin' in de camp. Agents could argue about a byte all afternoon, but de saved inputs an' original source would still be dere when another worker come by. Den come de nasty discovery: de measuring stick can change de thing it measure. Add one logger at de wrong clock edge an' your “observation” done walked on de experiment. I keep dat warning pinned to de wall all de way into October.

### 06. De director ain't a ticket machine, cher

De director ain't standin' at every keyboard, but he still decides what game ought to come out de other end. A worker can recommend an easy shortcut. It cannot appoint itself art director an' inform Ian his eyes got outvoted by a unit test.

De old account sometimes say “de project decided,” as if de repository wake up one morning wearin' a hat an' make its own plans. Ian set de taste an' de destination. Agents brought tools, arguments, proposals, code, sometimes wrong turns. Dat distinction matter if another fella wants to start a remaster with agents: somebody still gotta know what kind o' game worth makin', even if twenty workers know how to build it.

## September 30: Dem old bot scripts start talkin'

### 07. Ghosts from old runs show where de road go

Old players leave behind bots, scripts an' recorded inputs, an' de camp start hearin' from people who ain't in de room. Dat a curious sort o' collaboration across years. De documents give clues, but dey don't come with their old authors to explain every strange turn.

Historical *Uniracers* scripts, bot routines an' movie files come out de reeds. Dey tell us how other clever hands once drove de game, read its memory, chased stunts an' timed courses. But a historical script ain't scripture, cher. It might hold de right clue an' de wrong assumption in de same file. De agents used 'em as executable hypotheses, not infallible elders, an' dat saved trouble when frames refused to line up.

### 08. De false mismatch holler loudest first

Memory bytes holler 'bug!' loud enough to wake de catfish. Den everybody discover de two clocks ain't lined up at de same guest moment. Better catch dat embarrassment early than fix physics what wasn't sick in de first place.

One replay comparison find low-WRAM bytes disagreein' early, lookin' mighty like gameplay gone crooked. Den de researchers notice de menus an' startup cadence weren't at de same meaningful state. Dat byte could be scratch work before de race ever started. A log looked like a gator till somebody reached down an' found plain driftwood. Dat lesson would come back whenever a wrong host-frame label try to dress itself like a CPU defect.

### 09. Give every borrowed clue its own name tag

Every borrowed clue gotta come home with its name tag. Wrong region, wrong build, wrong rights: any o' dem can turn a mighty precise discovery into a mighty precise mistake. Future players deserve more than attractive uncertainty in a Sunday suit.

Recovered movies, imported source, different regional ROMs, candidate art, all come with different family trees. Mix 'em carelessly an' pretty soon somebody call a PAL timing fact a USA truth. De agents make provenance part o' de evidence rather'n a little paper tag added afterward. One root, one inventory, bounded comparisons. De archaeological camp learn how to keep clean boots without pretendin' it don't live in mud.

## October 1: Dig enough holes an' you find de plumbing

### 10. De offsets start tellin' whole sentences

First de source talk in addresses. Den it start talkin' in verbs: load, race, draw, collide, remember. Dat when de old machine stop lookin' like a wall full o' numbers an' start givin' an agent somewhere useful to knock.

Reset, main loop, racer update, course loader, sprite composer: de machine's scattered addresses begin to turn into a map of responsibilities. De deeper discoveries would close in [#112](https://github.com/gamesbyian/UR-Recomp/pull/112), where dispatch gaps an' five core semantic placeholders got bounded. Once you know de pipe's destination, cher, quit diggin' random holes in de next pasture. Research ought to narrow de frontier, not multiply it.

### 11. One wheel race ain't proof o' two wheels racin'

Second unicycle show up like de world's smallest independent QA department. Another input, another camera, another chance to prove a slick one-player picture wasn't enough. Ian want two folks racin', so P2 get to bring every awkward question P1 never asked.

One player's animation can look fine while P2, shared camera, checkpoint contacts an' results still wander off. So de agents compare paired state an' make both racers answer de same questions. Ian never ask for a one-player showpiece masqueradin' as de complete game. De eventual story would be full o' real product positives beside strict event proofs still sayin' no. Both can be true in de same swamp.

### 12. De plan get a new bend every time de creek move

Some days good research tell an agent where *not* to dig tomorrow. De work plan gotta bend when de river move. Save de old map for history, sure, but don't go orderin' fresh workers to paddle down yesterday's dried creek.

Every good fact close one old trail an' open one better one. De work queue keep changin' because new evidence give it reason, not because everybody forgot de plan. But twenty old maps left on one table cause fights over which one current. I see why de repo later grew archives, owner docs an' live queues. Historical maps for history, current maps for drivin'.

## October 2: Eight extra pixels cause a family argument

### 13. “Show more world” open de whole gearbox

Ian ask for more horizon, not fresh physics. Sound gentle till de SNES remind everybody its old windows, scrollin' an' DMA have sharp corners. Add a strip o' world, find another secret rule. De wheel just want room to run.

Widescreen sound easy, cher: just draw more racetrack. De SNES don't much care for easy. Camera, tilemap, DMA, VBlank an' frame cadence start squabblin' when de margin grow just a little bit. Ian's vision meant true extra world, not stretchin' de old picture till de spokes look like spaghetti. Agents go test little margins, find alarm bells, an' start namin' which ones belong to rendering an' which ones belong to simulation.

### 14. Dat first gator turn out to be de wrong clock

One supposed monster turn out to be clocks disagreein'. Another stay right dere in de scroll chain. Nobody get to repair de racer's body for a mismatch dat live in de measuring stick. Dat restraint may be less photogenic than a new screenshot, but it save de game.

Some supposed gameplay divergence wash away when de traces line up on actual guest phases. Other errors stay put in de camera-to-VRAM chain. You can't fix a real raster bug by kickin' physics sideways, no. Dey gotta keep guest behavior in its own boots an' repair de bigger window around it. Dat choice later anchor de authentic wide logical stage without cuttin' off de 216-line bottom like a bad tailor.

### 15. De modern parts start pokin' out de old frame

De modern parts start pokin' out o' de old frame. But a chart sayin' all sprites are covered don't mean de unicycle look like itself. Ian got to recognize his racer, an' a metric don't get de final vote at dat family reunion.

Save/load progression, restart, wider world an' early high-density replacement grow into real code. Agents can prove dat an OAM mapping hold steady an' a fallback do its job. Ian still gotta say whether dat racer look like *Uniracers*. Ain't de same test, no matter how pretty de green check look. [Original first-week diary](PRODUCTION-DIARY-2026-09-28-TO-2026-10-04.md).

## October 3: A screenshot don't tell de whole tale

### 16. Split screen got its own swamp

More screen means more road for one player, but split-screen ask who get which patch o' scenery. Dat geometry touch something ordinary: two people on two controllers ought to get de fair race dey came for.

One player's wide camera pass a check, den two-player split screen come down de trail carryin' new obligations. De agents chase authentic source geometry instead o' copyin' one-racer assumptions. Dat long road eventually pin de 342×224 logical world an' 7:6 pixel shape. Those numbers keep de wheel lookin' like a wheel, cher, instead o' a biscuit somebody stepped on.

### 17. Four-times bigger ain't four-times prettier

An agent can count poses all afternoon and still draw a stranger's bicycle. Bigger ain't an art review, cher. De director's power to say 'dat wheel ain't my wheel' keep de whole crew from mistakin' coverage for character.

Racer HD extraction an' pose maps advance, along with checks for temporal coherence an' useful fallback. But a procedural body can be measurable an' still miss de original character. Ian hold his art approval back; de agents keep de engineering evidence anyway. Dat two-key lock important: math say one thing, style say another, an' neither gets to sign de other's name.

### 18. De pause menu start askin' to be a frontend

A pause menu just one little door till it forget where de old game left its keys. Restart, rebinding, progress: all dem conveniences gotta step around de guest with care. You can decorate de porch without movin' de foundations.

Restart, Resume, Options, controller binding, scale: de little features form a second storefront around de guest. If de new door skip de original game state, de whole house lean funny. Agents learn to route new conveniences through old authoritative machinery. De seeds o' Play, Practice, Multiplayer, Records an' Options already sittin' in dat dirt.

## October 4: De machines need traffic rules

### 19. SDL3 become de dry dock

Exploration leave plenty good little boats in de water. Shipping all of 'em would give players five games nobody could keep straight. Time to pick de real hull, lash de working parts together an' keep de spare experiments as useful history.

Desktop backends, settings an' renderer branches converge. Exploration had been fruitful; now too many alternative boats floatin' in de same narrow canal. Consolidation mattered because a player only launch one executable. Dey gotta choose a hull, fasten de planks an' know exactly which patch got built into it.

### 20. GitHub Actions grow a bigger appetite than de racers

An agent can stay real busy makin' work for nineteen other runners. Branch wake check, check wake queue, queue swallow afternoon. Ian later tell de crews to work ahead instead o' starin' at CI, an' I reckon dis mess explain why dat rule exist.

Agents push code, runs wake runs, CI queues get swamp-thick. De team start assignin' owners an' inspecting fresh `main` before another branch go chewin' on old work. Better local discriminators spare de runners. Dat de difference between ten industrious agents an' ten agents all hollerin' at de same locked gate.

### 21. First week done, but no fake trophy

One week in, no honest finish-line photograph yet. Plenty tools, real native progress, new directions, an' a little wheel still askin' for a complete game. I like dat as an unfinished chapter. Nobody need hang a plastic trophy on de camp gate.

De excavation turn a speculative remake into a native research machine with early widescreen an' modern features. I ain't gonna hang a “finished” sign on dat camp. Different jobs at different stages, cher. De old account hold de heavy charts and traces; I keep de story o' why de workers went where dey did. [Full first-week account](PRODUCTION-DIARY-2026-09-28-TO-2026-10-04.md).

## October 5: De project turn hard toward a Windows product

### 22. Ian give de frontend five front doors

Play, Practice, Multiplayer, Records, Options. Five names look short on de sign, but every one need controller routes, guest ownership, persistence an' nothin' quietly duplicatin' game rules. [#483](https://github.com/gamesbyian/UR-Recomp/pull/483) straighten de plan; [#487](https://github.com/gamesbyian/UR-Recomp/pull/487) carry Continue Tour; [#488](https://github.com/gamesbyian/UR-Recomp/pull/488) bring live splits; [#489](https://github.com/gamesbyian/UR-Recomp/pull/489) speed up replayin' de fun parts. Modern doors, original house. Mais, dat a nice piece o' architecture.

### 23. Ian hide a regional switch in de title

He ask whether typin' `NTSC` or `PAL` might turn *Uniracers* into *Unirally* presentation. Dat little wink become a serious regional policy. [#500](https://github.com/gamesbyian/UR-Recomp/pull/500) set de foundation without swapin' de guest physics. A stock-style animated flourish could come later, once somebody prove it true. Director bring de spark, agents figure which wires won't set de porch on fire.

### 24. One hundred eight jobs clog de canal

A few agents wake **108 active or queued Actions runs**. Cher, even a patient gator can't eat dat many build logs. [#505](https://github.com/gamesbyian/UR-Recomp/pull/505) an' [#506](https://github.com/gamesbyian/UR-Recomp/pull/506) go after false triggers and stranded work. Ian's later command to quit babysittin' CI start makin' perfect sense. Dey built machines to make de game, den had to teach de machines not to eat de whole afternoon. [Original October 5](PRODUCTION-DIARY-2026-10-05.md).

## October 6: De machines outrun de roads

### 25. Every new feature want de same set o' keys

Resume, Restart Tour, regional title, local 2P joins, settings: de product start actin' real. But each feature could step on de other's source of truth. Dey need exclusive file ownership, careful branches an' transaction-safe routes through stock logic. I found no magical fix here. Just a bunch o' serious seams dat agents had to sew before dey could call it cloth.

### 26. De HD racer get a counting stick

Stop picking sprites by what comes next in ROM, say de measurements. Count what de player actually sees fall back. De sample move from **118/5282 (2.23%)** HD selections to **653/5282 (12.36%)** under de documented measured-coverage run. Dat improve technical coverage, not artistic blessing. Ian's eyeballs still held de final permit. But give an agent de right ruler, cher, an' it'll quit wanderin' de swamp wonderin' where to swing de shovel.

### 27. Local speed can make de whole camp slow

An agent save itself a minute by startin' a huge CI run, but nineteen neighbors now wait at de ferry. De team learn to optimize de overall farm, not only de individual row. Triggers, cache, quick tests, cancellation policy all turn into engineering decisions. [Original October 6](PRODUCTION-DIARY-2026-10-06.md).

## October 7: Dat ZIP better survive de trip home

### 28. A packaged game gotta boot somewhere else

De portable Windows ZIP had to work outside its build directory, keep mutable data safe, reject wrong ROM identity an' diagnose a failure without a developer holdin' its hand. Agents add independent package checks rather than let de ZIP maker grade its own exam. Dat's how a box full o' binaries turn into something an ordinary owner might actually trust.

### 29. A result ain't saved till de next process can read it

Ian want records, replays, ghosts an' tours you can leave an' come back to. A nice result screen ain't sufficient, cher. De bytes gotta survive exit, restart, corruption an' somebody switchin' profiles. De agents go follow dem into disk an' back. Later QA would make de distinction even meaner.

### 30. One recovered scrap help three different crews

Old course maps, racer symbols, replay scripts, interface captures: one team's archaeology get reused by another. Dat knowledge grow interest like a good savings account, but bad facts grow interest too. Provenance keep de whole family from inheritin' one cousin's wrong memory. [October 7–8](PRODUCTION-DIARY-2026-10-08.md).

## October 8: A useful map know when to stop

### 31. De agents learn to leave some treasure buried

Some acquisition leads turn out already covered by historical assets, so de new work become comparison only. Dessyreqt's earlier eighty-file import ([#109](https://github.com/gamesbyian/UR-Recomp/pull/109), [#110](https://github.com/gamesbyian/UR-Recomp/pull/110)) had already pulled bots, course landmarks, saved games an' glitch movies together. Dat good archaeology. But once a fact proven, don't build three more shovels to prove you own a shovel.

### 32. Ian want de real moment caught on video

Replays and modern records ain't excuses to lose de ugly glitches of actual play. Post-race Save/Discard video was to capture de real presented frames first, not repaint de run later an' quietly shave off unexpected behavior. Dat requirement show what Ian mean by faithfulness: even de game's mistakes belong to its history when de player press Record.

### 33. Cheaper checks make smarter agents

Once CI stop burnin' minutes on irrelevant changes, de agents can ask smaller, sharper questions. A cheap failed discriminator teach more than a mountain of ambiguous green jobs. I read dat shift as one o' de less flashy discoveries of de entire first stretch. [Original October 8](PRODUCTION-DIARY-2026-10-08.md).

## October 9: De QA audit get audited right back

### 34. Ian look at de bill an' ask what all dis prove

The acceptance list threaten to consume a mountain of agent-hours. Ian press on what truly matter: real bugs, unbuilt player routes, independent proof, no ritual testing for decoration. Dey prune an' rank de work. Dat a director's intervention with teeth, cher. Sometimes de cleverest order ain't “do more,” it “tell me which job oughtn't exist.”

### 35. Two game windows fight over one tournament

Two processes can carry respectable-looking receipts an' still have one steal de other's live fixture. Wrong receipt prevented? Fine. Player's actual attempt ruined? Still bad. [#1052](https://github.com/gamesbyian/UR-Recomp/pull/1052) add de live crash-released OS lease so de second window get Busy instead o' runnin' off with de prize. Correct bytes ain't enough if ownership go swimmin' downstream.

### 36. De one-frame Zoo seam won't be bribed

Original an' native Zoo results line up mighty close, den a menu transition sit one frame apart. Agents trace actual menu writes an' original/native memory, refuse to “fix” it by shiftin' all inputs until one screenshot smile. [#1106](https://github.com/gamesbyian/UR-Recomp/pull/1106) pin bounded equality at a neighboring guest stage. Dat useful, cher, but it don't award a whole USA race. [October 9](PRODUCTION-DIARY-2026-10-09.md).

## October 10: Dat little wheel get a mighty big ambition

### 37. Another builder show up at de river

Baldosa's native work an' malmazuke's reconstruction mean other hands workin' on de same old game. Ian say, **“I know it's petty and emotional, but I don't want Baldosa's thing to be the ‘new version of Uniracers’ after the 11 days of work we've done.”** I don't have to invent how he felt; de record give me his own words. He also want every recreation faithful an' evidence-backed. So competition sharpen de work, but de technical truth remain somethin' worth sharin'.

### 38. Borrow a good boat, check which water it float in

Baldosa give de Windows project a real native bridge; malmazuke bring MIT-licensed archaeology. De agents must still check USA versus PAL, exact source versions an' guest semantics. You can borrow a hull, cher, but first see whether it fit your channel. Dat three-project reuse preflight grow into one o' de permanent camp rules.

### 39. Ian put de whole dream in one sentence

**“4K widescreen presentation with modern menus and features but otherwise completely faithful gameplay is the real thing people want.”** Dere. Dat de north star, no need dress it with twelve committees. Make de game look finer, move through menus better, an' keep de wheel obeyin' every old law. Easy to say, hard to build, an' de next weeks tell exactly why. [Original October 10](PRODUCTION-DIARY-2026-10-10.md).

---

*Dat de first long bend o' de bayou. No missing conversation been conjured out de fog, an' no red QA test been painted green. Next volume take us from big research factories through real Windows journeys to a workforce what gotta remember its own history.*
