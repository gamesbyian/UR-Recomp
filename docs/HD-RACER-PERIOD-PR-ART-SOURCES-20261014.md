# HD racer: independent period art sources and review gate (2026-10-14)

**Source-research queue, not a new art asset or approval.** Existing
authentic 2P sprite/OAM native multi-pose source and the pinned title
frame400 still outrank web screenshots as *pixel* references.
The observed frames **1872, 1888, 2208**, each with four independently
source-hashed PPU OBJ layers, are separately documented in
[the source multi-pose atlas](QA08-ORIGINAL-2P-MULTIPOSE-SOURCE-ATLAS-20261013.md).
Their six top/bottom paired source RGBA aliases **are not six new
independent character poses**. A native title frame captured during
a fade is not reliable for full-bright title colours.

## Highest-value newly located primary-material collection

- **DMA Design Miscellaneous Press Material**, catalogued at
  https://hiddenpalace.org/Assets/DMA_Design_Miscellaneous_Press_Material .
  The Hidden Palace record says the collection was released by
  **Frank Cifaldi on 2021-12-28**, assembled from electronic press
  kits and printed publicity scans for a NoClip DMA history project,
  and expressly **includes Uniracers/Unirally** alongside other DMA
  games. Its own direct download is currently shown as absent; its
  externally linked Internet Archive mirror is live:
  https://archive.org/details/dma_press_material .
- The Internet Archive directory lists **dma_press_material.zip**,
  approximately **635.1 MB** at
  https://archive.org/download/dma_press_material/dma_press_material.zip .
  **Important provenance boundary:** Archive catalogue and ZIP
  existence were verified; individual Uniracers members, individual
  image dates, resolution, 3D model angles and original art metadata
  have **not** been inspected. The collection description alone
  does not prove it includes a usable alternate pose or actual
  original-render production asset.

This is potentially a **different provenance class** from
web-spread gameplay screenshots or repeated box-cover artwork:
actual contemporary DMA-supplied PR files or period physical
advertisements. Inspect before treating it as visual authority.

## Independently catalogued period image and cross-checks

- **Uniracers 1995 German magazine advertisement**:
  https://www.mobygames.com/game/8085/uniracers/promo/group-99320/image-778809/ .
  The listing attributes this to *Video Games* (Germany), **issue
  07/1995**, and reports a **1231x1757** original scan. It is
  contemporary printed advertising, **not yet a separately established
  3D camera angle or a mastered character model**.
- **LaunchBox image index**:
  https://gamesdb.launchbox-app.com/games/images/2104-uniracers .
  This catalog distinguishes North American, UK and Australian
  boxes, screenshots, **fanart** and **reconstructed boxes**.
  Only verified authentic scans may become historical source
  references; reconstructed and fan-created artworks must remain
  explicitly non-authoritative. Multiple regional cover variants
  derived from one illustration count as **one artistic view**.
- **MobyGames gameplay and selection screenshot index**:
  https://www.mobygames.com/game/8085/uniracers/screenshots/snes/46724/ .
  The stock unicycle-selection menu can constrain preset palette
  choices, while genuine runtime PPU/OAM is the first authority for
  pixel silhouette. Archived emulator/gallery screenshots may be
  scaled, cropped, composited, or recorded in unknown picture
  aspect, unlike exact-sha pinned source frames.

## Inspection protocol (offline, no CI factory)

1. Download the externally hosted press ZIP **on demand**, outside
   repository history and only when bandwidth/storage are warranted.
   Record its whole-file SHA256, archive version and source URL. Do not
   upload the 635 MB archive or any copyrighted images into Git.
2. Enumerate the **actual ZIP central directory** (e.g.
   `unzip -Z1 dma_press_material.zip`), inspect folder names under
   `Uniracers`, `Unirally`, `Unicycle` and possible DMA-wide
   image directories. Avoid treating a negative name search as
   proof the asset is absent. Retain directory member path, file
   size and CRC and record SHA256 for each selected visual.
3. Inspect **only** likely original unicycle art or relevant
   genuine PR/manual/period advertising files. Record source
   classification, dimensions, crop and scan provenance, whether
   the image is original paper art, source-render, emulator pixel
   art or later reconstructed/fan art. Detect identical or
   recompressed duplicates across regional covers and gallery sites.
4. For each genuinely **independent** original rendered viewpoint,
   annotate tyre diameter, axle/hub position, fork length/angle,
   saddle arc, frame/tube angle, silhouette bounding polygon and
   coloured model components. Record image-space perspective
   ambiguity instead of manufacturing a 3D measure from a
   single projection. *Do not apply SNES 7:6 pixel aspect to
   photographic/scanned press art*. Apply it only to bona fide
   SNES raster source when displaying proportions.
5. Compare shapes at exact original source atlas captures
   (12 isolated native slot layers, 6 proven mirrored same-pose
   pairs) plus the title render with provenance and fade caveats.
   Build an **A/B human character-model decision sheet** with each
   crop linked to source digest. The user must explicitly accept
   likeness and pose consistency before any procedural/HD art
   can be promoted to shipping.

## Explicit non-promotion boundaries

Neither archive metadata, title fade brightening, packaging exaggeration,
fanart, duplicated regional images nor a successful image-matching
algorithm approves the historically rejected procedural 4x HD racer.
No source assets are copied into the repository by this research note.
This work changes no original SNES PPU/OAM renderer, output scaling,
HD admission switch, gameplay, Modern storage or independent release
ledger. The stable Original contract remains **256x224, 7:6 PAR,
true 4x pixel fallback, and authentic widened world**.
