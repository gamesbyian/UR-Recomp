# October 26 contributor recruitment trailer

**Film:** [95-second 1080p/60 fps cut](ur-recomp-recruit-contributors-95s-1080p.mp4)  
**SHA-256:** `2bf5a4282564e6863dcd3ba63fdf89a84a96df4589c01bae5ef5cd58b8c29e9e`  
**Contact:** ianmakesjokes@gmail.com  
**Repository:** https://github.com/gamesbyian/UR-Recomp

This cut retains the first **4,260 genuine-source/editorial frames** of the October 20 graph-paper recruitment film and replaces its old nine-second generic invitation with four six-second illustrated recruitment cards. It is **95 seconds (5,700 frames)** with an extension of the prior original synthesized score; it does not invent or reposition game footage.

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

## Rebuild and inspect

```sh
python3 tools/showcase/build_targeted_recruitment_20261026.py --cards-only --outdir /tmp/recruitment-cards
python3 tools/showcase/build_targeted_recruitment_20261026.py
```

The script rejects source-film or owner-artwork hash changes. The film's [provenance](recruitment-provenance.json) holds the exact SHA, source identities, segment timings and SHA-256 of eleven individually decoded witness PNGs. The one-shot render workflow is [.github/workflows/one-shot-oct26-recruitment.yml](../../../../.github/workflows/one-shot-oct26-recruitment.yml). It is not a scheduled video-encoding job. The first run failed solely because FFmpeg was not installed; the corrected run [40433932861](https://github.com/gamesbyian/UR-Recomp/actions/runs/40433932861) completed successfully and published the output. The editorial panels have been visually inspected by the authoring assistant; full independent human screening, audio listening and promotional approval remain outstanding.
