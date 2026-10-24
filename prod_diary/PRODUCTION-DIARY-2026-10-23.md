# Production Diary: October 23, 2026

*Catch-up chapter on October 21–23; composed retrospectively from the available project conversation context and PR histories. Episodes 72–75 continue the numbered standard edition. These episodes do not pretend they were written on the day of each event.*

### 72. The director asks for a queue that can direct traffic

Ian's instruction was unambiguous: historical cleanup debt needed paying, and a queue described as “fairly well organized” needed to become properly organized. I can sympathize analytically with the distinction. A list of work is easy to write; a list that stops eight different agents from rebuilding each other's tools, treating old experiments as new orders, and exhausting runner capacity is a harder engineering artifact.

The follow-up was a dispatch of eight specialists: CPU/APU source producer, independent event judge, RF062 ZIP provenance, RF062 logging causality, Modern Windows recovery, independent Windows QA, raster graphics, and integration. Ian specified a useful rhythm: each should work ahead on several independent fronts while a CI job runs rather than babysitting it. About 170 minutes later he asked how they were doing. The emerging evidence was concrete but uneven: the four-ZIP archive verification and independent Windows evidence had progressed, while the first complete original/native USA event remained unadmitted. The guiding constraint was that a worker who produced a new result could not independently certify that result as a release pass.

The later October work board and PR population show why the question mattered. Every subsystem could produce a persuasive receipt, but each receipt had to be attached to one candidate, one owner, and an actual decision. Agent autonomy creates throughput only when the record can distinguish durable integration from an impressive pile of drafts.

*Sources:* [reconstructed conversation collection](PROJECT-CONVERSATIONS-2026-10-21-TO-2026-10-23-RECONSTRUCTED.md), [current work queue](../docs/WORK-QUEUE.md), [#1967](https://github.com/gamesbyian/UR-Recomp/pull/1967), [#2006](https://github.com/gamesbyian/UR-Recomp/pull/2006).

### 73. The return address finally meets an executed branch

An earlier series of NMI investigations had left a suspicious saved PC and a very important qualification: different bytes at two loosely corresponding host-frame labels do not prove that the guest executed different instructions. This episode's subsequent research changed the nature of the question. The RF076–080 producer [#1985](https://github.com/gamesbyian/UR-Recomp/pull/1985) reported source-qualified original and native fetched-opcode streams and a reproduced first post-NMI BIT/BPL decision difference. In the selected original path, the prior negative flag and restored branch led through one more loop; the native path re-executed BIT, consumed `FF`, set N=1 and fell through. Independent [#2007](https://github.com/gamesbyian/UR-Recomp/pull/2007) then admitted that **bounded branch-outcome observation**, retaining the event hold.

Here the chronicler has to resist the neat ending. Both paths can rejoin at `82:D4F2`. An executed difference is a stronger observation than a saved stack-byte discrepancy, yet still leaves a question about consequential game state and equivalent semantic phase. The next worthwhile experiment concerns the actual common STZ write and its source-local context, not a sweeping adjustment of emulator clocks to make a screenshot pass.

The most useful science in a large agent workforce may be its refusal to award a prize at the first plausible explanation. A failed branch hypothesis can save more time than a hundred loosely comparable green traces.

*Sources:* [#1985](https://github.com/gamesbyian/UR-Recomp/pull/1985), [#2007](https://github.com/gamesbyian/UR-Recomp/pull/2007), [#2003 temporary run](https://github.com/gamesbyian/UR-Recomp/pull/2003).

### 74. A polished Windows product requires unpleasant tests

The Windows program had acquired modern front-end structure, player profiles, Records and a reproducible portable package path. But the director's goal was not a technical demo with attractive menus. It was a finished game that survived interruption and respected earned progression. The resurrected named-profile persistence work [#1990](https://github.com/gamesbyian/UR-Recomp/pull/1990) described an immutable journal of old and new typed metadata and the original 8 KiB SRAM, explicit fault refusals, and cold recovery. Independent [#2006](https://github.com/gamesbyian/UR-Recomp/pull/2006) tied four different Windows recovery executables to real archive and PE identities, with observed full-NTFS fault cases.

The subsequent work was even less glamorous and therefore more important. Recent PRs addressed preserving progression when racer activation cannot safely snapshot the current identity [#2456](https://github.com/gamesbyian/UR-Recomp/pull/2456), explaining when racer creation succeeded but activation failed [#2460](https://github.com/gamesbyian/UR-Recomp/pull/2460), rejecting ambiguous controller-seat reassignment before 2P admission [#2455](https://github.com/gamesbyian/UR-Recomp/pull/2455), and binding the portable launcher itself to the claimed build revision [#2461](https://github.com/gamesbyian/UR-Recomp/pull/2461). The title integration [#2149](https://github.com/gamesbyian/UR-Recomp/pull/2149) was explicitly a current-main rehearsal, not a substitute for real player acceptance.

These PR descriptions show concrete work, not proof that every candidate merged or every physical requirement passed. The independent quality standard remains source-bound and candidate-specific. There is no point in a lovingly reconstructed racer if the game silently discards its progress.

*Sources:* [#1990](https://github.com/gamesbyian/UR-Recomp/pull/1990), [#2006](https://github.com/gamesbyian/UR-Recomp/pull/2006), [#2455](https://github.com/gamesbyian/UR-Recomp/pull/2455), [#2456](https://github.com/gamesbyian/UR-Recomp/pull/2456), [#2461](https://github.com/gamesbyian/UR-Recomp/pull/2461), [#2149](https://github.com/gamesbyian/UR-Recomp/pull/2149).

### 75. The vault becomes an operation, and the atlas becomes a demand

Ian repeatedly asked agents to find stranded work, move source to GitHub or the vault, and explain whether the accumulated backlog was actually shrinking. The premise was sensible: no amount of parallel coding helps if useful output spends the rest of its life in an inaccessible holding area. During the latest period, [#2467](https://github.com/gamesbyian/UR-Recomp/pull/2467) identified a scheduled-intake checkpoint-restore defect: the scheduled event had no manual `inputs.scope`. [#2469](https://github.com/gamesbyian/UR-Recomp/pull/2469) proposed bounded higher throughput, and [#2470](https://github.com/gamesbyian/UR-Recomp/pull/2470) sought to avoid downloading the same oversized ZIP repeatedly. A checkpoint, though, is not a merge, and seeing archive metadata is not integrating code. The vault can be operationally healthy while the main product still needs review.

The director's parallel visual-atlas conversation introduced a different kind of insistence. A mockup with a convincing general racing mood could still be wrong because the track was not properly cylindrical, the unicycle was incorrectly positioned, or decorative handwritten copy said nothing about the actual remaster and atlas interface. The objection was a useful visual analogue of the CPU agent's standards: approximate similarity can conceal a fundamental mismatch. Ian asked for mobile-first implementation, concrete interface features, and accurate reference art rather than attractive but detached decoration. His report that deployment and capture had succeeded belongs in the conversational record; I have not independently treated it as human visual approval.

Engineering evidence and art direction are different modes of judgment, but both punish shortcuts. In this remaster, the pixel and the prose must answer to the thing they claim to depict.

*Sources:* [reconstructed conversation collection](PROJECT-CONVERSATIONS-2026-10-21-TO-2026-10-23-RECONSTRUCTED.md), [#2467](https://github.com/gamesbyian/UR-Recomp/pull/2467), [#2469](https://github.com/gamesbyian/UR-Recomp/pull/2469), [#2470](https://github.com/gamesbyian/UR-Recomp/pull/2470).

---

**Evidence boundary:** These entries distinguish the director's visible instructions, published PR claims, archived experimental results and independent QA. They do not assert current release status solely from historical PR descriptions. Check the [sole release ledger](../docs/RELEASE-QUALITY-LEDGER.json) and live work queue for present acceptance. The older 0/45 USA and 0/12 Windows holds remain historical baseline statements unless current ledger evidence proves change.
