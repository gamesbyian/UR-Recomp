# Recruitment and coordination plan

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

## Pages reference gallery integration

The mobile-facing [candidate Pages artwork gallery](https://gamesbyian.github.io/UR-Recomp/contributors/) is staged by `tools/contributor_gallery/stage.py` inside the existing Windows Visual Atlas site artifact. It contains the **three supplied original concept PNGs**, the two English traced SVGs and the three regional experimental SVGs, all copied byte-for-byte. It excludes box art and private inputs. Its URL is a **deployment target, not verified live** until an explicitly authorized existing atlas workflow dispatch with `deploy_pages=true` succeeds and HTTP checks show the page and all eight source image files render. Deployment requires Pages Actions source settings and the existing workflow's explicit gate. After verification, use this link in the final wording of lettering, itch.io and INAT recruitment posts and link direct `contributors/images/*` URLs for forum embeds where permitted. Keep Github source URLs for technical reference and avoid posting broken Pages links.
