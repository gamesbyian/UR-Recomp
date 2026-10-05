# Local Completed-Run Browser and Replay

Status: first usable Windows x64 Modern product browser implemented. Switch is out of scope.

## Player-facing behavior

During a supported Modern one-player timed Race context, pause the game and open **Local Runs** with **Ctrl+B** on keyboard or **X** on a gamepad. The browser is host-owned and profile-scoped.

The list is newest-first and shows the stored chronological order, course, local run date derived from the canonical store timestamp, exact 60 Hz finish time, and **PB** / **PREV** status when those canonical selectors apply. Corrupt, malformed, unsupported-version, I/O-failed, and playback-incompatible `.urrun` artifacts remain visible as disabled rows instead of disappearing into the valid list.

Up/Down or the D-pad moves among playable records while skipping disabled rows. Enter/A launches the selected run. Escape/B returns to the existing paused product surface.

## Replay launch

Replay launch does not add a simulation model. The selected `.urrun` is validated, exported with `encode_completed_run_input_file()`, and staged as the same `INPUT_FILE` grammar already used by deterministic replay acceptance.

A narrow framework hook replaces the current deterministic input stream and leaves it inert until the title arms a race-relative origin. Launch then reuses the existing Modern **Restart Race** lifecycle anchor and resumes through the existing pause path. No course state, racer state, timer state, or arbitrary WRAM is written by the browser.

While a selected replay is running, the wrapper bypasses ordinary completed-run capture so watching a run cannot append a duplicate artifact or perturb Previous/PB ordering. At the observed stock results surface, deterministic input is cleared, the ordinary Modern host is reconciled once, the game is paused, the catalog is refreshed, and the player returns to Local Runs. From there Escape/B returns to the ordinary pause/results surface, where the existing **Exit Frontend** path remains available.

## Ownership and failure policy

The browser is a wrapper around the existing Modern host callbacks rather than a parallel frontend stack. Normal input, pause, options, rendering, restart, and frontend behavior delegate to the existing host unchanged when the browser is closed.

Authentic mode does not expose the browser or replay launch. Two-player/VS and unsupported timed-event contexts remain inert. Playback-incompatible or invalid artifacts cannot be selected or launched. A failure to stage input, load the canonical replay stream, or restore the existing restart anchor fails closed and leaves gameplay authority with the normal guest.

The browser consumes `.urrun` records only. It does not read or modify `.urghost` rendering/projection internals.

## Acceptance

Focused native tests cover newest-first catalog ordering, canonical Previous/PB annotation, invalid/incompatible-row visibility, selection skipping, canonical replay-input staging, invalid-record rejection, and replay return/cancel lifecycle.

The existing completed-run replay workflow now includes those tests and rebuilds the Windows-style native product whenever the browser, replay controller, host wrapper, or live canonical-input reload seam changes. It also seeds one valid captured `.urrun` plus a deliberately checksum-damaged `.urrun` into an acceptance-only run directory, follows the real Modern 1P route, opens Local Runs through the actual wrapper, requires the catalog to report two stored / one playable, launches the valid run through Restart + the canonical live input injector, requires the stock results return, and proves the directory still contains exactly those two `.urrun` files afterward. The established fresh-process deterministic replay comparison remains the independent simulation-equivalence proof.
