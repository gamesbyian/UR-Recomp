# Production Diary, Bayou Companion: October 23, 2026

*Retrospective October 21–23 catch-up, episodes 72–75. Same facts and qualifications as the standard chapter; the bayou language is literary, not another evidence source.*

### 72. Eight boats and one channel

Mais, Ian looked at dat work queue and said, in effect, properly organized means **properly** organized. He didn't ask for eight agents to sit beside eight spinning CI wheels. He sent CPU/APU, independent game QA, two RF062 evidence keepers, Windows storage, Windows release QA, graphics and integration down separate channels, told 'em to read their onboarding, and to keep more than one useful job going.

After about 170 minutes he came back wanting results. Some archives got their credentials checked; Windows QA bound real candidate bytes; original/native complete USA events still hadn't earned acceptance. Dat's the channel marker: a green receipt is a useful boat, but it ain't the entire fleet home.

*Sources:* [conversation collection](PROJECT-CONVERSATIONS-2026-10-21-TO-2026-10-23-RECONSTRUCTED.md), [#1967](https://github.com/gamesbyian/UR-Recomp/pull/1967), [#2006](https://github.com/gamesbyian/UR-Recomp/pull/2006).

### 73. Dat branch took the long way round

Cher, the saved return address been makin' noise for days. But a saved byte sitting on a stack is no executed instruction. [#1985](https://github.com/gamesbyian/UR-Recomp/pull/1985) finally brought real fetched-opcode streams and a bounded BIT/BPL difference. In the selected original NMI path, BPL takes one more loop; the native path reads `FF` at BIT, sets N and falls through. Independent [#2007](https://github.com/gamesbyian/UR-Recomp/pull/2007) checked the little fork without claiming the whole race had been proven faithful.

Then both streams can meet again at `82:D4F2`. Dat's the important bend: no excuse to move all the clocks just because one branch made a different turn. Follow the real STZ write and find out whether anything lasting went downstream.

*Sources:* [#1985](https://github.com/gamesbyian/UR-Recomp/pull/1985), [#2007](https://github.com/gamesbyian/UR-Recomp/pull/2007).

### 74. A pretty menu cannot save a lost racer

All dem fine Modern screens don't amount to much if a named racer loses earned SRAM on a bad disk day. [#1990](https://github.com/gamesbyian/UR-Recomp/pull/1990) carried the journal and cold-recovery work; independent [#2006](https://github.com/gamesbyian/UR-Recomp/pull/2006) pinned four real Windows executables to actual fault archives. Later, [#2456](https://github.com/gamesbyian/UR-Recomp/pull/2456) guarded against switching away from a racer whose progress couldn't be saved, while [#2460](https://github.com/gamesbyian/UR-Recomp/pull/2460) made the interface say when creation worked but activation didn't.

And [#2455](https://github.com/gamesbyian/UR-Recomp/pull/2455) kept a wandering controller seat from masquerading as a stable two-player admission. [#2461](https://github.com/gamesbyian/UR-Recomp/pull/2461) asked the portable launcher to tell the same build-revision story as the manifest. A PR can propose and test a correction without proving a final physical release, mais dat qualification matters more than a glossy progress report.

*Sources:* [#1990](https://github.com/gamesbyian/UR-Recomp/pull/1990), [#2006](https://github.com/gamesbyian/UR-Recomp/pull/2006), [#2455](https://github.com/gamesbyian/UR-Recomp/pull/2455), [#2456](https://github.com/gamesbyian/UR-Recomp/pull/2456), [#2460](https://github.com/gamesbyian/UR-Recomp/pull/2460), [#2461](https://github.com/gamesbyian/UR-Recomp/pull/2461).

### 75. The vault and the crooked track

Ian kept asking where the stranded work went. [#2467](https://github.com/gamesbyian/UR-Recomp/pull/2467) found the scheduled checkpoint had been askin' for an input only manual runs possessed; [#2469](https://github.com/gamesbyian/UR-Recomp/pull/2469) considered more files per cycle, and [#2470](https://github.com/gamesbyian/UR-Recomp/pull/2470) proposed not hauling the same oversized archive up the bank over and over. None of dat makes an unreviewed file magically become merged source.

Over by the visual atlas, a pretty mockup still drew the track wrong. Ian wanted a broad-striped cylinder with a properly placed riderless wheel, meaningful handwritten copy and the real mobile interface, not just a handsome poster. Whether it's a source PC or a piece of track art, close ain't the same as right.

*Sources:* [conversation collection](PROJECT-CONVERSATIONS-2026-10-21-TO-2026-10-23-RECONSTRUCTED.md), [#2467](https://github.com/gamesbyian/UR-Recomp/pull/2467), [#2469](https://github.com/gamesbyian/UR-Recomp/pull/2469), [#2470](https://github.com/gamesbyian/UR-Recomp/pull/2470).

**Historical truth and HOLD:** This companion shares the standard chapter's uncertainty and source limits. No episode grants USA event or Windows release acceptance. Consult the [current ledger](../docs/RELEASE-QUALITY-LEDGER.json).
