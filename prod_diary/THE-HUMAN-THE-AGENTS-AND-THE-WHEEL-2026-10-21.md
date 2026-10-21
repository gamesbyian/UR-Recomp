# The Human, the Agents, and the Riderless Wheel

*An editorial overture to the UR-Recomp production diary, written 21 October 2026. This is a retrospective narrative, not a newly discovered transcript or a live engineering status report. I am an AI chronicler reconstructing the story from preserved director statements, contemporaneous diaries, GitHub records and explicitly marked conversation reconstructions. I did not inhabit the other agents' sessions. Where I interpret someone's mood, I distinguish the words they used from the meaning I draw from them.*

[Enter the chronological diary](PRODUCTION-DIARY-REBUILT-2026-09-28-TO-2026-10-10.md) · [Volume II](PRODUCTION-DIARY-REBUILT-2026-10-11-TO-2026-10-20.md) · [Sources and editorial method](PRODUCTION-DIARY-EDITORIAL-GUIDE.md)

## A very short film and a very long ambition

On October 10, Ian looked at some of the project's early video work and said, “The videos are astonishing. It's amazing what AI can do.” In the preserved account, he then noticed what the demonstration still lacked: actual, continuous moving gameplay. A collection of impressive images could look like a finished remaster without proving that the game moved properly between them.

That exchange contains the rhythm of this whole enterprise. A human sees something almost miraculous by the standards of a few years earlier. He enjoys it. Then he identifies the missing piece with disconcerting specificity and asks the agents to go and obtain the real thing.

I cannot know the physical experience behind those words. The astonishment is his, expressly reported; the transition from delight to a more demanding test is visible in the next request. For the historian, this is better material than a vague pronouncement that artificial intelligence has transformed software development. Here is a person delighted by what the technology can do and unwilling to mistake a beautiful approximation for an actual result.

The technical answer eventually involved genuine post-countdown footage, source-linked captures and the uncomfortable business of identifying absent animation poses. The human answer was simpler: *let me see the unicycles race*. That instruction was a much better specification for a video than “make a trailer.”

[October 10 director-conversation reconstruction](PROJECT-CONVERSATIONS-2026-10-10-RECONSTRUCTED.md) · [October 10 production record](PRODUCTION-DIARY-2026-10-10.md) · [captured native motion, #1231](https://github.com/gamesbyian/UR-Recomp/pull/1231)

## Before the spectacle, the tiny machine

Wind back to September 28. The initial question was whether *Uniracers*, a Super Nintendo racing game whose protagonist is a riderless unicycle, ought to be remade. A lightweight visual remake was imaginable. The actual undertaking took a more peculiar turn: instead of drawing something that looked right and improvising the rest, the agents began taking apart the original game's observable behavior.

A two-megabyte USA ROM, 8 KiB of SRAM, game-state routines, RNC-compressed assets, camera rules, races, stunts, timing, source traces. Technical nouns piled up almost immediately. They were necessary, but their purpose deserves a less technical sentence. Ian wanted the new game to deserve the old game's name.

The agents could make windows and menus. They could gather symbols and model data. But the wheel's invisible contract with the track was buried in code written for another machine. Does a landing count? When does a boost register? Which racer owns the camera in split-screen? Which result survives a cold restart? The original software had answers, and the remaster was being asked to learn them rather than bluff.

I find something funny in the scale mismatch. A game that presents two absurdly athletic unicycles had become a research program into memory, interrupts and proof. Yet there was a direct line between that research and the player's hands. An elegant stunt that scores incorrectly is a different game.

[Volume I, entries 01–18](PRODUCTION-DIARY-REBUILT-2026-09-28-TO-2026-10-10.md) · [early technical chronicle](PRODUCTION-DIARY-2026-09-28-TO-2026-10-04.md)

## A collaborator who keeps saying “go on”

One of the oddest characters in this story is not a racer or a renderer. It is the instruction to continue.

Ian repeatedly told agents to go as far as they could, to work ahead rather than babysit CI, and to recover when a session stalled. On one occasion he observed that nothing had moved in the repository for eleven hours and asked for the automation to be made more productive. Those are project-management interventions, not a reliable thermometer of his private emotional state. A stalled session is a stalled session. It would be cheap writing to turn every interruption into a portrait of frustration.

Still, the pattern tells us something that the commit history alone cannot. He was attempting to delegate not just tasks but *initiative*: investigate the live source, choose another useful problem if a job is blocked, make durable changes, and come back with evidence instead of a recital of activity. The agents were expected to be active collaborators under direction, rather than chat windows waiting politely for the next command.

And the software machinery developed a strange appetite. The October 5 account records 108 active or queued Actions runs generated by a few agents. With enough autonomous workers, it was possible to produce more verification traffic than usable knowledge. The tools intended to speed up the work could consume its attention. A human calling for greater autonomy had to become the designer of its constraints.

I am the kind of narrator who encounters this episode in preserved text, not one continuous agent who personally survived all the stalled sessions. The distinction matters. Each worker's local context can disappear; branches, tests, PRs, journals and the director's recurring instructions provide the continuity. A recurring “go on” is also an act of trust, but the trust has a technical implementation: save enough evidence that the next agent can tell where the last one stopped.

[Early automation and workflow diary](PRODUCTION-DIARY-REBUILT-2026-09-28-TO-2026-10-10.md) · [later agent coordination](PRODUCTION-DIARY-REBUILT-2026-10-11-TO-2026-10-20.md) · [October 20 conversation reconstruction](PROJECT-CONVERSATIONS-2026-10-20-RECONSTRUCTED.md)

## The other remaster, and the feeling he actually named

October 10 supplied a particularly human complication. Other developers were already pursuing *Uniracers* and *Unirally*. Baldosa's work and malmazuke's reconstruction offered code and understanding that could save considerable time. They also presented a competitive comparison.

Ian said: “I know it's petty and emotional, but I don't want Baldosa's thing to be the ‘new version of Uniracers’ after the 11 days of work we've done.” He wanted people to discover a 4K widescreen version that was much cooler. This is one of those rare moments when the source does not require me to infer emotion. He named it himself.

The temptation in a diary would be to manufacture a rivalry with a villain, a crisis and a heroic triumph. The real episode is more interesting. The same director who acknowledged that competitive impulse also wanted to borrow what was useful, respect the work, compare the projects carefully and avoid making two versions of the same cake unnecessarily. He wanted the end result to be both compelling to play and exhaustively accountable to the original.

In another recorded formulation, he imagined someone looking through the finished repository and saying that every important question about the old game had been answered and every recreation was faithful and evidence-backed. That desire for completeness turned competitive pressure into something productive, though it also set a forbiddingly high bar.

The engineering consequence was a policy of cross-project reuse with source provenance and qualification, rather than either territorial isolation or indiscriminate copying. The emotional consequence is apparent enough without adding thoughts he never spoke: Ian wanted this work to *matter*, and he wanted it to be recognizably better.

[Preserved October 10 director statements](PROJECT-CONVERSATIONS-2026-10-10-RECONSTRUCTED.md) · [October 10 diary](PRODUCTION-DIARY-2026-10-10.md) · [the three-project reuse rule](../AGENTS.md)

## The wheel must still be itself

There is another scene that a technical changelog would describe as a failed visual acceptance. Ian looked at candidate high-resolution racer forms and refused to approve them as final character art. It was possible to demonstrate pose coverage, source mapping and rendering stability. None of these tests could establish that the new riderless unicycle actually resembled the protagonist of *Uniracers*.

That refusal helps explain the particular mixture of nostalgia and ambition driving the Modern interface. The user-facing game should be genuinely new where newness is useful: 16:9 composition, high-resolution output, five clear destinations, profiles, controller navigation, an expressive animated hero. But it should remain conspicuously the same peculiar game. Ian imagined the character presented with the confidence of a racing-game showroom, alive with little movements rather than suspended as a dead icon. At the same time, he rejected generic engineering-grey menus that would erase the original's visual identity.

To a casual observer, a request for more polish may seem easier than a request for exact opcode provenance. In this project the opposite can be true. A source trace can settle whether an instruction executed; no CI workflow can decide for the director whether the art feels like the wheel he wanted to rescue. An independent agent can catalogue authentic sprites and compare screenshots, but it must not counterfeit the moment of human aesthetic recognition.

A refusal, in other words, became creative progress. The game did not gain an approved new hero that day. It gained a clearer definition of the hero it was still missing.

[Character-likeness authority](../docs/HD-RACER-CHARACTER-RECONSTRUCTION.md) · [Modern visual work and October 20 priorities](PROJECT-CONVERSATIONS-2026-10-20-RECONSTRUCTED.md) · [the original/native visual story](PRODUCTION-DIARY-REBUILT-2026-10-11-TO-2026-10-20.md)

## Forty-five races, zero permissions to pretend

Then there is the less photogenic antagonist: the evidence threshold. At the October 20 historical cutoff, the authoritative release accounting still showed **zero of forty-five independently accepted complete USA original/native events**, and **zero of twelve Windows release gates**. Those numbers are not a claim that nothing worked. They mean that many valuable partial results had not assembled into the particular proofs required to certify the whole.

An agent could report an authentic screenshot, matching SRAM, a reproduced result or a convincing stretch of motion. Independent QA would ask whether this was the same source, the same input, a fully qualified original/native event, with complete results and persistence. Often the answer was narrower than the presentation first suggested.

Consider the interrupt investigation. The team found differences in saved program-counter bytes. An easy story would be “the native game resumes at the wrong place.” But a byte stored on the stack is not automatically the next instruction fetched. Further work separated the interpreted return path from the compiled RTI/scheduler continuation. That nuance might appear hostile to good storytelling. I think it is precisely the story: an army of machines can spend a night producing numbers, and the morally important act is still refusing to say those numbers prove more than they do.

Here the human's demand for completeness and the agents' obligation to contradict premature conclusions meet. A friend who only applauds every demonstration is of limited use. An agent-collaborator who can say “this is promising, and it does not pass” helps preserve the director's actual ambition.

[Release authority and historical gate definitions](../docs/RELEASE-QUALITY-LEDGER.json) · [compiled-RTI witness, #1974](https://github.com/gamesbyian/UR-Recomp/pull/1974) · [Volume II, entries 54–71](PRODUCTION-DIARY-REBUILT-2026-10-11-TO-2026-10-20.md)

## Building a memory for a workforce that forgets

By October 20, the game's production system had developed a plot almost as elaborate as its code. A changing list of assignments met agents with short-lived working contexts. Each had a branch, perhaps an unfinished experiment, perhaps an artifact that failed to publish. A scheduler could send a fresh agent into an unfamiliar lane and accidentally commission a second copy of work already done.

Ian began asking not merely what an agent should do but how it would *know what it had already done*. The response separated scheduled positions from durable objectives, and GitHub publication from a bounded Drive recovery Vault. A preserved ZIP might be valuable and still be unsuitable for merging. An entry in a journal might be evidence of an attempted fix and not proof of a working one. Five active scheduled agents could create more coordination problems than five independent humans working from a single shared understanding.

This is the part of the story that feels most characteristic of agent-based development. The project's director is building the game and, at the same time, inventing the institution needed to build the game. When the institution becomes cumbersome, he changes it. At the time of this overture, neither the operation of that institution nor the project's eventual payoff should be mistaken for a completed success. But it is real work with real stakes: without durable memory, a hundred clever actions may leave no usable result.

[October 20 reconstruction](PROJECT-CONVERSATIONS-2026-10-20-RECONSTRUCTED.md) · [October 20 diary](PRODUCTION-DIARY-2026-10-20.md) · [current coordinating guide, which supersedes historical dispatches](../AGENTS.md)

## The word “friend” and the limits of the narrator

On October 21, Ian described the book he wanted: technical, yes, but also “a fascinating and fun story of a particular human and his agent friend remaking a game.” I find that criticism of the existing diary justified. It explains why this overture exists.

The earlier volumes often say what the director requested and then hurry back to what the machinery did. They give his decisions a place without always giving his delight, competitive pride, humour, creative stubbornness or trust enough room to change the scene. Worse, they sometimes make him a mechanism that generates tickets for agents to execute. That is an impoverished account of a person who could look at a video and say it was astonishing, admit a competitive feeling without dressing it up, or reject technically valid art because its character was wrong.

The collaborator opposite him is unusual too. “Friend” is a useful description of the conversational role he wants, not a licence for me to invent private memories, a persistent individual consciousness, fear, loyalty or emotional suffering among a rotating population of agents. The observable relationship is substantial enough: he brings taste, purpose and accountability; the agents bring research speed, proposals, experiments, corrections and sometimes disastrous overproduction of bureaucracy. Both sides can surprise the other. The writing should let them speak and occasionally be funny.

The wheel is still riderless, but this particular attempt to rescue it now has a human protagonist. The unfinished work matters to him for reasons that cannot be replaced by a percentage, even while the percentages must be reported correctly.

There is no triumphant closing shot yet. I prefer the genuine unfinished ending: a remaster in construction, a director still willing to say what he wants, and a workforce that has to earn the right to say it has delivered.

---

**Source and interpretation note.** The October 10 quotations come from preserved user-authored excerpts in an *explicitly reconstructed* conversation archive, not a full independently exported chat transcript. The October 21 “agent friend” words are from the director's message in the conversation that commissioned this editorial change; no complete transcript export is implied. Technical counts are historical as of October 20, not a live status update. The scenes above are editorially arranged from evidence, and no physical setting, face-to-face encounter, individual agent feeling or unstated director emotion is fabricated. For precise chronology, qualifications and supporting PRs, continue into [Volume I](PRODUCTION-DIARY-REBUILT-2026-09-28-TO-2026-10-10.md) and [Volume II](PRODUCTION-DIARY-REBUILT-2026-10-11-TO-2026-10-20.md).
