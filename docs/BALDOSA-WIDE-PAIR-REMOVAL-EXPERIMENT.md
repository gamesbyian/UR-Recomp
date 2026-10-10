# QA-08: distinguish same-colour overlapping source using a two-slot PPU counterfactual

Status: **actual native pair-removal acceptance passed at guest frame 1856**. This is observational evidence, not HD replacement permission.

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

## Pinned native 98/99 execution (strict acceptance attempt)

The existing Baldosa AOT job now independently executes the 2P
`race_2p_split` route with the diagnostic `98-99` pair removed only
at guest frame **1856**. It reuses the existing real Original 342-wide
unmodified stock PPU image and both separately extracted source-only
OAM planes. All **four separately executed complete guest CRC streams**
must be identical and the unique `REMOVE_PAIR` marker must be present.

The exact 342×224 native pair-removed PPU capture is compared
pixel by pixel with stock. Its changed-pixel footprint must remain
inside the union of the front and rear emitted source alpha masks.
The report, actual pair-removed PAM and native log are retained in
the same existing Baldosa CI artifact, with no extra workflow and no
production HD admission. The first accepted run should be used to
investigate the **14 equal-colour front/rear overlap pixels** that
were invisible to the earlier slot-98-only counterfactual.

**Do not claim pair attribution, a solution to the 14-pixel ambiguity,
or any release permission until the native full-process report passes.**
The pair result identifies only the union of the two source slots.

## Verified real native paired-rider result, October 10

Merged [PR #1185](https://github.com/gamesbyian/UR-Recomp/pull/1185),
commit `62e48c9946379e8d8c54c21492214b5e5d1ce4ec`, passed all
Baldosa AOT and tooling checks. Its AOT
[run 38077924397](https://github.com/gamesbyian/UR-Recomp/actions/runs/38077924397)
retained native artifact **11679444298**, including separately executed
stock, slot-98 read-only source, slot-99 read-only source and pair-deleted
native PPU framebuffer. The corresponding JSON file is
`baldosa-evidence/ws342_pair98_99_final_visibility_1856.json`.

| Guest frame 1856, upper viewport | Measured pixels |
|---|---:|
| Original slot-98 emitted | 321 |
| Original slot-99 emitted | 319 |
| Both source masks overlap | 157 |
| Union of source masks | **483** |
| Changed after deleting slot 98 alone | 307 |
| Changed after deleting **both** slots 98–99 | **483** |
| Changed outside union of source masks | **0** |

The native report verifies all **four independently executed complete
guest CRC streams are identical**, the exact paired PPU removal marker
was armed and the 342×224 Original source/controller frame names match.
All 483 final changes occurred in the **top** split view and none in the
bottom. This is a genuine native PPU experiment, not a generated overlay.

The prior single-slot source comparison identified **14 positions** at
which both slots emitted identical RGB and deletion of front slot 98
changed no final colour. With the native pair removal, **all fourteen**
of those positions now change colour, demonstrating the **pair-level
causal influence** hidden from a single colour-difference mask.
In fact every observed pixel in the union changed when both racers
were removed.

The pair report includes authentic SHA256 RGBA digests:

- Stock PPU: `0e956fac212cb7413a32ee2a0de318540e58cfd5f2b7610472c2573ab6719dd9`
- Slot 98 source: `5122c86a797710965bf17caf99677ca2cf738fbff852101a9469ff66750fc2c5`
- Slot 99 source: `658b214071df7637abc308a0222e37cb15753b72c4ef42cf4c084311c031ec8f`
- Original PPU without both: `440b0fd56c4fcdad4b9d5c64bf85738876eb61e7fcdcc867074943df49a9df3d`

**Still blocked:** exact individual winner identity, other frames and
positions, all BG/window/screen colour math, safe authored HD rider
replacement and complete-event fidelity. Do not translate pair-level
colour causality into destructive 342-wide HD sprite admission.
The next direct control is the independent rear-only slot-99 removal
in PR #1197, followed by the authenticated six-plane classification
in PR #1198.
