# Related-project technical scan

Retrieved/reviewed: 2026-09-30

Purpose: look beyond direct Uniracers/Unirally remakes for projects that can materially help reverse engineering, fidelity work, or implementation. This is deliberately bounded by value of information. A related game is not project debt merely because it resembles Uniracers.

## Promotion rule

Promote a related project only when it supplies at least one of:

- source code or tooling that solves a problem UR-Recomp is likely to face;
- a concrete track/physics/editor representation worth testing against our recovered model;
- a validation technique that can cheaply improve our fidelity loop;
- historical Uniracers-specific reverse-engineering evidence.

Otherwise keep it as a low-cost reference and do not create an acquisition workstream.

## Wheelsprung

Source: https://github.com/ninovanhooff/wheelsprung  
Reviewed revision: `67ef4f3ad6837eaf8a7e3a3fbfe2de6c09bda5b8`

This Playdate motocross/physics game is useful as a modern implementation reference, not as evidence of original Uniracers behavior.

Concrete transferable ideas:

- authoring uses Tiled with a custom scripted map format;
- save-time editor hooks normalize geometry: integer coordinates, polygon winding, and circle constraints;
- level loading converts editor polygons/polylines into explicit runtime geometry rather than making the editor format itself the simulation API;
- terrain is reduced to static line segments for Chipmunk2D collision;
- object classes and properties are parsed into typed runtime entities;
- debug/render/physics representations remain separable.

Relevant files reviewed:

- `src/screens/game/game_terrain.nim`
- `src/screens/game/game_level_loader.nim`
- `editor/extensions/src/index.ts`
- `editor/extensions/src/apply-wheelsprung-fixes.ts`
- `editor/extensions/src/wheelsprung-map.ts`

### UR-Recomp consequence

Do **not** adopt its bicycle physics model or make Chipmunk/Tiled a dependency now.

When Phase I custom-course/editor work becomes active, use this as one implementation reference for a clean boundary:

`authoring geometry -> normalized intermediate representation -> validated runtime course model`

That boundary is compatible with the direction already implied by our ROM course work: original packed/RNC structures should decode into a project-owned semantic course model, and a future editor should target that model rather than mimic the original binary layout.

## Trike

Source description: https://chaps.dev/projects/trike/

Trike explicitly cites Uniracers as inspiration. Its useful contribution is methodological rather than behavioral:

- spline-defined tracks and human-readable scene data;
- gameplay kept in inspectable scripts;
- headless PNG rendering used as a cheap regression surface;
- small purpose-built regression scenes for flips, quaternion/orientation behavior and laps before full playtesting.

### UR-Recomp consequence

No code import or new dependency is justified.

Retain one practice: for future renderer/Widescreen/editor geometry changes, prefer tiny deterministic visual fixtures that answer one question over repeated full-race capture. This reinforces the repository's existing value-of-information and progressive-evidence rules.

## 2005 GameDev.net Sonic/Uniracers-physics source lead

Thread: https://gamedev.net/forums/topic/299691-uniracers-physics/

Linolium described an older DOS/MSVC Sonic-style engine with loops, hills, slopes and a level editor. The implementation used:

- four discrete surface orientations;
- coordinate transforms between those orientations;
- collision-map switching around loops;
- tile/block collision structures;
- special transition objects.

Linolium explicitly offered the game source and level editor. Hotmail initially rejected the zip; by 2005-02-10 the files had been sent individually to forum user DekuTree64, and another recipient supplied an email address.

### Bounded recovery attempt

Searched on 2026-09-30 for combinations of:

- Linolium + Sonic clone/source/editor;
- the exact forum signature/name;
- DekuTree64 + Linolium/Sonic;
- the recipient address recorded in the thread;
- distinctive implementation phrases such as the old MSVC/mode-13h description.

No surviving source archive or level-editor download was found.

A current web identity for DekuTree64 appears to exist, but contacting people is not warranted for this supporting lead while UR-Recomp already has direct original-game evidence and active critical-path work.

**Disposition: closed/passive.** Reopen only if a surviving archive appears cheaply, or if the native course/surface model reaches a design blockage that analogous historical source could realistically resolve.

## Historical Uniracers level-viewer thread

The 2008 ROMhacking.net level-viewer work discovered during this scan was already present in the repository:

- `reference/catalog.yml` entry `rhdn-uniracers-level-viewer`
- `reference/notes/course-reverse-engineering-history.md`
- linked current work in `docs/COURSE-FORMAT.md`

No duplicate research lane is needed.

## Other descendants surveyed

FutureGrind, RingRaceR, MonoRace, Go Gimbal Go, Old Spice Racers, Racing Tyres Space, Assembly 2009 Ribbon Racer and several jam/prototype projects remain design references only.

None currently exposes evidence or tooling strong enough to justify taking time from the shipping critical path. Do not actively acquire or reverse engineer them unless a later concrete implementation question changes their expected value.

## Net result

Two durable takeaways only:

1. Future custom-course tooling should preserve a hard authoring/semantic-runtime boundary, with validation/normalization at import.
2. Small headless deterministic visual/physics fixtures are a proven cheap technique for geometry and stunt-system iteration.

Neither finding changes current P0 priority. The scan is complete unless a later blocker gives one of these projects new decision value.
