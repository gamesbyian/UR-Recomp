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

The first native capture
[run 37756144443](https://github.com/gamesbyian/UR-Recomp/actions/runs/37756144443)
reached the genuine race (guest frame 1044), product Exit-to-Frontend
success (surface=0, applied pause=0/exit=0), reinitialized main menu
(guest frame 502) and usable rider menu (guest frame 565). Its original
reducer incorrectly treated enum 0 as a failure and assumed the guest
frame counter continued monotonically through the guest reboot. Neither
assumption was valid. It was corrected without changing the game, reset
mechanics or stock guest input route.

The corrected **real packaged-Windows** proof
[run 37756388629](https://github.com/gamesbyian/UR-Recomp/actions/runs/37756388629)
**passed**, using verified main portable package from source run
37754866279. The returned usable frontend produced one full second
of genuine SDL S16LE stereo output with left RMS **4478.86** and
right RMS **4726.82**. Complete device capture: 1,372,160 stereo
frames at 44,100 Hz, whole-stream RMS 2930.77, nonzero fraction 0.8057.
Original canonical guest checkpoints and authoritative host exit/ready/
usable markers all matched, and no raw copyrighted PCM was retained
in the uploaded bounded evidence.

This closes minimal audible **race Exit-to-Frontend restoration**
on the shipping Windows execution path. The results do **not** prove
sample-exact menu music, individual SFX/DSP fidelity, calibrated
transition latency, transient-free speaker playback, or hardware recovery.
