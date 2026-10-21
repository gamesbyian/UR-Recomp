# Flagship 85-second genuine action-footage revision

**Source-locked editorial successor to October 19 flagship.** This does not touch original gameplay, native guest execution, presentation correctness, or Modern frontend. The running game and 342-column Original world are unchanged; only the film's two previously bland 2P clips are replaced.

Timeline is **exactly 85 seconds / 5,100 frames at 1080p/60fps**, with the original composed soundtrack copied unchanged from the accepted first flagship movie.

| Film frames | Source | Original source ordinals | Verified visual content |
| --- | --- | --- | --- |
| 0–599 | Prior accepted flagship | 0–599 | Original colorful title, checkerboard menu, genuine moving widescreen reveal |
| 600–839 | Native MegaJump P2-leads | 300–539 | Steep vertical topology, asymmetrically moving riders, full 342-wide 2P |
| 840–4199 | Prior accepted flagship | 840–4199 | Modern navigation, native/65816 engineering, exact pixel evidence, 4× prototypes |
| 4200–4379 | Native Looper P1-leads | 180–359 | Curved and rolling track; **complete closed loop not yet verified** |
| 4380–4559 | Native Jumps P1-leads | 360–539 | Actual original airborne trick poses and sloped/ramp-like terrain |
| 4560–5099 | Prior accepted flagship | 4560–5099 | Existing contribution invitation |

The underlying source recordings, source hashes, guest frame indices, full guest-state control/recorded WRAM CRC equality, original course IDs, and independent P1/P2 world-coordinate witnesses are documented in [the accepted source package](../dynamic-native-2p/ACCEPTED-FOOTAGE.md), merged separately as [PR #2014](https://github.com/gamesbyian/UR-Recomp/pull/2014).

Production is reproducible via `tools/showcase/build_flagship_dynamic_course_v2.py`. Its source whitelist includes exact 85-second old flagship SHA plus all three original native movie SHA values. It refuses altered video, unexpected fps/resolution/frame counts, or missing source guest-state proof. Three short native clips fit into separate editorial top-matte frames with source-session captions, without cropping away either two-player racer view, changing course geometry, synthesizing gameplay, or interpolating time. The original audio is mapped untouched from the previous 85-second master.

The only new output is `ur-recomp-flagship-85s-dynamic-courses-1080p.mp4`, with `dynamic-flagship-v2-provenance.json`, four independently decoded output frames and model-assisted representative-frame review. **Do not claim a completed full closed loop, Hill Climb race or accepted stunt results.**

The old source footage was technically honest yet visually unrepresentative. This edit is intended to answer that recruitment problem through more compelling genuine footage while preserving the deeper engineering story.
