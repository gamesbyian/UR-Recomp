# QA-08: reconstruct source PPU beam-order colour-state knowledge

**Correction, October 13, 2026.** The older colour-journal analysis sorted raw
SNES scanline tags numerically 0..261. That ordering does not follow the
original pinned SNESRecomp PPU's field start at beam V=225. Source:
`baldosa/snesrecomp@075fbe4c`,
`runner/src/snes/ppu.c` functions `raster_key`,
`ppu_rasterFieldBoundary`, `ppu_rasterApplyLine`, and
`ppu_rasterDebugDump`. Its **true chronology** is tags
**225..261, 0..224**. Writes in the blanking interval **225..261 precede**
visible tagged lines 0..223, and may alter the state at the first visible
line. A numeric 0..261 interval may describe which raw tags had each value,
but **cannot be used as the effective visible-line colour-state history**.

The new `tools/qa08_ppu_beam_colour_state.py` builds a beam-key chronology,
and a separate visible-tag summary, using the original journal's ordered
register writes. The existing strict post-GO 2P checker adds the derived
report to `field_register_journals.*.beam_order_colour_knowledge` **after**
all unchanged Original PPU/frame SHA-256, full 2,473 guest CRC and native
journal admissibility checks. The prior numeric-tag diagnostic remains
available for backward compatibility but its arithmetic order must **not**
be interpreted as the render order.

Three register semantics are source-verified against pinned `ppu.c`:
- `$2131/CGADSUB` baseline *is* in the native field's `base` object;
- `$2130/CGWSEL` baseline *is not* in that limited JSON `base` object;
- `$2132/COLDATA` uses data bits 5/6/7 as independent RGB-channel write
  selectors; the initial RGB15 fixed-colour operand **is not** exported as
  a field baseline. Unknown channels remain `null` until the first matching
  channel write; a full RGB15 value is not invented before all three
  components have been written.

The **end-of-render sampled** `CGWSEL` and RGB15 are not substituted as
the completed field's pre-render baseline. The tag-wise report retains
source event indices and same-line writes in their original order,
with the last write to a register at a tag determining its
post-write **whole-line replay approximation**. The report can be
regenerated from the already existing journal experiment; it requires
**no new native process**, GHA campaign, guest mutation or feature flag.

A hypothetical `$2132=0x2D` at native tag0 establishes only **red 13**
(`0x0D`) at that tag; green/blue remain unknown until selected. A
hypothetical `$2131` write at tag230 must affect the native tagged
line0 state despite the old numeric sorting. Adversarial synthetic
tests exercise both and reject invalid or reversed beam chronology.

**Evidence boundary:** Neither the native tag numbers' precise mapping
to photographed screenshot rows, per-pixel mid-scanline write effects,
subscreen selection, window masks, OBJ-vs-BG priority, nor the final
source of the repeated 13-red5 discrepancies is established. The
whole-line replay approximation is explicitly the pinned **native
renderer** policy, not a general assertion about physical SNES timing.
It does not approve HD character likeness, destructive PPU OBJ removal
or a Windows graphics release. Original 256x224, 7:6 PAR, 4x fallback
and authentic 342-wide course materialization remain unchanged.

## Follow-on: original saved CGWSEL and fixed-RGB field baselines

The pinned `Ppu` struct in `baldosa/snesrecomp@075fbe4c` stores both
`fixedColor` and `cgwsel` in the existing 0x40-byte field register
snapshot `inidisp..cgwsel`. Its `f->regs` already captures the exact
V=225 values. Only the original `raster_dump_field` debug JSON omitted
them. The new `qa08_patch_ppu_field_colour_baselines.py` changes that
**read-only diagnostic printer alone**: `RJ_OFF(cgwsel)` and
`memcpy(... RJ_OFF(fixedColor) ...)` retrieve the already saved values.
The patch fails closed on source/layout drift or duplicate application.

The **existing** 2P native graphics route applies this after its
already-required split-world PPU source patch, before recompilation. Its
unchanged whole-Original raster and 2,473 native guest CRC gates still
apply. The journal checker now additionally **requires** both completed
and recording field baselines on that native route. It will reject a
supposed new native pass if the two values were not captured.

The offline beam-order decoder remains backward-compatible with old
journals: missing field baselines stay unknown, and only explicitly
written channels become known. The extended genuine source journal,
when available, supplies all three field-start registers and true
scanline-ordered state. That enables a narrower *register-path*
adjudication of the upper/lower 13-red5 signature, **not** independently
proven pixel arithmetic, subscreen/window priority, output-Y timing,
authored Remastered art or full game acceptance. The next real AOT
and its immutable original raster/CRC receipts must establish the
new witness; synthetic unit tests do not.
