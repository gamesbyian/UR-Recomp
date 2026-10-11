# Verified Uniracers art showcase production lane

Status: **renderer scaffold committed; footage NOT rendered or accepted**. This directory deliberately contains no invented samples or placeholder sprite images. The 1080p clips can be produced only after approved source-frame PNG exports are provided.

## Evidence and scope

The authoritative approval ledgers are `analysis/data/racer-hd-art-approval.json`, plus the `-057e-0544`, `-1244-1252`, `-1230-1239`, and `-1261-1267` variants. `docs/HD-ART-DIRECTION.md` documents their motion-review and shipping-art decisions. Approved Remastered pixels are procedural C++ imagery from `native/presentation/racer_hd_presenter.hpp`, **not** an implied set of pre-existing PNG sprites. Export that exact output with source representation identity, then verify its *RGBA byte stream* against the ledger. The script refuses unknown and hash-mismatched art, and does not substitute the generic contract placeholder.

The original side must be a genuine, independently evidenced original racer compositing/export, with exact 64×64 RGBA pixels and registered pose identity. A visual resemblance or a matching semantic ID alone is insufficient to establish the same source representation. Consult the retained review dossiers and their ROM extraction/repacking paths. Record the source ROM identity and the dossier/capture evidence in each manifest entry. No graphics or palette bytes may be invented by this showcase editor.

The existing first-family approval is tied to native review run `37248763308`, artifact `11319814239`. Other family approval run/artifact references are carried directly from each ledger and emitted into provenance. These approvals establish bounded fixed-scene authored racer coverage, not 342-wide Remastered sprite correctness, full scene coverage, or 4K output.

## Input contract

Install Pillow and FFmpeg. Populate an input manifest, e.g.:

```json
{
  "frames": [
    {
      "representation_id": "EXACT_ID_FROM_APPROVAL_LEDGER",
      "stock_png": "/absolute/path/to/authentic-64x64-rgba.png",
      "authored_png": "/absolute/path/to/authored-256x256-rgba.png",
      "stock_source": "US ROM SHA256 plus extraction tool/version",
      "stock_evidence": "review dossier/run and corresponding exact composition"
    }
  ]
}
```

At least two genuinely consecutive, registered, hash-approved poses are required. Every entry must refer to the *same* authentic pose in stock and authored assets. The renderer validates the 4× art's exact RGBA SHA256, rejects family blockers and non-shipping decisions, and stores source-file and raw-pixel SHA256 identities. It cannot independently verify the authenticity or source registration of supplied stock images: those must be reviewed against the retained evidence before publication.

```bash
python3 tools/showcase/art_showcase/render_approved_art.py \
  --manifest /path/to/verified-inputs.json \
  --output media/showcase/art-reconstruction/2026-10-10
```

The renderer prepares 1920×1080 30fps H.264 MP4 videos, exact source PNG frames, and `provenance.json` containing file SHA256, approval source/run/artifact, original-source assertions, pose IDs, and clip duration/frame counts.

| Planned clip | Frames | Duration | Claim |
| --- | ---: | ---: | --- |
| `01-original-4x-remastered.mp4` | 210 | 7 seconds | Authentic stock pixel structure → nearest-4× → approved authored 4× same pose |
| `02-animation-archaeology.mp4` | 210 | 7 seconds | Editorial animation from retained ordered sprite poses |
| `03-remaster-progress.mp4` | 150 | 5 seconds | Approved 4× artwork progression versus authentic stock |

All clips include an explicit **verified art sample, not continuous native gameplay** legend. Artwork is never redrawn by the showcase. Output art sampling is nearest for authentic pixels and high-quality downsampling for true 4×. Editorial text/panels are distinct from game assets.

## Acceptance still required

1. Export authentic registered stock and hash-matching authored 4× PNGs from the retained tools and artifacts.
2. Review one-to-one pose pairing, same contact/pivot, and correct source aspect/palette.
3. Run this renderer; independently validate the output FFprobe frame counts and decode every frame without warnings.
4. Visually inspect contact sheets and actual video, including gameplay-scale appearance and transitions.
5. Commit the binaries, source/contact sheets, provenance JSON and checksums in this dedicated directory; link the completed clips to trailer Agent 1.
6. Only then mark Deliverables A–C complete or propose a merge.

This lane does not touch original guest execution, the sprite renderer, OBJ-visibility policy, Modern frontend, HD approval decisions, or the master trailer.
