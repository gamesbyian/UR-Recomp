# Course order and stunt-timer reference

Retrieved: 2026-09-28

Purpose: external gameplay cross-checks for interpreting the 45 independently decoded RNC payloads.

## Sources

1. Uniracers instruction manual transcription:
   https://www.world-of-nintendo.com/manuals/super_nes/uniracers.shtml

   Relevant fact: each tour contains five tracks in the fixed order Race, Circuit, Stunt, Race, Circuit.

2. GameFAQs Uniracers FAQ by orange_star:
   https://gamefaqs.gamespot.com/snes/588824-uniracers/faqs/9137

   Relevant facts: preserves the nine-tour track order and names; identifies the third track of each tour as the stunt course.

3. GameFAQs stunt-course Q&A:
   https://gamefaqs.gamespot.com/snes/588824-uniracers/answers/299587-any-help-with-the-stunt-courses

   Relevant fact: describes stunt play as occurring during a 45-second interval.

4. HonestGamers Uniracers review:
   https://www.honestgamers.com/2549/snes/uniracers/review.html

   Relevant fact: independently describes stunt-score targets being attempted in 45 seconds.

## Track order

The public gameplay order is listed below, but the canonical RNC stream order is **not** the same tour order. Cross-source reconciliation on 2026-10-02 shows the RNC stream groups follow the SRAM/progression row order: Crawler, Jumper, Shuffler, Bounder, Walker, Runner, Hopper, Sprinter, Hunter. Historical start-coordinate landmarks match decoded header A.x × 16 for 43/45 courses under that ordering. The older stream-candidate column is retained below as historical context and must not be used as canonical stream identity:

| Stream candidates | Tour | Slot 1 Race | Slot 2 Circuit | Slot 3 Stunt | Slot 4 Race | Slot 5 Circuit |
|---|---|---|---|---|---|---|
| 1-5 | Crawler | Dragster | Zoom Zoo | Bowl | Switcher | Monster |
| 6-10 | Shuffler | Looper | MegaJump | Jumps | Flat Fun | Infinity |
| 11-15 | Walker | Dragrace | Ping Pong | Hill Climb | Hybrid | Short Cut |
| 16-20 | Hopper | Wario Paint | Crock | Downer | East | Hairpin Hill |
| 21-25 | Jumper | Wobble | Twinpeak | Skier | Loopback | Small Cut |
| 26-30 | Bounder | Last One | Marathon | Circle | Plinkey | Jumpover |
| 31-35 | Runner | Down+Up | Highroad | Spine | Boo! | Fire Escape |
| 36-40 | Sprinter | Vertical | Flash | Little Dipper | Fruitbat | 123 Jump |
| 41-45 | Hunter | Griller | Two Loops | Neon | Hamster | To and Fro |

## Local binary correlation

The canonical USA ROM contains exactly 45 validated RNC Method 1 payloads.

For decoded payload ordinals 3, 8, 13, 18, 23, 28, 33, 38 and 43, byte offset 2 is exactly `0x2D` (45 decimal). Those are exactly the nine third positions in the five-track grouping above. Every other decoded payload has byte offset 2 equal to `0x00`.

This is a powerful independent correlation between the RNC ordinal and shipped track order. The most economical interpretation is that each of the 45 RNC payloads is one track, in tour order, and decoded byte 2 is the stunt-course duration in seconds. The repository still treats exact stream-to-name assignment as supported until a runtime load trace or another in-ROM index independently confirms ordinal identity.


## 2026-10-02 stream-order reconciliation

The earlier assumption that RNC streams followed the manual's player-facing tour order was falsified by joining three independent local sources:

1. decoded stream header coordinate A.x;
2. Dessyreqt's 45 named historical start-coordinate landmarks;
3. the recovered SRAM medal-matrix row order.

The canonical five-stream groups are:

| Streams | Tour |
|---|---|
| 1–5 | Crawler |
| 6–10 | Jumper |
| 11–15 | Shuffler |
| 16–20 | Bounder |
| 21–25 | Walker |
| 26–30 | Runner |
| 31–35 | Hopper |
| 36–40 | Sprinter |
| 41–45 | Hunter |

With this ordering, the *literal constants* in the historical optimizer match header A.x × 16 on 43/45 rows. That is **42 nonzero numeric matches**, **one nonzero discrepancy** (Zoom Zoo: 8961 vs 9200), and **two zero-valued optimizer constants** (Jumps and Hill Climb) that cannot independently validate a runtime spawn. The script never reads its startX values during computation; even nonzero matches support stream/name transcription, not observed starting positions. Keep Jumps' zero as an unresolved annotation rather than an established coordinate mismatch. The normalized course identity is cross-source supported, while runtime spawn mapping still requires direct guest evidence.
