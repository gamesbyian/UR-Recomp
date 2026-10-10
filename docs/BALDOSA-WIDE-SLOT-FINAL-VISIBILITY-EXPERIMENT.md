# QA-08: exact final-visible rider pixels from native PPU counterfactuals

Status: **diagnostic source attribution only**. No shipping Remastered
342-wide admission, sprite replacement or guest logic changes.

## Why upstream isolated OBJ alpha cannot decide paint ownership

The existing Baldosa wide native source census captures actual PPU OBJ
slots 96–99 independently at guest frames 1856, 1872 and 1888 with
\`RemoveFromGame=0\`, and verifies the Original main raster is untouched.
This establishes source emission and ordering candidates, **not** which
pixels survived BG tiles, split-screen OAM priority, windows and color math
in the final frame. Even a matching source RGB in the stock raster is
not proof that the sprite owns that pixel.

## One native PPU single-slot counterfactual

The opt-in presenter accepts all of the following at once:

- \`UR_RACER_HD_WIDE_REMOVE_DIAGNOSTIC=counterfactual\`
- \`UR_RACER_HD_WIDE_REMOVE_SLOT=98\` (exactly one of 96–99)
- \`UR_RACER_HD_WIDE_REMOVE_FRAME=1856\` (exact guest frame)
- \`UR_BALDOSA_WS342_CAPTURE_DIR=<native capture directory>\`

It also requires a genuinely prepared 342×224 PPU world frame and the
existing \`UR_RACER_HD=1\` observer bridge. Its isolated diagnostic uses
the pinned PPU's existing per-OAM-slot capture and
\`kPpuOverlayFlag_RemoveFromGame\` **for that one frame only**. It
never invokes host HD painting, changes the ROM/guest memory, bypasses
the production full-pair overlap gate, or grants HD admission. The
existing source-only \`UR_RACER_HD_WIDE_SOURCE_SLOT\` mode is explicitly
mutually exclusive.

Run the same pinned original 2P guest input under three independent
native processes with isolated input/record data and exact guest-frame
CRCs: intact 342-wide stock, read-only isolated source slot, and this
one-slot PPU removal. In the removal process the expected log is:

\`UR_RACER_HD_WIDE_REMOVE_SLOT frame=1856 slot=98 status=armed guest_unchanged=1\`

The full-raster PNG/PAM must be **captured by the real native host**.
No synthetic pixels are accepted as real evidence.

## Fail-closed assessor

\`tools/check_baldosa_wide_slot_final_visibility.py\` consumes the
independent full stock PPU PAM, the source-only slot RGBA PAM, the
counterfactual full PPU PAM, all three complete guest CRC streams,
the counterfactual native log, and exact slot/frame identity.

It checks **every** 342×224 RGBA pixel. Changed stock-versus-removal
pixels are the actual post-PPU contributions of that slot at that
frame, independent of accidental color matches. Every changed pixel
must be contained within an emitted-alpha pixel from that exact
source slot; a difference outside that region or any guest CRC
disagreement fails. It reports which contributions are visible above
and below split line 112 and in the +43 left/right margins, plus SHA256s.

The oracle deliberately refuses a zero-change "success": a source-emitting
but totally hidden sprite is not HD-visible. The synthetic unit
regressions cover visible top/bottom/side pixels, source emission without
final visibility, unexplained changes, frame mismatch, malformed PAM,
unauthorized native execution and guest divergence.

## Next execution and release gates

Run this counterfactual against actual source-visible front OAM slots
(98 top, 96 bottom) at 1856 before expanding to all four slots and
moving frames. If the PPU flag affects more than isolated source pixels,
report a failed attribution, do not compensate with fabricated masks.
Only after **independently verified** all-slot, multi-frame final
visibility and exact same-frame Original compositing should the
author consider a production per-pixel 342-wide replacement compositor.

Even an exact counterfactual is necessary evidence, not sufficient
proof of correct Remastered art geometry, contact pose, colour math,
all other sprite depth, physical 4K or original-emulator parity.
