# Uniracers contributor coordination

**Primary outreach link:** [Short recruitment landing](https://gamesbyian.github.io/UR-Recomp/contributors/), with compact role cards and one-click contribution intake. **Deeper optional gallery:** [Artwork references](https://gamesbyian.github.io/UR-Recomp/contributors/references/). Keep the compact page as every post's common entrypoint; original PNGs/SVGs remain at their prior `/contributors/images/` direct URLs. Publication follows the existing Visual Atlas Pages workflow.


Unofficial Uniracers / Unirally SNES-to-Windows recreation. Contributions are voluntary, unpaid and optional. A single glyph correction, 3D review, code-review packet or Windows test report is welcome. No expectation of permanent team membership, compensation, revenue share or employment.

## Opportunities

- **3D character artist:** reconstruct/refine the articulated racing unicycle from original sprite/art references and the existing experimental five-parent model. Start with the [character brief](https://github.com/gamesbyian/UR-Recomp/blob/main/docs/HD-RACER-CHARACTER-RECONSTRUCTION.md) and [experimental model review source](https://github.com/gamesbyian/UR-Recomp/blob/main/tools/art/model-review/visual-review.html). The 2026 model is not a recovered original 1994 mesh or approved finished art.
- **Regional logo/lettering artist or language reviewer:** preserve the original English wordmarks' style in other languages. See [Uniracers English](https://github.com/gamesbyian/UR-Recomp/blob/main/assets/branding/uniracers-box-wordmark-traced.svg), [Unirally English](https://github.com/gamesbyian/UR-Recomp/blob/main/assets/branding/unirally-box-wordmark-traced.svg), [Japanese](https://github.com/gamesbyian/UR-Recomp/blob/main/assets/branding/uniracers-japanese-katakana-wordmark.svg), [Russian](https://github.com/gamesbyian/UR-Recomp/blob/main/assets/branding/unirally-russian-cyrillic-wordmark.svg) and [French](https://github.com/gamesbyian/UR-Recomp/blob/main/assets/branding/unirally-french-wordmark.svg). Regional versions are experimental, not approved canonical translations.
  The three new [concept PNGs](https://github.com/gamesbyian/UR-Recomp/tree/main/assets/branding/concepts) are useful visual ideas for French, Japanese and Russian, separate from the working SVGs. Their source-file language mapping awaits direct source-image verification.
- **Agent operators and reviewers:** donate your own agent hours plus appropriate human supervision, governed by [AGENTS.md](https://github.com/gamesbyian/UR-Recomp/blob/main/AGENTS.md) and the [live engineering queue](https://github.com/gamesbyian/UR-Recomp/blob/main/docs/WORK-QUEUE.md). Normal PR review and source-bound QA remain mandatory. No external contributor receives automatic repository write/merge privileges.
- **Windows playtesters:** review the [expert testing protocol](https://github.com/gamesbyian/UR-Recomp/blob/main/docs/EXPERT-PLAYTEST-PROTOCOL.md) and [Windows H01–H07 instructions](https://github.com/gamesbyian/UR-Recomp/blob/main/docs/WINDOWS-PLAYTEST-INSTRUCTIONS.md). **No permanent public qualified Windows Release is currently available.** A successful Actions artifact is not automatically a safe public download.
- **Other Uniracers/Unirally project maintainers:** we are interested in research exchanges, compatible tools, deduplicating effort and independent cooperation. We know the [Baldosa project](https://github.com/baldosa/uniracers-recomp) and [malmazuke project](https://github.com/malmazuke/unirally-reconstruction); that is not a claim of partnership.

After this branch is merged, use the [public contributor interest form](https://github.com/gamesbyian/UR-Recomp/issues/new?template=contributor-interest.yml) or reply in the relevant forum thread. **GitHub issues are public:** never include private email addresses, credentials, personal identifiers or unapproved assets. A dedicated project mailbox/private file route will be announced only after it actually exists.

Project links: [recruitment plan](PLAN.md), [site-specific outreach drafts](posts/), [asset reference pack](REFERENCE-PACK.md), [intake and correspondence contract](OPERATIONS.md), [current handoff](HANDOFF.md). These are recruitment instructions, **not** a competing engineering work queue or a release acceptance authority.

## Visual recruitment gallery

The [GitHub Pages artwork gallery](https://gamesbyian.github.io/UR-Recomp/contributors/) was published through [the successful site deployment run](https://github.com/gamesbyian/UR-Recomp/actions/runs/42718635056). It displays the three supplied concept PNGs, original English wordmarks and experimental regional vectors. Confirm public gallery and image availability in an internet-connected browser before external posting.

## Accessible 3D reconstruction entrypoint

The [brief 3D model and viewer page](https://gamesbyian.github.io/UR-Recomp/contributors/3d/) is the public-first destination for artists. It links to the existing interactive model reviewer, visual likeness comparisons and a byte-identical downloadable experimental OpenSCAD rig. Published pose GLBs appear as downloads only when the source-verified model manifest actually lists them. The technical character reconstruction brief remains a secondary detail link. An unapproved 2026 model is not a recovered original 1994 3D mesh.

## Public contact options and current 3D model

All five recruitment roles now provide a no-account-required email link to **ianmakesjokes@gmail.com**, the project contact address explicitly approved by the owner for public volunteer inquiries. GitHub issue intake is retained as an optional alternative. Replies must respect privacy, opt-outs, and contributor permissions. Do not publish email messages, attachments or addresses in issues or source control without explicit consent.

The Pages 3D reviewer is configured to generate source-verified, explicitly **unapproved experimental** five-pose GLB exports from the current checked-out `main` when the contributor site is republished. The current model is the source-authored `tools/art/candidates/unicycle_shared_rig.scad`, not recovered 1994 geometry. Publication checks must confirm the manifest, GLB SHA-256 records, downloads and visual load before artist outreach promises a hosted model. A failed export or deployment is a release blocker for these public claims; never mislabel a blank lab as a model viewer.


## Existing Windows builds and no-account contact

Volunteer Windows testing is **currently useful**. Source-identified, ROM-free Windows x64 experimental test packages already exist, and current-main candidates can be requested through the existing controlled playtest build process. Interested testers can use the email links on the landing page without GitHub; the maintainer provides a source-verified package and instructions only once the exact build has been checked. This does not announce a finished, publicly downloadable release.

The lettering references and 3D artist detail pages share the main website's sketch-logo header, graph-paper background and sketched track/racer footer. Each specialty page presents email and GitHub as equal invitations, with privacy guidance for public GitHub issues.

## Current visitor-facing recruitment paths

All public recruitment subpages follow the same static cream graph-paper, original sketched-logo header, and bottom-track illustration as the main page. The regional lettering reference gallery is `/contributors/references/`, model viewing and assets are `/contributors/3d/`, and the approachable Windows playtesting explanation is `/contributors/playtest/`. Each accepts volunteers by email or public GitHub issue with equal visual prominence. Keep the option to email the owner visible, and check direct links and fixed-header/footer readability on a small phone after each redesign. Do not funnel non-GitHub visitors into GitHub-only instructions.

**Playtesting status:** Experimental native Windows x64 build artifacts have been produced and independently byte-audited; source-specific candidates can be supplied to human testers. A generally available finished public release is not yet approved. Do not advertise an expired or obsolete artifact as a current download: check its source SHA, ZIP/PE digests, expiration and owner authorization before sending any particular build. Keep physical Windows audio/input/display observations separate from hosted CI qualification.
