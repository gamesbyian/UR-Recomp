# Native Windows Modern: what a player sees, step by step

Player-visible behaviour of the **native Baldosa Modern root** as implemented. This
page describes *what the game does and says*; it is not an acceptance ledger.
Evidence and its limits live in [MODERN-FRONTEND-SHIPPING-STATUS.md](MODERN-FRONTEND-SHIPPING-STATUS.md);
independent gate status lives only in [RELEASE-QUALITY-LEDGER.json](RELEASE-QUALITY-LEDGER.json).
Controller names below are the semantic P1 pad (A / B / X / D-pad); the keyboard
equivalents are Enter / Esc / X / arrows.

## 1. Unzip and start

1. Extract the ROM-free ZIP anywhere writable. Copy **your own unmodified USA dump**
   next to the executable as `Uniracers_USA.sfc`.
2. Double-click `run-uniracers.cmd`. Saves and settings go to
   `%APPDATA%\gamesbyian\UR-Recomp` (or `UR_RECOMP_USER_DATA_ROOT`), never into the
   extracted folder.

If something is wrong the window stays open for up to a minute (any key closes it)
and says plainly what happened and that nothing was changed:

| Situation | What you see | Exit |
|---|---|---|
| ROM missing | `UR-BALDOSA-STARTUP-ROM-MISSING` + "Uniracers_USA.sfc was not found next to this launcher" | 2 |
| Wrong region, patched or damaged ROM | `UR-BALDOSA-STARTUP-ROM-INVALID` + "not the supported USA release ... Nothing was changed" | 2 |
| Save folder inside the game folder, a junction into it, or unwritable | `UR-BALDOSA-STARTUP-SAVE-ROOT` + what to set | 3 |
| Named racer data inconsistent (never auto-repaired or deleted) | `UR-BALDOSA-STARTUP-PROFILE-REJECTED` + "Your save files were not changed or deleted. Copy the whole save folder ... before asking for help" | 7 |

## 2. The root menu

Five rows: **Play, Practice, Multiplayer, Records, Options**. The bottom line shows
the one thing you can do next (for example `X CREATE STOCK RACER`) or, when an
action was refused, one short reason (`COURSE NOT REACHABLE - RETRY`,
`RESTART TO USE NEW RACER`, `COULD NOT START - TRY AGAIN`, `RACER CHANGED -
RESTART GAME`). The notice clears on your next press. B asks to quit; A confirms.

## 3. First racer (controller only)

`X` opens the stock-racer chooser (D-pad up/down picks one of the original riders),
`A` creates it. The new racer applies on the **next launch**; the root says
`RESTART FOR NEW RACER` and Play is blocked until then so nothing is played
unrecorded under a racer name. The packaged launcher restarts once by itself after
the first racer. A second racer and switching between two existing racers use the
same `X` entry; two-player needs both racers confirmed with their own pads.

## 4. Play and Multiplayer

Play hands the original game its own 1P menus; Multiplayer confirms both racers and
hands over the original 2P menus. Genuine results become named, read-only Records.
B on the original main menu returns to the root.

## 5. Practice

A opens the picker. It lists exactly the courses the **original game** has unlocked
for your racer: Crawler, Shuffler, Walker and Hopper (20 courses) on a new save,
more tours as you earn medals, never the secret Hunter tour. The picker says
`N OPEN - MORE FROM MEDALS` until all 40 ordinary courses are open.

- Up/Down changes course, Left/Right changes tour, A starts, B backs out.
- The game then walks its own rider, tour, track and NOW PLAYING menus for you and
  hands you the race only after the decoded course matches your choice.
- Practice runs on a disposable copy of the save: it never changes your career or
  Records. Normal exit, a crash or a killed process all leave your real save as it was.
- Pause (Start) offers Restart, which rewinds to the race start. Quit works as
  everywhere else.
- If the original menus do not reach the course, the route stops and says so
  (`COURSE NOT REACHABLE - RETRY`); nothing is faked.

## 6. Options

Rows that really change the game, and nothing else:

| Row | Left / Right | A |
|---|---|---|
| Display | windowed, borderless, fullscreen | next value |
| VSync | on, off, adaptive | next value |
| Volume | 0-100 in steps of 10, no wrap | +10, wraps full to silent |
| Controls | - | shows menu controls |
| Defaults | - | restores Display, VSync and Volume together or not at all |

Status line: `SAVED`, `DEFAULTS RESTORED`, `NOT APPLIED` (the window system or
config file refused it; nothing changed), `NOT SAVED - CHECK DATA`, `CHANGED
ELSEWHERE - RETRY`, `OLD FILE KEPT .damaged`. Settings persist across launches in
`options-v1.txt` (Display, VSync) and `config.ini` (Volume). A damaged settings file
is reported (`SAVED OPTIONS DAMAGED`), never stops the game, and is kept aside as
`options-v1.txt.damaged` (then `.damaged.1` ...) before a fresh file is written.
Pause on focus loss, rumble, widescreen, render scale and output resolution are not
offered because this build does not apply them.

## 7. Records

Read-only 1P runs and 2P history for the active racer. Empty states say
`NO STORED RUNS YET`, `NO ACTIVE NAMED RACER / CREATE OR SELECT A RACER`; archive
damage is counted (`UNAVAILABLE n`), never hidden.

## Known gaps (do not read as shipped)

No physical-pad, audible-volume, display-appearance, power-loss or two-pad
verification; no strict original/native complete-event parity; Racer HD art has no
current visual sign-off; Practice replay/rematch is the stock game's own flow.
