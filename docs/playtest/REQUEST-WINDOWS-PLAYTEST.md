# Request a verified current-main Windows playtest build

**This file is a deliberate, PR-driven dispatch switch, not a release gate.**

When an authorized agent or maintainer needs an immutable, ROM-free Windows candidate for physical H01–H07 testing, open a PR that updates the request record below, review it, then merge it to **main**. Only a `push` to `main` touching **this exact file** triggers the existing `.github/workflows/manual-romfree-windows-playtest.yml` to build its original 13-journey Windows candidate and preserve the four-file `verified-romfree-windows-playtest` Actions artifact. The resulting `GITHUB_SHA` is the merge commit containing the request, not the preceding commit or a PR synthetic test-merge.

This is a build **request**, not an acceptance claim. Do not run it for every PR or use it to replace required source integration, hosted Windows checks or physical hardware tests. The trigger cannot publish prereleases: only an explicit manual `workflow_dispatch` with `publish_provisional_preview` can enter that job. Preserve the inner playable ZIP/PE SHA-256 and `PLAYTEST-PROVENANCE.json`; do not publicize private ROMs or user saves.

## Next build request

- Request sequence: **3** (Windows physical candidate after Quick Practice and Unicode save-lock integration)
- Requested reason: After #2789 independently qualifies and merges the real non-ACP Unicode P1/P2 plus source-earned result and fresh-process Records journey, produce one exact-current-main ROM-free Windows x64 physical-test candidate that also contains the already merged #2787 source Tour settlement, #2788 actual Windows Quick Practice scene/release-gap fix, and #2790 native UTF-16 save-lock repair. Those fixes change real playable menu/input and profile save behavior absent from the older #2770 ROM-free physical ZIP. Reuse the existing 13-journey qualified Windows bridge and four-file verified playtest artifact path, not a second build pipeline. Preserve actual merged-main Git commit identity, verified playable inner ZIP/PE SHA-256, exact original source/ROM boundary and provenance JSON before nominating for H01–H07; require the same-PE cold non-ACP profile/Options/Records evidence including real physical two-pad, keyboard wake, audio and display independently when humans run it. The sequence-2 historical candidate remains valid for its own source epoch until expiry, but cannot certify newer fixes. This is one consolidated product-fix verification, not a build for a documentation timestamp or release gate credit.
- Expected candidate: The exact `main` merge commit of **this** request PR (not the setup PR or test merge)
- Requested by: Authorized project maintainer/agent
- Required workflow outcome: `verify_only` equivalent, temporary Actions artifact, **zero release gate credit**

To request a build, increment the sequence and replace the reason in a distinct PR. Changing only this file in the same PR that installs the workflow will not trigger the new push path until the workflow exists on the default branch; the next request PR does.
