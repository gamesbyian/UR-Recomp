# Contributor operations: next executable actions

**Primary outreach link:** [Short recruitment landing](https://gamesbyian.github.io/UR-Recomp/contributors/), with compact role cards and one-click contribution intake. **Deeper optional gallery:** [Artwork references](https://gamesbyian.github.io/UR-Recomp/contributors/references/). Keep the compact page as every post's common entrypoint; original PNGs/SVGs remain at their prior `/contributors/images/` direct URLs. Publication follows the existing Visual Atlas Pages workflow.


**Status: draft-only scaffold.** This PR does not establish a mailbox, monitoring service, volunteer contact list, public game release, forum thread, mailed tester invitation or permanent upload endpoint.

1. Review and merge this PR; confirm two new GitHub issue forms render, then manually submit a nonprivate test issue and close it. Link the public contributor guide from any project showcase page once it exists.
2. Review approved reference pack. Capture genuine current Windows gameplay footage if available; prepare a clearly labeled experimental 3D turnaround and side-by-side lettering previews. Only use material with appropriate display rights.
3. Before attaching regional styling PNGs individually, inspect the three full-size GitHub images and label the French, Japanese and Russian concepts accurately; source naming remains neutral until this mapping is confirmed. Confirm asset relocation PR merges before the outreach PR, or the links will be broken.
5. Select a project sending identity (dedicated Gmail or user-designated alias), decide private Google Drive storage, and establish the restricted permissions. Do not publish personal contact coordinates by guessing.
5. Open drafts in docs/contributors/posts/, verify each forum's current rules and posting eligibility, then have a human publish permitted posts. Especially respect itch.io's no-AI-agents rule. Record actual live permalinks in campaign.json, never as a prediction. Do not send unsolicited messages to the publicly collected historic playtester leads.
6. Keep r/playmygame and r/DestroyMyGame drafts **blocked** until durable publicly shareable tested Windows build, exact hash receipt, footage and form exist. No GitHub Release exists as of 2026-11-09.
7. Add a private, testable Gmail/forum event collector and consent ledger without committing PII or credentials. Validate edit/delete behavior, duplicate messages, risky attachments, failed/uncertain sends, opt-outs, and provenance.
8. Connect release-driven opt-in mailings only after approved packages and verified sender/recipient consent exist. Record receipts and troubleshoot delivery failures before any retries.

Authority: docs/contributors/PLAN.md for outreach; OPERATIONS.md for communications; AGENTS.md, WORK-QUEUE.md and the release QA ledger remain engineering/acceptance owners. This handoff is active instructions only; keep historical outreach outcomes in separate private records.

## Remaining Pages publication check

Completed: PR #3307 was merged; both site assembly and GitHub Pages publishing succeeded in [run #42718635056](https://github.com/gamesbyian/UR-Recomp/actions/runs/42718635056). Gallery target: [https://gamesbyian.github.io/UR-Recomp/contributors/](https://gamesbyian.github.io/UR-Recomp/contributors/).

Outstanding: verify public HTTP access to the gallery and each of its three PNG and five SVG assets using an external browser, plus mobile layout. This environment cannot reach the Pages host over HTTP, so never invent such verification. Resolve anonymous concept source filename-to-language mapping before individual captions. The four image-focused proposed posts already contain the deployed gallery link; forum rules and human-only posting restrictions still apply. Windows playtester invitation posts remain blocked pending verified download.

## Recruitment site visual composition (current instruction)

Keep `/contributors/` a **short single-page mobile-first invitation**, with no large standalone artwork card. Use only the two exact owner-provided historical drawing files from `media/showcase/2026-10-20/graphpaper-source/` as compositional elements: `uniracers_graphpaper_logo.jpg` inside the fixed header and `uniracers_track_unicycle.jpg` as the fixed footer's bottom illustration. Stage byte-identical copies at `tools/contributor_gallery/source/`; never use an AI recreation or the combined blueprint background as a substitute. The main content rests on a **static graph-paper CSS background** and offers four short contributor cards plus other-project coordination. Maintain readable text and controls above the illustrated footer, even on 320–412 px phones; page content must not disappear underneath the fixed bars. Keep all old `/contributors/images/*` URLs and the secondary `/contributors/references/` gallery alive.

Confirm after deployment that the sketch logo reads visibly in the header, the racer/track is recognizable at the bottom and the background does not scroll with content. This visual acceptance is distinct from automated HTML/staging assertions. No box art or unqualified gameplay images belong in the invitation.

## 3D artist recruitment link (active)

Use [3D model viewer and downloads](https://gamesbyian.github.io/UR-Recomp/contributors/3d/) rather than the dense `HD-RACER-CHARACTER-RECONSTRUCTION.md` brief as the first-click artwork destination. The page links to the existing `model-review/` viewer and `model-review/visual-review.html` likeness inspection, and stages the source-owned `unicycle_shared_rig.scad` byte-for-byte for direct download. The standard Pages publish is model-free by default: the opt-in GLB export route is source/receipt-gated and must not be misrepresented as routinely published. When model GLBs are actually listed in the manifest, the page automatically offers their source-identified pose downloads. Check current live manifest and page appearance before outreach; the technical brief stays available for deeper discussion.

## Title-screen reconstruction reference updates

The four owner-supplied title-screen racer PNGs are sourced verbatim from `media/showcase/art-reconstruction/2026-11-09/title-screen-racer/` and displayed at `/contributors/3d/`. The 3D outreach posts should use the visually legible [3D entry page](https://gamesbyian.github.io/UR-Recomp/contributors/3d/) as their first art link, optionally embedding one approved full-size source PNG from the original GitHub source directory only where forum policy permits. Do not misidentify interpretive lines as original 1994 mesh seams or claim that these references describe today's 2026 model. Verify that all four images render and download after publishing; their original Git blob identity is recorded in the source directory README. They are not gameplay screenshots and should not replace the source-verified 3D model lab.

## Large original-image Pages publication

The contributor site now includes four full-resolution original PNGs from the title-screen racer study. The atlas site assembly remains independently verified before deployment. The GitHub Pages publication job must allow enough time for `syncing_files` on this larger artifact; its `timeout-minutes` is 15. A prior five-minute Pages publish was cancelled while syncing files, not by any failed artwork/staging validation ([run #42734776294](https://github.com/gamesbyian/UR-Recomp/actions/runs/42734776294)). Before describing updated images as live, require a successful `publish-pages` receipt for the exact merged source head and an external browser check where available. If Pages continues to time out, investigate artifact size and produce deterministic small preview derivatives while retaining the exact originals in the repo and offering links to them, rather than weakening source-provenance checks.

## Pages image-budget safeguard

The public `/contributors/3d/` gallery serves **deterministic downscaled RGB PNG previews**, generated with the dependency-free `tools/contributor_gallery/png_preview.py` during site staging. No full-resolution title-screen PNG is copied into the deployed Pages artifact. Each card links straight to the unchanged GitHub original, preserving the original image bytes and the previous art provenance. Keep preview generation bounded to 960×720, with per-preview and aggregate limits; any source format not safely supported must fail qualification. Deployment job timeout alone cannot circumvent `actions/deploy-pages@v4`'s own 10-minute polling limit. Prior large-art runs stuck at `syncing_files`; require actual completed `publish-pages` success before claiming a refreshed gallery is live.

## Box-art wheel contour studies (current outreach)

The owner-supplied wheel/fork contour JPEGs are preserved byte-for-byte in [the box-art study directory](https://github.com/gamesbyian/UR-Recomp/tree/main/media/showcase/art-reconstruction/2026-11-10/box-art-wheel-contours) and published directly under `/contributors/3d/box-art/`. Use the [short 3D volunteer gallery](https://gamesbyian.github.io/UR-Recomp/contributors/3d/) as the default first click for artists; it shows title-screen imagery and both new box-art close-ups, with links to the original GitHub files. Keep these *source artwork studies* separate from experimentally reconstructed 2026 meshes. Do not expand the ordinary recruitment homepage with dense art or claim that the traced lines identify confirmed original 1994 model pieces. Verify the artifact and live image URLs before forum publication.
