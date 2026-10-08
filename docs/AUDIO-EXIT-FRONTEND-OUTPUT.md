# Packaged Windows audio after Modern Exit to Frontend

## Shipping question

The audio test must verify that using the real product-host
Exit-to-Frontend transition from an active 1P race does not leave the
returned playable frontend silent. This is distinct from guest Start
pause/resume and the independently proven Modern frozen pause -> Resume path.

The repository already owns a proven lifecycle script:
`tests/input/modern-exit-frontend-active.script`. The audio variant
`tests/input/audio-exit-frontend.script` keeps every existing input,
condition, and semantic dump in that canonical route, replacing only its
terminal `quit` with a long guest wait. The host-side
`UR_EXIT_FRONTEND_ACCEPTANCE=active` hook still drives the **actual**
session exit/reset from a genuinely observed race. The script must then
observe restored stock main-menu state 0xD7 and confirm ordinary guest
input into the usable rider selector 0x3C.

## Device-output acceptance

`tools/capture_exit_frontend_audio.py` launches the ordinary packaged
Windows `run-uniracers.cmd`, waits for the authoritative product markers
`UR_EXIT_FRONTEND REQUESTED`, `FRONTEND_READY`, and `FRONTEND_USABLE`,
plus the matching earlier race and later guest script checkpoints. It
permits the returned frontend to keep producing playback for four
wall-clock seconds, then intentionally closes the entire process tree.
Only **after** Windows closes SDL's exclusively held output file does it
analyze final one-second 44.1-kHz stereo S16LE device PCM.

A pass requires audible nonzero audio in *both* channels of that returned
frontend tail, not simply a loud race earlier in the capture. Raw audio
is deleted after reduction and is never uploaded. This validates a
production guest/host/SDL path, not merely model functions.

The focused pure checks live in
`tests/unit/test_capture_exit_frontend_audio.py`. The corresponding
`windows-exit-frontend-audio-probe.yml` Windows proof uses an already
verified main portable ZIP without compiling or repackaging the game.

## Evidence status

Pending the first native Windows run. A passed probe would establish
that normal stereo audio is restored after leaving the race and reaching
an actually usable frontend. It would **not** prove sample-exact menu
music, individual SFX or DSP fidelity, calibrated host/audio latency,
or speaker-level output. Those require independent targeted evidence.
