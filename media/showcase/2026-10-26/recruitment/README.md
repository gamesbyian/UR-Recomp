# October 26 contributor recruitment trailer

**Film:** [95-second 1080p/60 fps cut](ur-recomp-recruit-contributors-95s-1080p.mp4)  
**SHA-256:** `0b616efea5192da0c5658e21818e17fd621bb38c94b594425f9c1d47606512a9`  
**Contact:** ianmakesjokes@gmail.com  
**Repository:** https://github.com/gamesbyian/UR-Recomp

This cut selects the first **4,260 genuine-source/editorial frames**, with a new on-screen factual correction to older art-approval terminology, of the October 20 graph-paper recruitment film and replaces its old nine-second generic invitation with four six-second illustrated recruitment cards. It is **95 seconds (5,700 frames)** with an extension of the prior original synthesized score; it does not invent or reposition game footage.

## Who this film is for

1. **Independent Windows playtesters:** actual 1P/2P pads, display modes and 4K monitors, audio, controller-only navigation, records, profile persistence and recovery, physical cold boots. A candidate build is a *technical preview* until independent hardware QA signs it off.
2. **2D and 3D artists:** source-faithful rounded 1994-style CGI unicycle modeling, rigging, expressive animation, 4×/high-density sprite families, course/environment composition and modern interface assets. Existing procedural 4× racers are **not approved** as finished likeness.
3. **People contributing agent hours:** start with [AGENTS.md](../../../../AGENTS.md), the [ranked shared work pool](../../../../docs/HOURLY-AGENT-LINES.md), tests and a reviewable PR. The five hourly agents are interchangeable generalists with independent acceptance gates.

## What is real in the film

The inherited footage contains genuinely rendered 342-column native 2P split-screen capture from **three separate sessions** (MegaJump, Jumps, Looper), including independently witnessed inverted-airborne motion on Jumps. The familiar moving original-to-wide reveal shows additional real course world. Technical/editorial sequences depict machine code translation, bounded original-centre raster parity, an actual **Original-mode** 3840×2160 framebuffer measurement and preliminary 4× art. Source identity, exact selected edit points and the original film's caveats are preserved in [the parent manifest](../../2026-10-20/graphpaper-final/flagship-provenance.json).

## What is *not* claimed

- The three genuine course sessions are **not a single contiguous race**; the Looper excerpt is not evidence of a completed loop.
- This edition does **not** newly capture authentic 1P action or a latest-current Windows Modern menu journey. Older authentic original title/menu footage and a bounded editorial Windows profile/Records card are retained. Fresh 1P, modern-menu and physical 4K Windows recording remain priorities for a future edit.
- The 3840×2160 proof is source-checked **Original-mode display output**, not a native 4K remaster character render or an approved full-width square-pixel HD presentation.
- Neither physical Windows release certification nor independently admitted full original/native USA course events is implied.
- The owner-supplied longer full-width footer image requested later was not present on main; this film uses the preserved existing October 20 graph-paper logo and earlier footer source, including its synthetic left-hand extension. No unreceived artwork has been recreated or represented as the owner's missing original.
- Historical artwork, ROM-derived sources, and footage require a separate rights/publication decision. Reproducibility and successful media encode do not supply that authorization.


## Portrait social edit and campaign poster

- **[34-second vertical film (1080×1920 / 60 fps)](ur-recomp-recruit-contributors-34s-vertical.mp4)**, SHA-256 `1864bc28012f899df50cc8763bac786953435d431c699b3f89f2ed392170bfd6`. First 1,260 frames select genuine source/editorial video from the preserved October 20 portrait film; the next four illustrated role-specific panels cover Windows playtesting (3s), 2D/3D art (3s), coding-agent development contributions (3s) and repo/email contact (4s). The ending does not manufacture gameplay.
- **[1920×1080 poster](ur-recomp-targeted-recruitment-poster-1080p.png)**, SHA-256 `ebbfd66e69c7804c1c51c2ca926325c2921ebfc98e5fbab501d4cb447ecd1d86`. Includes authentic Jumps 2P source still, owner sketch art, role-specific asks and both contact channels.
- [Exact portrait provenance](social-provenance.json) retains input source hashes, output hashes, frames, timeline, and SHA-256s of nine decoded review screenshots. [Source code](../../../../tools/showcase/build_targeted_recruitment_social_20261026.py) and [successful one-shot render #40436002255](https://github.com/gamesbyian/UR-Recomp/actions/runs/40436002255) are available to reproduce the edit.

The portrait artwork and poster were sampled and visually inspected. Human full-film/audio screening and publication-rights approval remain independent tasks.

## Rebuild and inspect

```sh
python3 tools/showcase/build_targeted_recruitment_20261026.py --cards-only --outdir /tmp/recruitment-cards
python3 tools/showcase/build_targeted_recruitment_20261026.py
python3 tools/showcase/build_targeted_recruitment_social_20261026.py
```

The script rejects source-film or owner-artwork hash changes. The film's [provenance](recruitment-provenance.json) holds the exact SHA, source identities, segment timings and SHA-256 of eleven individually decoded witness PNGs. The one-shot render workflow is [.github/workflows/one-shot-oct26-recruitment.yml](../../../../.github/workflows/one-shot-oct26-recruitment.yml). It is not a scheduled video-encoding job. The first run failed solely because FFmpeg was not installed. The first corrected render [40433932861](https://github.com/gamesbyian/UR-Recomp/actions/runs/40433932861) passed; the latest factual-art-label revision [40434938792](https://github.com/gamesbyian/UR-Recomp/actions/runs/40434938792) also passed and published the canonical output. The editorial panels and the corrective art label have been visually inspected by the authoring assistant; full independent human screening, audio listening and promotional approval remain outstanding.
