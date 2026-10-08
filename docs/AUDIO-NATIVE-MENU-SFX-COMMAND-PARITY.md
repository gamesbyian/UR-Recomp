# Native Windows original-menu SFX identity parity

## Fidelity question

The existing stock SNES-reference archaeology has recovered original
frontend SFX command identities from the game's own WRAM command FIFO,
not by guessing which sound file is played. In
`analysis/generated/menu-sfx-ids.json`, the named Main Menu cursor
movements enqueue `087F, 0203` (volume/priority 0x7F and sound selector
3), while confirmation into the one-player rider menu enqueues
`084F, 0202` (0x4F and selector 2).

The original Windows audio acceptance proved the SNES-to-SDL playback
transport and real stereo presence at Main Menu, Now Playing, and Race.
That did **not** prove which SFX IDs the native game actually requested
during frontend navigation. A native implementation can produce continuous
music and still dispatch the wrong menu SFX.

## Source-owned acceptance

`tools/build_native_menu_sfx_route.py` imports and reuses the first
three already-validated `FRONTEND` events and `SETTLE` conditions
from `tools/probe_menu_sfx_ids.py`. There is no second authored route:
identical *original SNES guest input* on each side performs cursor Down,
cursor Up, and one-player Confirm. The native test runs in a fresh
Windows process against the existing verified portable package; the
original SNES audio driver queues commands in WRAM.

The test saves four full 128 KiB snapshots, with authoritative native
guest script checkpoints `e00-start`, `e01`, `e02`, `e03`.
`tools/check_native_menu_sfx_commands.py` requires:

- Exactly four observed in-order dump markers at increasing native guest
  frames, no fabricated readiness flags or memory writes.
- Exact stock menu transitions `D7,D7,D7,3C` and full 128 KiB snapshots.
- The **full two-word sound-command FIFO sequence** (including the
  08xx volume/priority prefix) for each named event, exactly equal to
  the independent `analysis/generated/menu-sfx-ids.json` reference.
- Exact original selector identities 3, 3, and 2, with the required
  post-event menu state.

Tests explicitly reject wrong command selectors, overwritten FIFO words,
short snapshots, reordered/faked guest markers and an invalid reference
inventory. The specialist Windows audio workflow reuses the same main
ZIP as its three-phase PCM test, does not recompile, and retains only
logs plus bounded comparison JSON, removing temporary copyrighted PCM.
It adds no new Actions job and touches no frontend/UI, sound mixer,
ROM content or product controls.

**Interpretation:** Matching proves the recompiled guest requested the
same original SFX IDs and 08xx prefixes for those three canonical
frontend inputs. It does **not** prove the SPC700 consumed each port
command at the correct cycle, matched BRR sample decoding, DSP envelope/
echo synthesis or analog auditory similarity. Those require separate
APU handshake and audio waveform evidence.

The run is unproven until the *actual packaged-Windows specialist test*
passes this new gate. Its failure would name a concrete source-command
regression rather than weakening the source reference.
