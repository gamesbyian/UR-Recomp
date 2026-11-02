# Original-ROM 2D wheel ring landmark candidates (experimental)

A dedicated source-only diagnostic reads the retained authenticated original USA ROM 64x64 stock-composed PNG corpus from the actual original-source GitHub Actions artifact #13118909409 (run #41396846120). It verifies the EXACT source-corpus manifest SHA-256 e26193f767d22280ab65b0549e707fa05ef246a903a4cebd47411f75726dc66e and ROM identity, plus all 41 original PNG-file SHA-256s, decoded RGBA/alpha/binary-mask digests and all 59 representation declarations. It emits **numeric source raster candidate circles only**, never source pixel data and never 1994 timing.

The bounded search considers neutral-grey opaque source pixels, x=14..49, y=22..34, source-raster radius 6..10, 48 nearest-neighbour angular circumference samples, accepting at least 36/48 hits. It reports ALL tied highest scoring pixel-centre/radius candidates. These are visible **2D raster ring landmarks**, not original source 3D wheel axles, physical wheel radius, real contact point, source camera, height above road or time-registered poses.

Local initial analysis of the actual 41 PNGs found radius 7 as the sole maximum radius in every image. Best-fit raster hit counts 43..45/48; 26 images have one best candidate, 13 have two, and 2 have three. Angular samples use an explicit half-away-from-zero raster rounding rule with a small tie tolerance; ordinary Python round() and NumPy rint() disagreed at some half-pixel boundaries, so their preliminary counts must not be reused. All 35 exact source-binary-mask identity groups agree on candidate sets across different palette representations. The 48 samples may include repeated raster pixels; counts are samples, not 48 distinct arc pixels. The identified centre's uncertainty is an entire tied set (typically adjacent raster pixels), not an invented subpixel precision claim.

This creates a future **source-side anchor** that can be extracted without choosing a target silhouette shift based on a fitted 3D model. It can be joined to later independently captured PPU/OAM observations using authenticated source mask hashes, but it does NOT establish live original animation chronology or improve 3D likeness without source-registered camera/rig pose validation. Keep previous authored registry studies and experimental GLB art separate.

Run the source-only focused tests with the standard unit suite:

    python3 -m unittest tests.unit.test_audit_art4k_original_wheel_ring

For offline original source numeric measurement, install Pillow in the optional analysis environment, use the exact previously retained original 41-image source artifact and a **new** destination path:

    python3 tools/art/audit_art4k_original_wheel_ring.py --source-zip ORIGINAL_SOURCE_CORPUS.zip --out /private/2d-wheel-ring-candidates.json

Publication uses the existing fail-closed atomic no-replace evidence writer. No new workflow, emulator, second model, or shipping art.
