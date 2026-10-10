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
