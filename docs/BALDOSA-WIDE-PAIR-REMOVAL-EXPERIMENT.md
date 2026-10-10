# QA-08: distinguish same-colour overlapping source using a two-slot PPU counterfactual

Status: **diagnostic mechanism, no live paired execution accepted yet**.

The original native 342-wide screenshot at frame 1856 revealed fourteen
pixels where front slot 98 and rear slot 99 emitted identical RGB.
A single-slot removal leaves these pixels unchanged; that does not mean
the front source is hidden. Existing native source, single-slot removal
and three-process CRC checks demonstrate only **observable final RGB
change**, not an unambiguous per-slot ownership mask.

## Narrow additional native experiment

The first-party HD presenter, already used as Baldosa's read-only
native diagnostic, now supports an explicitly separate **two-slot**
counterfactual at one guest frame:

- `UR_RACER_HD_WIDE_REMOVE_DIAGNOSTIC=counterfactual`
- `UR_RACER_HD_WIDE_REMOVE_PAIR=98-99` or `96-97` only
- `UR_RACER_HD_WIDE_REMOVE_FRAME=1856`
- `UR_BALDOSA_WS342_CAPTURE_DIR=<actual native capture directory>`

This is mutually exclusive with both `UR_RACER_HD_WIDE_REMOVE_SLOT`
and the source-only `UR_RACER_HD_WIDE_SOURCE_SLOT` mode. It requires
a real 342×224 prepared PPU frame, working `UR_RACER_HD=1` host
bridge, and the exact named frame. Only then can it set
`kPpuOverlayFlag_RemoveFromGame` for the contiguous **two-slot**
range. Production Remastered admission is untouched; no authored
sprite pixels are painted by the diagnostic. Other frames preserve
the stock renderer. The marker is:

`UR_RACER_HD_WIDE_REMOVE_PAIR frame=1856 slots=98-99 status=armed guest_unchanged=1`

The pair-removal experiment must use an independent full native 2P
route with the same isolated ROM/SRAM/input and guest CRC sequence as
the stock, source-only slot98, source-only slot99 and pair-removed
processes. A real PPU 342×224 capture of the pair-removed result is
required, not a fabricated overlay.

## Four-process full-pixel gate

`tools/check_baldosa_wide_pair_final_visibility.py` imports the
existing native 342-wide PAM parser. It checks exact source/stock/
removed frame identities, all **four complete native guest CRC
streams**, the unique authorized paired PPU marker, and every pixel
of the final Original frame versus paired counterfactual. Every
changed pixel must lie in the **union** of the two independent
source alpha planes; one changed pixel outside either footprint
fails. The report separately retains overlap, top/bottom changes,
hashes and no HD release credit. Synthetic unit tests cover missing
authority, foreign pixels, truncated rasters and guest divergence.

A positive pair-removed change at any of the fourteen coincident
front/rear RGB positions would demonstrate that at least one racer
source was responsible for that final colour. Combined with
verified OAM priority, source order and a rear-only removal
control it could help isolate the exact winner; **pair removal alone
does not prove which source owned the colour**. Do not infer an
authoritative HD mask without closing that remaining attribution
gap.

Next native execution: run frame 1856 for pair 98-99 against the
existing separate stock/source source planes, preserving the proven
production overlap guard. If successful, repeat the bottom pair,
later moving frames, and compare an isolated *rear-only* removal
to distinguish exact winners. None of these diagnostics should
be shipped as a graphics mode or exposed to Modern product options.
