# Owner Windows playtest preview: manual distribution and feedback

**Status: provisioning mechanism, not a shipped or QA-accepted release.** This guide is a player-facing wrapper around the already-established genuine Windows native Baldosa route; it does not create another product, game oracle, save layer or release quality gate. The [methodology audit](PROJECT-METHODOLOGY-AUDIT-20261015.md) identifies missing human hardware feedback as a P0 concern.

## Produce a downloadable, source-bound preview

1. In GitHub Actions choose **Manual ROM-free Windows technical playtest**, select the **main** branch and `verify_only`. The workflow invokes the existing full Windows bridge once, with its eleven original Win32 tests, real startup probes, candidate/executable binding and SHA receipts.
2. From that run download **verified-romfree-windows-playtest**. It contains one portable ZIP, its .sha256, `PLAYTEST-PROVENANCE.json` and user-facing release notes. Verify `sha256sum -c UR-Recomp-Baldosa-Windows-x64-ROMLESS.zip.sha256` on the downloaded file.
3. To make a durable GitHub **prerelease**, dispatch the same workflow on main with **publish_provisional_preview** instead. This is an explicit human publishing decision, not an automatic nightly job. It repeats the exact-source Windows build and verifies both the zipped executable and package, then creates an immutable `playtest-<source-SHA-prefix>` GitHub prerelease. It will refuse an existing tag rather than overwrite it. Its GitHub Release is deliberately labelled **ROM-free, provisional, not an accepted beta**.
4. **Never attach game ROMs, SRAM, personal profiles or raw player data.** This technical preview is a candidate to *play and critique*, not an accepted shipping package. Repository history includes research ROM material and must not be made public as a shortcut to publishing it. The preview ZIP itself is independently audited ROM-free.

The user must supply a verified personal **Uniracers USA** ROM dump named `Uniracers_USA.sfc` alongside the extracted game executable, then launch `run-baldosa-modern.cmd` on Windows x64. The launcher rejects missing or wrong-ROM bytes and uses a per-user data directory outside the package. For an early playtest use a disposable data root (via `UR_RECOMP_USER_DATA_ROOT`) rather than existing valued saves. Preserve the SHA and playtest revision when reporting defects.

## A focused one-hour owner playtest

This is not a replacement for the independent, fixed [release QA journeys](QA-PLAYER-JOURNEYS.md) or [gate ledger](RELEASE-QUALITY-LEDGER.json). Record *actual physical* hardware and player observations that scripts cannot supply.

| Window | Human activity and what to note |
|---|---|
| First 10 minutes | Fresh ZIP extraction, actual CMD startup, personal ROM admission; create a racer using real controller or keyboard, quit and cold-start; record any confusion or missing prompt |
| Next 10 minutes | Play a genuine 1P race, finish, inspect visible winner/time/Records; note audio, control latency, errors and progress after full process exit |
| Next 15 minutes | Connect **two physical controllers**, create/join two distinct players and run a complete 2P race through both result perspectives; note focus, one-pad cross-control, splitscreen, sound and whether both players can reopen Records |
| Next 10 minutes | Open Practice (D-pad up/down changes course, left/right changes tour), enter several courses from different tours and kinds (race, circuit, stunt), return/quit/restart and inspect saved profile integrity; record unavailable choices or confusing UI explicitly |
| Final 15 minutes | Open Options and change Display (windowed/borderless/fullscreen), VSync and Volume, quit and restart to confirm they persist, and try a deliberately wrong or missing ROM to judge the refusal message; switch Original and accessible presentation options **only where actually available**; inspect 16:9/world margins, text/HUD density, real monitor resolution/4K if available, pause/restart/quit; submit the three most painful player-visible deficiencies |

**Known upfront:** native Practice offers the courses the original game has unlocked for your racer (20 on a new save, up to the 40 ordinary courses; secret Hunter stays closed) rather than all 45 from the start, and Options contains only the three controls this build genuinely applies (Display, VSync, Volume) plus a controls help page. The historical procedural HD art has not received current artistic sign-off. Real physical audio/display/two-pad, complete original/native event parity (0/45 accepted) and power-loss-safe persistence are not yet release-certified. Report these accurately rather than treating a preview launch as certification.

### Compact feedback record

For each issue record: **playtest release tag + exact ZIP SHA256**, Windows version, GPU/display resolution, physical pad model and connection, reproduction from a fresh/disposable user root, expected behaviour, observed behaviour, whether real stored profile/Records bytes were affected, and optionally a screenshot or short video. Share sanitized logs only; never attach a copyrighted ROM, full personal SRAM or the user's private profile catalog.

Prioritize immediately reproducible **P0 loss of player data, wrong results, broken physical controls or crashes**, then the missing native destinations and original/HD visual fidelity. QA remains responsible for deciding whether any captured evidence warrants a release-ledger witness. The workflow cannot turn a human playtest into a release pass by itself.
