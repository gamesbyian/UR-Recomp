# Resume / Restart Tour continuation conversation transcript

Captured: 2026-10-05 through 2026-10-06

Source: project conversation **Implement Resume Restart Flow** and its resumed sessions.

The user assigned the next player-facing profile/progression continuation step above the already-shipping profile-local unfinished-tour state. The constraint was to expose a coherent Resume Tour and confirmed Restart Tour flow without creating another save format, picker, progression authority or Tour model.

The completed flow reuses the existing stock MAIN → RIDER → TOUR → TRACK route. Resume alone may restore the validated five-byte continuation. Restart suppresses restoration and retires the continuation only after the persisted context still matches, settled TRACK_SELECT is reached and a title-owned read-only predicate proves stock actually performed its historical qualification-row wipe. Cancellation and failures preserve or restore resumable progress.

Fresh-process acceptance covers player-facing Resume, confirmed Restart, cancellation and failure behavior. The work merged through PR #522. The separation between the earlier pure policy/model work and later UI wiring made this a relatively safe multi-agent handoff.
