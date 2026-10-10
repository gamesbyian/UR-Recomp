# QA-08: source overlap causal interaction, not winner identity

The exact native PPU frame-1856 source witness has 14 positions where
the front and rear OAM source alpha masks overlap, their RGB values
are identical, and removing only front slot 98 changes no final colour.
These pixels need a controlled **pair-removal** witness before concluding
even *pair-level* causal influence.

The new `tools/check_baldosa_wide_overlap_causality.py` accepts five
independently captured real native Original 342×224 images, including
unmodified stock, read-only front source, read-only rear source,
front-only removal and two-slot removal. It also requires the
authenticated native single-front and pair-removal checker JSON
reports with exact frame, both source hashes, all result hashes,
separate full guest CRC equality, and exact one-slot/pair PPU
authorization. This is the **only** data source for its decision;
synthetic unit buffers do not count as native evidence.

The distinct categories are:

- **Front removal visibly changes a pixel:** lower bound for front
  influence in the final Original colour
- **Front removal does not change it, pair removal does:** pair-level
  causal effect beyond single-front difference, not individual ownership
- **Front and rear source emit identical RGB, stock matches their RGB,
  front-only removal changes nothing, pair removal changes it:** a
  direct **redundant-colour causal overlap** observation
- **Both removals change nothing:** ambiguous; background/window colour
  may match, source may be clipped, or further foreground priority may
  dominate

Every paired raster difference must lie within the **union** of the two
real source alpha planes, every single-front difference within the
front alpha mask, and native counts must match both original checker
reports exactly. The output includes bounded pixel coordinates,
complete image digests and `winner_identity_proven=false`,
`release_hd_admission=false` regardless of the result.

The offline tool is ready to consume the first real paired native
capture from PR #1185. It cannot invent that capture or elevate the
existing single-slot evidence into a release decision.

## Authenticated front, rear and paired intervention cross-check

After the rear-only diagnostic produces a real native capture, the
existing overlap analyser can take **two optional additional inputs**
(`--rear-removed` and `--rear-report`) and correlate six
independent Original 342×224 PPU planes: stock, front source, rear
source, front-deleted, rear-deleted and pair-deleted.

It validates the new rear report's exact guest frame/slot and CRC
attestation, read-only source/stock and native removal image digests,
and its positive **or zero** observed changed-pixel count before
classifying colour-causal signatures. It also cross-checks existing
front-only and pair-removal native reports rather than reinterpreting
a synthetic colour match as source provenance.

The supported classes distinguish front-only colour effects,
rear-only effects, both single removals changing colour, neither
single removal changing colour while paired removal does, and
unchanged colour even after paired removal. The identical-source-RGB
subset of pair-only changes is recorded separately with bounded real
pixel coordinates.

All three removal footprints are checked against their respective
source alpha masks. Even when every observed pixel is explained,
`unique_original_ppu_winner_proven=false` and
`release_hd_admission=false`; these interventions establish
colour causality, not hidden winner/depth or correct replacement art.

The analyzer is ready for, but makes **no claim** about, the actual
rear-99 native route from PR #1197 until that route passes and
supplies its signed-off original PPU evidence.
