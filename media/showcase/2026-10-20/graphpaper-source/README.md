## Current owner art direction: long continuous footer (20 October 2026)

The next film regeneration MUST use `uniracers_footer_long.jpg`, the owner-supplied 1536×512 longer graph-paper drawing with the continuous foreground and background track, loop, wheel and fine drafting marks. Preserve it as the source asset, crop **only** blank top and bottom margins, scale uniformly to the entire 1920-pixel card width, and align it flush to the card bottom. No synthesized left-hand extension, procedural wave or regenerated line work. This supersedes `uniracers_track_unicycle.jpg` (retained for historical production provenance).

The hand-drawn text logo remains `uniracers_graphpaper_logo.jpg` and should remain the default header illustration.

**Intake status:** The exact original image is 1536×512 JPEG despite the upload's `.png` filename. The uploaded source is 154,531 bytes, SHA-256 `744d61c5855be55b113c16313b44d2e0a37479a4019363ef4a9c8690a8029fd7`; the renderer now refuses any other bytes. The source is available as a handoff ZIP from the owner's conversation but has **not** been added to GitHub, because the GitHub connector cannot receive these local file bytes. The new renderer explicitly **refuses regeneration** until `uniracers_footer_long.jpg` is actually committed. Do not classify this art-intake task complete, and do not change the SHA of the already-published film. The user supplied the reference in the October 20 ChatGPT conversation.

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
