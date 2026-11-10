# Recruitment and coordination plan

**Primary outreach link:** [Short recruitment landing](https://gamesbyian.github.io/UR-Recomp/contributors/), with compact role cards and one-click contribution intake. **Deeper optional gallery:** [Artwork references](https://gamesbyian.github.io/UR-Recomp/contributors/references/). Keep the compact page as every post's common entrypoint; original PNGs/SVGs remain at their prior `/contributors/images/` direct URLs. Publication follows the existing Visual Atlas Pages workflow.


**Purpose:** actively invite unpaid, optional, bounded contributions in four lanes: 3D racer reconstruction, regional lettering/language review, supervised agent-run engineering and Windows testing. A fifth invitation, prominent in **every initial post**, seeks coordination with all Uniracers/Unirally efforts beyond known Baldosa and malmazuke projects.

## Publication order and criteria

1. Merge the public contributor-interest and playtest GitHub issue forms. Check that they render, route to this guide, and warn about public privacy. Verify existing reference asset URLs before posting.
2. Assemble a small, rights-respectful **artist reference pack**: English traced SVGs, proposed regional SVGs clearly marked experimental, actual experimental 3D viewer screenshots/model where authorized, and approved illustrative promo art. A background image is not gameplay evidence.
3. Post **Blender Artists Volunteer Work** (3D), **r/INAT** (mixed), and **itch.io Help Wanted or Offered** (art) by authorized humans. Itch.io currently explicitly prohibits AI agents from posting. Community rules, relevant tags, and moderation guidance win over any automation.
4. Post technical appeals in allowed locations in **r/ChatGPTCoding**, **r/ClaudeCode**, **r/aiagents**, and **r/opensource**. r/opensource may require its designated project/contributor thread. Each offer is one bounded supervised task with independently reviewable evidence, not an open-ended assignment.
5. In **r/retrogaming** and **r/snes**, lead with genuine source-verified gameplay footage and a request for remembered mechanics, expertise and other projects; abide by self-promotion rules. Do not imply a ready public Windows build.
6. Seek feedback or volunteer lettering in **r/lettering** and **r/logodesign** only after confirming recruitment/solicitation rules. Convert to feedback-only if necessary.
7. Release-gate **r/playmygame** and **r/DestroyMyGame**: publish only after an authorized, publicly accessible, stable **ROM-free** Windows test download with exact source/package SHA, setup instructions and a working report route. r/DestroyMyGame also requires actual gameplay video. No GitHub Release exists yet; an expiring CI artifact does not meet this gate.

All proposed venue-specific copy is stored in the posts directory. Nobody has posted these messages yet. No recurring polling, forum bots or email sending is enabled by this PR.

## Rules for every initial post

- Be explicit that this is unofficial fan work, **unpaid**, opt-in and independent of the original rights holders.
- Invite fellow Uniracers/Unirally projects, **explicitly mention Baldosa and malmazuke**, link to their independent repos, and do not imply prior coordination or endorsement.
- Describe work as accurately scoped and unfinished; distinguish past source experiments, current main, proposed art, tested Windows bits and release-qualified distribution.
- Show one concrete contribution and a working permitted way to reply; never publish someone's private contact details in a public issue.
- Check current forum rules before posting. Never simulate a human account or evade moderation/rate limits. Use human original posting on human-only forums.
- Record the exact public permalink in the venue registry only once actually published; record blocked or rejected attempts accurately. Do not auto-repost or use historic prospect lists for cold contact.

## Ongoing coordination

Keep public forum post URLs and draft status in campaign.json; store contact details, raw correspondence, submitted files, consent and private reviews **outside this public repository**. Acknowledge inbound volunteers, request a bounded next contribution, then link accepted public research or code through ordinary issue/PR review. Respect departures and opt-outs without follow-up pressure.

Metrics should be privately recorded: genuinely opted-in contributors, actionable submissions, qualified accepted improvements, response latency, and tester feedback anchored to real packages. Stop publishing into venues with no permitted route. Optimize quality of connections, not volume of repeated outreach.

## Authority boundaries

Existing five agents continue their single ranked shared engineering queue; no new recruitment lane is added to the hourly pool. Existing QA ledger is sole release authority. No artwork, code, model, language claim, external-source import or binary becomes accepted merely because a volunteer submitted it. See [operations](OPERATIONS.md).

## Pages gallery publication

The recruitment reference gallery is published through the existing Visual Atlas workflow at [https://gamesbyian.github.io/UR-Recomp/contributors/](https://gamesbyian.github.io/UR-Recomp/contributors/). Its first [main deployment](https://github.com/gamesbyian/UR-Recomp/actions/runs/42718635056) succeeded. Main-branch contributor-gallery changes trigger the same publishing workflow; unrelated atlas updates retain their existing manual publish gate. Before a forum post, test actual browser access, direct media links and mobile layout. Only the provided concept PNGs and the existing wordmark SVGs are included, not box art.


## Public experimental Windows playtester recruitment

The project can already produce independently byte-audited ROM-free Windows x64 **experimental physical-playtest candidates**, so invite volunteers **now** to help test when a current, verified candidate is furnished. Requesting interest by email or GitHub does not imply that a fixed public release download exists or that an expiring GitHub Actions artifact is accessible without login. Before sharing any package, verify source commit, ZIP and PE SHA-256, ROM-free boundary, availability and clear startup/reporting instructions via the existing `docs/WINDOWS-PLAYTEST-INSTRUCTIONS.md` and `docs/playtest/REQUEST-WINDOWS-PLAYTEST.md` process. Tell testers about limitations and treat all reports as observations requiring further reproduction, not original-game oracle evidence. Keep the r/playmygame and r/DestroyMyGame public-download/video publication gates in place until a stable public test package exists.

All recruitment Pages subpages (`/contributors/`, `/contributors/references/`, `/contributors/3d/`) use the same sketched logo, fixed graph-paper treatment and bottom track/racer visual language. All five primary opportunities present equally visible email and GitHub routes; specialists can contact the owner-approved project email without a GitHub account.
