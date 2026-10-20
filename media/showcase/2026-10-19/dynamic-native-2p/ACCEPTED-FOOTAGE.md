# Source-verified native widescreen two-player topology footage

**Status:** source-video and 15-second film are independently SHA-checked and inspected at representative frames; complete closed-loop and Hill Climb sequences are not yet certified.

Four H.264 1080p/60-fps MP4s, all captured or edited from the *real running* native 342-column Original presentation. No guest code, physics, course geometry, track-position editing, remastered art, fabricated race frames or temporal interpolation.

## Finished footage

| Video | Duration / decoded frames | Exact SHA-256 | What footage establishes |
| --- | --- | --- | --- |
| [MegaJump P2-leads](native-megajump-p2-leads-900f.mp4) | 15s / 900 | `cee7dbdf271068896c9636206c6613bda302ba938a1c473ac4483ab6369617a4` | Dramatic curved slope, vertical transitions, asymmetric rider progress, genuine separated split cameras |
| [Jumps P1-leads](native-jumps-p1-leads-900f.mp4) | 15s / 900 | `46283d6fb1f698868a736df0cee857aa8928cc587f39d88c77a41c41813c9b03` | Real inclined track and an inverted airborne green rider at ordinal 570, as independently seen in [decoded image](jumps-p1-leads-frame-0570.png) |
| [Looper P1-leads](native-looper-p1-leads-900f.mp4) | 15s / 900 | `3de690c458b70d802af692418a155b31bb0381d595e61c897a62be492aeecbe3` | Strongly curved and rolling track with unequal player positions; **full closed loop not independently observed** |
| [Three-course action reel](native-dynamic-2p-three-courses-15s.mp4) | 15s / 900 | `46b5bf43bcfb4f8bdd4874e7a9994f70996688c2c86a259bef01d5102630598d` | Three clearly distinct five-second hard cuts from the verified recordings; MegaJump ordinals 280–579, Jumps 300–599, Looper 120–419 |

View the [MegaJump](megajump-p2-leads-contact-sheet.png), [Jumps](jumps-p1-leads-contact-sheet.png) and [Looper](looper-p1-leads-contact-sheet.png) source-review contact sheets, and the [three exact decoded output witnesses](dynamic-three-course-reel-provenance.json).

## Evidence

The original source-capture run [39356424570](https://github.com/gamesbyian/UR-Recomp/actions/runs/39356424570) successfully completed all three 900-frame recordings, each with a corresponding no-video control run and matching full guest WRAM CRC stream; it subsequently failed when attempting a fourth, unqualified **Hill Climb** menu route. Source evidence was rescued without a native rebuild and accepted by [recovery CI 39359002789](https://github.com/gamesbyian/UR-Recomp/actions/runs/39359002789); the three-course montage was created and source/frame checked in [CI 39359506207](https://github.com/gamesbyian/UR-Recomp/actions/runs/39359506207).

Exact evidence is in [dynamic-racing-provenance.json](dynamic-racing-provenance.json) and [the final montage manifest](dynamic-three-course-reel-provenance.json). The source-capture artifact omitted its native executable SHA checksum file; this specific field is explicitly `null`. The binary and original source **must not** be claimed fully provenance-complete on that axis. Its immutable pinned source/framework and ROM identity, control-versus-capture CRCs, signed CI evidence, original FFV1 source digest and three source-world position witnesses per route are still documented.

No new ROM images, WRAM dumps or commercial soundtracks are committed. The final reel is silent for integration with the main trailer's independently authored original soundtrack. This source footage is separated into its own media PR, without merging unfinished experimental navigation work from [#2002](https://github.com/gamesbyian/UR-Recomp/pull/2002).

**Visual acceptance boundaries:** The MegaJump and Jumps geometry and an actual airborne inverted rider have been reviewed on decoded frames; Looper shows rolling slopes and racer separation but no full loop conclusively witnessed. A true three-feature hill + closed loop + ramp reel remains blocked on further authentic footage. Do not claim Hill Climb, a complete Looper revolution, stunt scoring or landed-trick certification from these samples.

For a flagship update, splice this 15-second source-locked action reel into the already produced [85-second flagship](../flagship/ur-recomp-flagship-85s-1080p.mp4), replacing the formerly flat source race cuts, with clear source-session editorial cuts. Do not visually represent these course sessions as one continuous race.
