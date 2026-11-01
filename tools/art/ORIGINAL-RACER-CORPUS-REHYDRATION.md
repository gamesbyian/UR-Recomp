# Rehydrate exact registered original racer sources from a locally held ROM

**Offline-only source corpus recovery, no uploaded ROM or source sprites.** Historical 2026 native-original GitHub Actions artifact IDs remain documented under the QA-08 evidence authority; at the time of this investigation, their artifact inventories returned no currently retrievable files for source runs 38492408817, 38120828291 and 38097914195. This does not invalidate recorded source findings, but it prevents claiming that the old original PPU raster ZIPs are immediately usable. In contrast, the October 10 first-family review already retains 14 original-composed PNGs in-repo, with exact SHA manifests.

For the **other registered original 64×64 ROM-composed poses**, reuse the existing \`prototype_racer_hd_replacement.py::build_stock_rgba\`, \`extract_racer_presentation_family.py::encode_png_rgba\` and the live source registry. The new tool does not implement another ROM parser or rely on vanished Actions artifacts. It runs only when the canonical locally held USA ROM is available and matches both its **2,097,152-byte size and exact SHA-256 \`859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478\`**.

```sh
# User-supplied/private canonical ROM path; keep all outputs out of public Git.
python3 tools/verify_rom.py /private/rom/Uniracers_USA.sfc
python3 tools/art/export_registered_original_racer_corpus.py \
  --rom /private/rom/Uniracers_USA.sfc \
  --out /private/ur-art-corpus/snapshot-001

# Optional bounded first experiment with exact existing original review window:
python3 tools/art/export_registered_original_racer_corpus.py \
  --rom /private/rom/Uniracers_USA.sfc \
  --window first-1205-1220 \
  --out /private/ur-art-corpus/first-family-only
```

By default, every **named and registered source animation window** is included. \`--window\` can be repeated to restrict it; unknown or duplicate window IDs and malformed player/source identity fail closed. Each exact original representation is rasterized once and its RGBA image SHA, alpha hash, binary mask hash, source bounding box and original semantic source ID are retained. Identical RGBA across semantic entries shares one local source PNG; palette variants remain distinct RGBA but can share a binary silhouette group. Every exported visual remains associated with its actual source player and temporal frame window. The first 1205–1220 source window must independently reproduce the previously retained P1/P2 original review manifest's exact decoded RGBA hashes, otherwise the **entire export is rejected**.

All raw output files and JSON provenance are staged privately, then published into a **new exclusively created output directory** by same-volume no-replace hardlinks. `source-corpus.json` is published **last** and is the only completion marker. A concurrent foreign file, empty directory or symlink is never overwritten. A failed export may leave a clearly incomplete directory **without** `source-corpus.json`; discard it and choose a new destination, never count it as a successful source collection. Filesystems without hardlink support fail closed rather than using unsafe rename/copy fallbacks. Result fields clearly distinguish deterministic ROM-composed 64×64 gameplay stock from a real independent native PPU final-composite or period 3D viewpoint. Explicit likeness/shipping approval and original model recovery flags remain false.

The purpose is to expand beyond the first-family 10 distinct RGBA images into other registered animation poses without the old AOT artifact availability. **Native source OAM alpha/final PPU claims remain separate**. No independent original camera or hidden side/back geometry is proven by recovering additional time-sequenced sprites. After source export, import the new source families into the existing source-hash/landmark protocol and predeclare independent sequence holdouts before any new 3D geometry fitting.

**Policy:** do not copy original game ROM or generated original artwork into public repository, pull requests, GitHub Actions artifacts or an external AI service. The standard unit suite uses fake ROM-free compositions only and does not require a canonical ROM in CI. The output is a private workstation/HP-only authoring input, not a product asset or a release artifact.
