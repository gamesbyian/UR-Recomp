# Graph-paper illustrated recruitment edition (20 October 2026)

This treatment is based **directly on the two owner-supplied engineering drawings**, not on an AI reconstruction of the logo/track. The actual uploaded source JPEG bytes are preserved unchanged in this directory (the initial filenames supplied in ChatGPT were not reliable MIME indicators). The art is converted to an ink-only drawing layer so that pencil constructions, pen hatching, wheel mechanism and original course geometry remain visible without a pasted white rectangular matte.

**Art family:** `tools/showcase/graph_paper_trailer_art_direction.py` renders 12 cards at 1920×1080. Three static cards (Windows, bounded 4K framebuffer, contribution invitation), plus nine cohesive motion holders (continuous 256→342 widescreen reveal, race, original code→C, raster-xray, pixel-parity, 4× art, animation, second character study, and unused Modern holder). There is one shared restrained cream graph grid, Uniracers hand-inked header, engineering labels and a narrow right-hand wheel/track footer with a subtle hand-drawn continuation on the left. The user's original track drawing is *not warped or regenerated*: it is cropped and uniformly scaled. Only the left footer continuation is newly drawn. The giant image is not burned over the source moving picture.

**Film:** `tools/showcase/build_graphpaper_recruitment_20261020.py` reuses the accepted exact 80s / 27s footage source assertions and original synthesized score in `build_flagship_recruitment_20261019.py`. It injects the new editorial design into the existing 1120×630 factual footage box at `(400,270)`, rather than changing guest frames or inventing gameplay. The original continuous widescreen reveal remains. The October 10 grey temporary frontend footage remains excluded. The accepted 15-second three-course reel contains real MegaJump topology, Jumps inverted-airborne racer and Looper rolling grade (NOT a certified complete loop). Film captions must respect separate native sessions.

**To regenerate just the cards:**
```bash
python3 tools/showcase/build_graphpaper_recruitment_20261020.py --cards-only --outdir /tmp/ur-graphpaper-cards
```

**To regenerate films and source/target SHA manifests (requires the verified committed original media inputs, Pillow, FFmpeg):**
```bash
python3 tools/showcase/build_graphpaper_recruitment_20261020.py --outdir media/showcase/2026-10-20/graphpaper-final
```

The 80s and 27s films are not accepted until decoded video and frame witnesses are checked. Source binary/ROM redistribution rights and a complete human full-film screening remain independent open gates. The nonapproved 4× art segment must retain its caveat. No new game/renderer physics code was changed.
