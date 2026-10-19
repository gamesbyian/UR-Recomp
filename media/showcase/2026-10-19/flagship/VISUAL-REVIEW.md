# Flagship visual inspection, source identity and release limitations

**2026-10-19 / model-assisted review:** Reviewed committed 1920×1080/60fps and 1080×1920/60fps source-decoded frame receipts and contact sheet, plus the enhanced social frames at six well-defined output ordinals. FFprobe and SHA-verification are independent of this visual judgment; the screen check is representative-sample-only, **not** a human full 85-second watch-through.

## Verified identities

The 85-second film has **5,100 decoded video frames**, 27-second matte social precursor **1,620**, and its final ambient social edit **1,620**; all at nominal 60fps. The footage master contains two disjoint halves of the same real native 600-frame 2P run: 240 then 360 continuous frames in chronological order, with no missing original frames in the combined source range. The 7s widescreen reveal uses those *same* underlying game frames as an independently accepted presentation edit. The Modern root is a separately executed real 2026-10-10 native capture, not the newer 2026-10-19 product state.

Every source MP4 has its own exact SHA256, recorded frame count and classification in [the film manifest](flagship-provenance.json). The horizontal output, two social variants, poster, generated score and 4× art cards were not represented as 4K native footage or production-ready Remastered art.

## Visual samples inspected

- The opening two edited stock shots visibly display authentic colorful Uniracers title artwork and the original checkerboard menu, without startup black.
- The 256→342 animated reveal shows active upper/lower player race bands and additional track already present in the underlying continuous source video; moving racer and timer cadence are preserved.
- The genuine Modern root capture clearly shows **Practice SOON / Options SOON** because it is explicitly the older October 10 version. The newer October 19 functionality is deliberately represented as a source-cited *editorial diagram*, **not** retroactively inserted into the old game recording.
- The code-to-C segment contains verifiable original 65816 MainLoop source bytes and associated generated C; the source-raster and exact-centre-parity segments present 342 source columns, true native raster witness and a scoped 0/57,344 centre difference, with editorial boundaries.
- The 3840×2160 card communicates the genuine independently accepted **8,294,400 original-mode SDL readback pixels**, explicitly not a recorded UHD gameplay session.
- The three 4× pose-family sequences remain conceptual/procedural experiments subject to the current explicit 3D character-likeness veto. They do not claim completed high-definition rider art or fully Remastered widescreen gameplay.
- The final actual 2P clip preserves both riders and displays the original source HUD. The final card solicits contributors specifically in C++, reverse engineering, character animation and source-grounded QA.
- The ambient portrait's independently decoded frames at ordinals 30, 180, 650, 840, 1140 and 1480 display source-faithful 1080×608 central raster, a visibly blurred/tinted surrounding matte, cyan separators, clear campaign title and an always-visible GitHub location. No extra track content is claimed in the blur, and neither 2P viewport is cut away.
- The promotional poster is a source-native racing image with purely editorial text and a SHA-verified prior-gameplay source, not a newly fabricated title screen.

`flagship-output-review.json` records all 21 exact frame PNG hashes from the first independent encode, and `flagship-social-ambient-provenance.json` retains the six decoded social frame SHA256 values. The contact sheet exists for visual review, not as a replacement for the source videos or proof of every intermediate frame.

## Remaining external boundaries

The movie and these observations do not grant **0/45 USA complete-event** credit, **0/12 Windows release QA gate** credit, physical gamepad/audio/4K-display qualification, source-output 4K video capture, or finished Windows beta status. The launch footage is separately dated and labelled honestly. Neither ROM nor original music is bundled.

**Public redistribution rights for copyrighted Uniracers imagery remain uncleared.** A human full-playback review, music-mix critique on reference hardware and final external publication are useful later handoffs; they are not falsely asserted here.

[Future current-head exact Windows cinematic player-journey capture](https://github.com/gamesbyian/UR-Recomp/issues/1995) is tracked separately. It is not a prerequisite to integrating this verified promotional package.
