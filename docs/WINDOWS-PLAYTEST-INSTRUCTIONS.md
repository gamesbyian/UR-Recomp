# Owner Windows playtest preview: manual distribution and feedback

**Status: provisioning mechanism, not a shipped or QA-accepted release.** This guide is a player-facing wrapper around the already-established genuine Windows native Baldosa route; it does not create another product, game oracle, save layer or release quality gate. The [methodology audit](PROJECT-METHODOLOGY-AUDIT-20261015.md) identifies missing human hardware feedback as a P0 concern.

## Use the already-verified owner playtest ZIP (no new build needed)

The first independently source-pinned Windows owner preview already exists. **Prefer its retained, byte-verified artifact** when evaluating that historical candidate, rather than dispatching a new Windows runner job on today's `main`. New `main` is *not* the tested source revision of this nominated ZIP.

1. Open [the successful owner-package retention run 38828519791](https://github.com/gamesbyian/UR-Recomp/actions/runs/38828519791) and download Actions artifact **`retained-nominated-owner-playtest-11501a15`**, ID **`12016101293`**. Current artifact expiration: **2027-01-14 00:16 UTC**. You may need signed-in repository access.
2. The retained wrapper contains the **original four playtest files**, plus `ORIGINAL-ARTIFACT-RETENTION.json`. Read that retention receipt but do not put it into the portable game folder. The original four are the ROM-free `UR-Recomp-Baldosa-Windows-x64-ROMLESS.zip`, its `.sha256` sidecar, `PLAYTEST-PROVENANCE.json`, and `RELEASE-NOTES.md`.
3. Verify the *inner portable ZIP*, not the new outer Actions archive wrapper: SHA-256 **`5605aaf2ab1773b35385601564ee320ef065ce9bde091117b1e8e5a4661ed1f7`** (the companion `.sha256` file must agree). Original tested source **`11501a15dea38fa912335cfc63103ce3a7208001`**; embedded Windows EXE SHA-256 **`0701f72481531ad4f2803caadc62bbb072f292abef69f039edda004b01c18ea9`**. On systems with `sha256sum`, run `sha256sum -c UR-Recomp-Baldosa-Windows-x64-ROMLESS.zip.sha256`.
4. For independent QA auditing, [the successful original evidence retention run 38829200136](https://github.com/gamesbyian/UR-Recomp/actions/runs/38829200136) contains `retained-original-nominated-win32-qa-wrappers-11501a15` (artifact **`12016521644`**, same January 14, 2027 retention date). It includes the original nine independently SHA-checked CI evidence ZIP wrappers and `ORIGINAL-WRAPPER-RETENTION.json`. These are **QA archives, not additional player downloads**. Their original outer ZIP digests and sample limitations are recorded in [the source-pinned independent report](QA-EXACT-MAIN-WINDOWS-CROSS-ARTIFACT-DISPOSITION-20261015.md).
5. **Never attach copyrighted ROMs, SRAM, personal profiles or raw player data.** The verified portable ZIP is ROM-free. These retained artifacts keep the *existing* candidate and evidence available, not a newly nominated build, release certification or downloadable public GitHub Release.

### Only when a new source revision actually needs its own Windows build

Use [Manual ROM-free Windows technical playtest](https://github.com/gamesbyian/UR-Recomp/actions/workflows/manual-romfree-windows-playtest.yml) on `main`, choosing `verify_only`. It invokes the full source-bound native Windows build, existing real guest/process journeys, archive checks and candidate/executable binding. The resulting `verified-romfree-windows-playtest` has the *new* source SHA and ZIP digest and **must never be relabelled as the original nominated candidate**. `publish_provisional_preview` is a separate explicit human publishing decision, not an agent default or release-QA acceptance. No GitHub release has been published for the archived candidate.

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

For each issue record: **source/artifact identity (or playtest tag, if one is ever published) + exact ZIP SHA256**, Windows version, GPU/display resolution, physical pad model and connection, reproduction from a fresh/disposable user root, expected behaviour, observed behaviour, whether real stored profile/Records bytes were affected, and optionally a screenshot or short video. Share sanitized logs only; never attach a copyrighted ROM, full personal SRAM or the user's private profile catalog.

Prioritize immediately reproducible **P0 loss of player data, wrong results, broken physical controls or crashes**, then the missing native destinations and original/HD visual fidelity. QA remains responsible for deciding whether any captured evidence warrants a release-ledger witness. The workflow cannot turn a human playtest into a release pass by itself.
