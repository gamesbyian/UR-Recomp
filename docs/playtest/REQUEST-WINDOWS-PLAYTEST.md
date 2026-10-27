# Request a verified current-main Windows playtest build

**This file is a deliberate, PR-driven dispatch switch, not a release gate.**

When an authorized agent or maintainer needs an immutable, ROM-free Windows candidate for physical H01–H07 testing, open a PR that updates the request record below, review it, then merge it to **main**. Only a `push` to `main` touching **this exact file** triggers the existing `.github/workflows/manual-romfree-windows-playtest.yml` to build its original 13-journey Windows candidate and preserve the four-file `verified-romfree-windows-playtest` Actions artifact. The resulting `GITHUB_SHA` is the merge commit containing the request, not the preceding commit or a PR synthetic test-merge.

This is a build **request**, not an acceptance claim. Do not run it for every PR or use it to replace required source integration, hosted Windows checks or physical hardware tests. The trigger cannot publish prereleases: only an explicit manual `workflow_dispatch` with `publish_provisional_preview` can enter that job. Preserve the inner playable ZIP/PE SHA-256 and `PLAYTEST-PROVENANCE.json`; do not publicize private ROMs or user saves.

## Next build request

- Request sequence: **1** (first requested integrated-main technical playtest build)
- Requested reason: Generate the first integrated-main verified ROM-free Windows x64 candidate for upcoming physical H01–H07 sessions, now that P2 title, original attract and Unicode Options fixes are merged
- Expected candidate: The exact `main` merge commit of **this** request PR (not the setup PR or test merge)
- Requested by: Authorized project maintainer/agent
- Required workflow outcome: `verify_only` equivalent, temporary Actions artifact, **zero release gate credit**

To request a build, increment the sequence and replace the reason in a distinct PR. Changing only this file in the same PR that installs the workflow will not trigger the new push path until the workflow exists on the default branch; the next request PR does.
