# Malmazuke PAL findings: scenery and 2P timing (2026-10-11)

**Evidence class:** read-only external research, **PAL-confirmed / USA-unverified**. Follow-up to [the pinned October 10 malmazuke intake](malmazuke-pal-reconstruction-intake.md). No source, ROM, assets or executable bytes copied.

**Upstream revision:** [malmazuke/unirally-reconstruction 962fb9ba3f728e1ea0e72bc0c623d1447c322891](https://github.com/malmazuke/unirally-reconstruction/commit/962fb9ba3f728e1ea0e72bc0c623d1447c322891), 11 October 2026. The upstream evidence uses the Europe PAL retail 2 MiB ROM (SHA-256 a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e), not our canonical USA ROM. Do not promote PAL addresses, 50 Hz timing or its implementation claims to USA or release acceptance without independent evidence. The earlier pinned source import and structural index remain unchanged.

## A. Scenery lists inside decompressed track streams

**Source:** [R-0093 data-coverage, frozen at this revision](https://github.com/malmazuke/unirally-reconstruction/blob/962fb9ba3f728e1ea0e72bc0c623d1447c322891/docs/research/R-0093-data-coverage.md). Our earlier intake already indexes R-0093 at an older revision; the specific scenery structures below were absent from the owning UR course-format document.

- PAL has an ordinary asset directory of 239 five-byte entries at $82:B332. Flagged entries $C2–$EE are the **45 track streams**. A **separate scenery directory** at $82:B7DD has **41 indices, $00–$28**, with assets in banks $96–$97. There are 45 tracks but only 41 scenery-directory entries.
- Each RNC-unpacked track at $7F:0000 has a **little-endian word at byte offset 0x0B** pointing to a **0xFF-terminated byte sequence of scenery indices** inside that track's unpacked data. The original PAL loader iterates it using the second directory (R-0093 cites $82:E17A–E1BB and $82:B2AC).
- In the 236-run, 1,666,993-frame PAL coverage corpus, 36 scenery entries were read. $1B and $1C appear in the list only for locked track 44; $00, $21 and $23 appear in no track list. These facts do **not** prove the five entries unreachable in every possible state.
- R-0093 supersedes R-0089's tentative second-graphics-codec interpretation: PAL $81:BB7A is a VRAM-writing counterpart of the track unpacker, with no observed call site handing it a flagged track stream. No additional codec is justified by that old lead.

**Reuse boundary:** UR-Recomp already recovered all 45 USA/prototype RNC stream boundaries in docs/COURSE-FORMAT.md and analysis/generated/rnc-stream-manifest.json. Seven Europe retail stream ordinals differ from the USA/prototype group (4, 16, 20, 26, 27, 35, 36), so this is a **semantic-layout hypothesis**, not a reason to repeat RNC extraction or assume PAL and USA byte offsets/loader addresses match.

**Cheapest USA discriminator, only when scenery/course/editor integration needs it:**
1. Inspect two already decoded canonical USA course streams without changing the production parser. Read two little-endian bytes at unpacked offsets 0x0B–0x0C, check that the pointed-to list terminates at 0xFF within the payload, and record the preceding indices without naming artwork. Test the tentative index range 0..40 explicitly.
2. Independently confirm a USA ROM scenery-directory xref and one original-emulator source/destination for a known scenery upload. Do not assume that PAL $82:B7DD is the USA directory.
3. If confirmed, enumerate all 45 streams and region variants, logging ROM revision, stream ordinal, decoded length, pointer at 0x0B, termination, indices and established directory provenance; report the seven changed final-PAL streams distinctly. Fail closed on missing terminators or out-of-range offsets.

**Disposition:** high-value course and editor research lead; no decoder change or new QA gate. Reopen only on a relevant real task, a contradictory USA capture, or a verified USA source match.

## B. Two-human menus, results and controller ownership

**Source:** [R-0095 two-human stunts](https://github.com/malmazuke/unirally-reconstruction/blob/962fb9ba3f728e1ea0e72bc0c623d1447c322891/docs/research/R-0095-two-human-stunts.md), [accepted TWO-HUMAN-STUNTS task](https://github.com/malmazuke/unirally-reconstruction/blob/962fb9ba3f728e1ea0e72bc0c623d1447c322891/tasks/TWO-HUMAN-STUNTS.md) (merged upstream as PR #72, 11 October).

PAL original-game captures and code reconstruction now cover BOWL, JUMPS, HILL CLIMB and DOWNER in two-human 2P and VS, separate rider stunt tallies, split HUD, VS mode-2 counters/champions, loser-challenger choice, tie REMATCH and quit paths. Their result is bounded by R-0095's listed exclusions, rather than a universal 2P parity claim.

A particularly useful original input rule: PAL menus gate the pads through cartridge RAM $77:0742. Rider 2's **own selection** uses pad 2 alone; after the second selection, both pads can navigate normal two-human NOW PLAYING, PICK TOUR and PICK TRACK. In VS challenger continuation, **only the challenger's pad** drives that continuation and its child menus until a new race or QUIT; tie REMATCH adds no win. NEXT TRACK wraps after the last track and skips locked tours. PAL address/bit positions require independent USA validation.

**Targeted USA checks only on a current controller/2P result blocker:** compare original USA and the exact Modern/Baldosa host for (a) pad-2-only second selection, (b) both-pad normal menu navigation, (c) challenger-only continuation after a VS loss, (d) scoreless tie/rematch, and (e) NEXT TRACK skipping locked tours. Preserve pad read/write order, mode/seat and first divergent transition; do not port PAL gate bits or introduce a second menu router. Candidate for QA-02/03/05 investigation, **not** proof of an existing defect or acceptance.

## C. DOWNER mode-7 multiplication latch collision

**Source:** R-0095 section 'Not covered'. In the PAL two-view DOWNER (track 32) run, rider 1 lands at original frame 3558 at **-288 vertical velocity**, whereas the reconstructed native run produces **-308**. The original CPU writes the low and high halves of SNES Mode 7 register **$211B (M7A)**; split-screen HDMA writes a shared register latch **between those two CPU accesses at scanline 112**. The observed multiplicand changes from **$0202 to $021C**. R-0095 explicitly says reproduction requires CPU cycle timing.

This is a concrete **PAL original-versus-upstream-native** discrepancy, not a demonstrated UR-Recomp/Baldosa issue. Neither PAL frame 3558 nor PAL scanline 112 is an assumed USA event boundary.

**Bounded adversarial discriminator, if a 2P DOWNER mismatch arises on our USA candidate:**
1. Establish corresponding USA event identity, then log ordered original-USA CPU and HDMA writes to $211B with cycle/scanline placement and control state.
2. Under the same USA original reference input, compare first M7A read/consumer and subsequent rider-1 vertical velocity before examining unrelated collision physics or images.
3. Only if USA original and the exact native candidate disagree because of this interleaving, open a gameplay/hardware timing correction with its own original/native regression. **Do not tune the velocity constant, assume PAL address equivalence, or weaken QA-01/07 acceptance.**

Other R-0095 open limits include a league table one-scanline print overrun, a native-missing PAL $0618 league-total write after 2P/VS results, and a PAL $77:10B1 race-count timing window. These remain **future discriminators**, not USA defects.

## Decision and ownership

Expose the course hypothesis through docs/COURSE-FORMAT.md and the CPU/HDMA and controller tests through docs/CROSS-PROJECT-BEHAVIOR-CORROBORATION.md. Preserve the live WORK-QUEUE, existing specialist ownership, release ledger, previously imported pinned snapshot and no-extra-harness rule. No public game assets or binaries were imported. New original-USA observations, if pursued, belong in the existing research/QA artifacts rather than creating a second truth ledger.
