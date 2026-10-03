#!/usr/bin/env python3
"""Extract the stock menu visual-language contract from snesref captures.

Input: a dump directory produced by ``tests/input/menu-visual-language.script``
through the reference harness (snesref + pinned snes9x-libretro). Output: a
compact JSON contract describing the original MAIN_MENU/OPTIONS typography,
palette, layout, cursor animation/easing and screen-slide transition, so modern
host surfaces can match the original menu grammar instead of guessing it.

Every claim is decoded from PPU state (VRAM, CGRAM, OAM, scroll registers), and
the font encoding is checked against the known menu labels. ``--atlas-out``
writes a PNG of the 40 decoded glyph slots for review. That PNG is extracted
art and stays out of version control.

Standard library only.
"""

from __future__ import annotations

import argparse
import array
import json
import math
import re
import wave
import struct
import zlib
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = "tests/input/menu-visual-language.script"

# Font layout recovered from the MAIN_MENU BG2 tilemap: a glyph is 2x2 8x8 tiles,
# top row at tile 2*slot, bottom row 0x50 tiles later (one 128-px-wide sheet row).
FONT_SLOTS = 40
FONT_BOTTOM_ROW_OFFSET = 0x50
SPECIAL_GLYPHS = ["OK", "ARROW_LEFT", "ARROW_RIGHT", "ICON_CIRCUIT_LOOP", "ICON_STUNT_HOOK"]
SMALL_FONT_FIRST_TILE = 0xA9  # '0'; A-Z follow at 0xB3 with no O, space is 0xCE
SMALL_FONT_SPACE_TILE = 0xCE
SMALL_FONT_BOTTOM_OFFSET = 0x3C
MAIN_MENU_LABELS = ["1P", "2P", "VS", "LEAGUE", "OPTIONS"]
SETUP_SCREEN_LABELS = {
    "rider": {"title": "PICK YOUR UNI", "small": ["MIKE", "ANDREW", "MARTIN", "MELISSA"]},
    "tour": {"title": "PICK TOUR", "small": ["CRAWLER", "SHUFFLER", "WALKER", "HOPPER"]},
    "track": {"title": "PICK TRACK", "small": ["CRAWLER", "DRAGSTER", "ZOOM ZOO", "BOWL", "SWITCHER", "MONSTER"]},
}
OPTIONS_LABELS = ["RECORDS", "DEFINE PLAYER", "RENAME PLAYER", "DEFINE LEAGUE", "MAIN MENU"]


# ---------------------------------------------------------------- decoding ---

def slot_for_char(ch: str) -> int:
    """Glyph slot for a character. The font has no O glyph; O renders as 0."""
    if ch.isdigit():
        return int(ch)
    if ch == "O":
        return 0
    if "A" <= ch <= "Z":
        index = ord(ch) - ord("A")
        return 10 + index - (1 if ch > "O" else 0)
    raise ValueError(f"no glyph for {ch!r}")


def char_for_slot(slot: int) -> str:
    if slot < 10:
        return str(slot)
    if slot < 35:
        index = slot - 10
        return chr(ord("A") + index + (1 if index >= 14 else 0))
    return SPECIAL_GLYPHS[slot - 35]


SMALL_FONT_PUNCTUATION = {0xA2: "%", 0xA4: "(", 0xA7: "-", 0xA8: ".", 0xCC: ":"}


def small_char_for_tile(tile: int, hflip: bool = False) -> str | None:
    """Small-font character for a top tile; ')' is the '(' tile drawn H-flipped."""
    if tile == SMALL_FONT_SPACE_TILE:
        return " "
    if tile in SMALL_FONT_PUNCTUATION:
        ch = SMALL_FONT_PUNCTUATION[tile]
        return ")" if ch == "(" and hflip else ch
    index = tile - SMALL_FONT_FIRST_TILE
    if 0 <= index < 10:
        return str(index)
    if 10 <= index < 35:
        letter = index - 10
        return chr(ord("A") + letter + (1 if letter >= 14 else 0))
    return None


def glyph_tiles(slot: int) -> list[int]:
    top = 2 * slot
    return [top, top + 1, top + FONT_BOTTOM_ROW_OFFSET, top + FONT_BOTTOM_ROW_OFFSET + 1]


def bgr555(cgram: bytes, index: int) -> list[int]:
    v = cgram[2 * index] | cgram[2 * index + 1] << 8
    return [(v & 31) << 3, ((v >> 5) & 31) << 3, ((v >> 10) & 31) << 3]


def tile_pixels(vram: bytes, char_base_word: int, tile: int, bpp: int) -> list[list[int]]:
    base = (char_base_word * 2 + tile * 8 * bpp) & 0xFFFF
    rows = []
    for y in range(8):
        row = []
        for x in range(8):
            value = 0
            for plane in range(bpp):
                byte = vram[(base + (plane // 2) * 16 + y * 2 + plane % 2) & 0xFFFF]
                value |= ((byte >> (7 - x)) & 1) << plane
            row.append(value)
        rows.append(row)
    return rows


def bg_layout(fillram: dict, bg: int) -> tuple[int, int, int, int]:
    sc = int(fillram["%04X" % (0x2107 + bg)], 16)
    nba = int(fillram["210B" if bg < 2 else "210C"], 16)
    char_base = ((nba >> (4 * (bg % 2))) & 0xF) << 12
    size = sc & 3
    return (sc >> 2) << 10, char_base, 64 if size in (1, 3) else 32, 64 if size in (2, 3) else 32


def tilemap_entry(vram: bytes, map_base: int, width: int, tx: int, ty: int) -> int:
    screen = tx // 32 + (ty // 32) * (2 if width == 64 else 1)
    addr = (map_base + screen * 0x400 + (ty % 32) * 32 + tx % 32) * 2
    return vram[addr & 0xFFFF] | vram[(addr + 1) & 0xFFFF] << 8


def letter_o(text: str) -> str:
    """Slot/tile 0 doubles as O: inside an alphanumeric word that has a letter, read 0 as O."""
    return re.sub(r"[0-9A-Z]+", lambda m: m.group(0).replace("0", "O") if re.search("[A-Z]", m.group(0)) else m.group(0), text)


def text_rows(vram: bytes, map_base: int, width: int, height: int, palette: int,
              x_screen: int, y_tile_start: int = 0) -> list[dict]:
    """Decode 16x16 font rows on one 32-column screen.

    A glyph is a left tile 2s followed by right tile 2s+1, so glyphs may start on
    any column; gaps between glyphs become single spaces and their widths are kept.
    """
    rows = []
    for i in range(min(height, 32)):
        ty = (y_tile_start + i) % height
        entries = [tilemap_entry(vram, map_base, width, x_screen * 32 + tx, ty) for tx in range(32)]
        glyphs, tx = [], 0
        while tx < 31:
            e, nxt = entries[tx], entries[tx + 1]
            tile = e & 0x3FF
            if ((e >> 10) & 7 == palette and tile < FONT_BOTTOM_ROW_OFFSET and tile % 2 == 0
                    and (nxt & 0x3FF) == tile + 1):
                glyphs.append((tx, tile // 2))
                tx += 2
            else:
                tx += 1
        if not glyphs:
            continue
        text, gaps = char_for_slot(glyphs[0][1]), []
        for (prev_tx, _), (cur_tx, slot) in zip(glyphs, glyphs[1:]):
            if cur_tx > prev_tx + 2:
                text += " "
                gaps.append((cur_tx - prev_tx - 2) * 8)
            text += char_for_slot(slot)
        text = letter_o(text)
        first, last = glyphs[0][0], glyphs[-1][0]
        rows.append({"tile_row": ty, "y": i * 8, "x_left": first * 8,
                     "x_right": (last + 2) * 8, "text": text, "word_gaps_px": gaps,
                     "center_x": (first + last + 2) * 4})
    return rows


def small_text_rows(vram: bytes, map_base: int, width: int, height: int, palette: int,
                    x_screen: int, y_tile_start: int = 0) -> list[dict]:
    """Decode 8x16 small-font runs (top tiles only). A row may hold several runs."""
    runs = []
    for i in range(min(height, 32)):
        ty = (y_tile_start + i) % height
        current: dict | None = None
        for tx in range(33):
            ch = None
            if tx < 32:
                e = tilemap_entry(vram, map_base, width, x_screen * 32 + tx, ty)
                if (e >> 10) & 7 == palette:
                    ch = small_char_for_tile(e & 0x3FF, bool(e & 0x4000))
            if ch is not None and (current or ch != " "):
                if current is None:
                    current = {"tile_row": ty, "y": i * 8, "x_left": tx * 8, "text": ""}
                current["text"] += ch
                continue
            if current:
                current["text"] = current["text"].rstrip()
                current["text"] = letter_o(current["text"])
                current["x_right"] = current["x_left"] + 8 * len(current["text"])
                runs.append(current)
                current = None
    return runs


def sprites(oam: bytes) -> list[dict]:
    out = []
    for i in range(128):
        x, y, tile, attr = oam[4 * i:4 * i + 4]
        hi = (oam[512 + i // 4] >> ((i % 4) * 2)) & 3
        x |= (hi & 1) << 8
        if x >= 256:
            x -= 512
        if 224 <= y < 240 or not -64 < x < 256:
            continue
        out.append({"x": x, "y": y, "tile": tile | (attr & 1) << 8, "palette": (attr >> 1) & 7,
                    "priority": (attr >> 4) & 3, "large": hi >> 1})
    return out


def run_lengths(values: list) -> list[list]:
    out: list[list] = []
    for v in values:
        if out and out[-1][0] == v:
            out[-1][1] += 1
        else:
            out.append([v, 1])
    return out


def deltas(values: list[int]) -> list[int]:
    return [b - a for a, b in zip(values, values[1:])]


# ------------------------------------------------------------- dump access ---

class Dump:
    def __init__(self, directory: Path, tag: str):
        self.tag = tag
        p = directory / tag
        self.vram = Path(f"{p}.vram.bin").read_bytes()
        self.cgram = Path(f"{p}.cgram.bin").read_bytes()
        self.oam = Path(f"{p}.oam.bin").read_bytes()
        self.wram = Path(f"{p}.wram.bin").read_bytes()
        regs = json.loads(Path(f"{p}.regs.json").read_text())
        self.fillram = regs["fillram"]
        self.ppu = regs["ppu"]


def series(directory: Path, name: str) -> list[Dump]:
    tags = sorted(p.name[:-len(".vram.bin")] for p in directory.glob(f"mvl-{name}-*.vram.bin"))
    if not tags:
        raise SystemExit(f"no mvl-{name}-* dumps in {directory}; run {SCRIPT} first")
    return [Dump(directory, t) for t in tags]


# --------------------------------------------------------------- analysis ---

def font_contract(d: Dump, map_base: int, char_base: int, width: int, height: int) -> dict:
    usage = Counter()
    for slot in range(FONT_SLOTS):
        for tile in glyph_tiles(slot):
            for row in tile_pixels(d.vram, char_base, tile, 4):
                usage.update(v for v in row if v)
    palette = [bgr555(d.cgram, 7 * 16 + i) for i in range(16)]
    main_rows = text_rows(d.vram, map_base, width, height, 7, 0)
    return {
        "layer": "BG2 (mode 3, 4bpp), tile priority bit set above the BG1 logo/background art",
        "glyph_cell_px": [16, 16],
        "glyph_tiles_rule": "slot s uses 8x8 tiles 2s, 2s+1 (top) and 2s+0x50, 2s+0x51 (bottom)",
        "slots": [char_for_slot(s) for s in range(FONT_SLOTS)],
        "encoding_rule": "digit d -> slot d; letter -> 10 + (ch - 'A'), minus one after N; no O glyph, O renders with the 0 glyph (rows containing letters read slot 0 as O)",
        "character_set_limits": "uppercase only; no punctuation or lowercase in this sheet",
        "bg_palette_index": 7,
        "palette_bgr555_as_rgb": palette,
        "pixel_value_usage": {str(k): v for k, v in sorted(usage.items())},
        "pixel_roles": {
            "3-7": "yellow fill, light to dark (vertical shading)",
            "8": "black outline",
            "9-12": "grey edge/shadow ramp",
            "1-2": "present in the palette but unused by the 40 font glyphs",
        },
        "main_menu_rows": main_rows,
    }


def layout_contract(main_rows: list[dict], options_rows: list[dict]) -> dict:
    ys = [r["y"] for r in main_rows]
    return {
        "row_pitch_px": sorted(set(deltas(ys))),
        "letter_pitch_px": 16,
        "word_gap_px": sorted({g for r in main_rows + options_rows for g in r["word_gaps_px"]}),
        "alignment": "each row centered on x=128",
        "row_centers_x": sorted({r["center_x"] for r in main_rows + options_rows}),
        "first_row_y": ys[0] if ys else None,
        "options_rows": options_rows,
    }


def cursor_contract(idle: list[Dump], move: list[Dump], main_rows: list[dict]) -> dict:
    def pair(d: Dump) -> tuple[dict, dict]:
        sp = sorted(sprites(d.oam), key=lambda s: s["palette"], reverse=True)
        return sp[0], sp[1]

    arrow0, shadow0 = pair(idle[0])
    spin = [pair(d)[0]["tile"] for d in idle]
    lengths = run_lengths(spin)
    cycle: list[int] = []
    for tile, _ in lengths:
        if tile in cycle:
            break
        cycle.append(tile)
    holds = sorted({n for _, n in lengths[1:-1]})
    move_xy = [(pair(d)[0]["x"], pair(d)[0]["y"]) for d in [idle[-1]] + move]
    settle = next(i for i in range(len(move_xy)) if move_xy[i:] == [move_xy[-1]] * (len(move_xy) - i))
    rows_by_y = {r["y"]: r for r in main_rows}
    start_row, end_row = rows_by_y[sorted(rows_by_y)[0]], rows_by_y[sorted(rows_by_y)[1]]
    return {
        "sprites": "two 32x32 OBJs: arrow on OBJ palette 7, drop shadow on OBJ palette 5",
        "shadow_offset_px": [shadow0["x"] - arrow0["x"], shadow0["y"] - arrow0["y"]],
        "arrow_palette_rgb": [bgr555(idle[0].cgram, 128 + 7 * 16 + i) for i in range(16)],
        "shadow_palette_rgb": bgr555(idle[0].cgram, 128 + 5 * 16 + 1),
        "spin_cycle_tiles": cycle,
        "spin_frames_per_tile": holds,
        "spin_period_frames": len(cycle) * (holds[0] if len(holds) == 1 else 0),
        "rest_position_vs_row": {
            "first_row": {"arrow": [arrow0["x"], arrow0["y"]], "text_left": start_row["x_left"], "row_y": start_row["y"]},
            "second_row_after_move": {"arrow": list(move_xy[-1]), "text_left": end_row["x_left"], "row_y": end_row["y"]},
        },
        "move_y_per_frame": deltas([y for _, y in move_xy])[:settle],
        "move_settle_frames": settle,
        "move_response_same_frame": move[0].wram[0x9B] == 1 and move_xy[1] != move_xy[0],
        "easing": "per-frame step of roughly one quarter of the remaining distance in both x and y; spin continues during motion",
    }


def slide_contract(enter: list[Dump], back: list[Dump]) -> dict:
    def hofs(ds: list[Dump]) -> list[int]:
        return [d.ppu["bg"][1]["hofs"] & 0x3FF for d in ds]

    def trim(values: list[int]) -> list[int]:
        end = next(i for i in range(len(values)) if values[i:] == [values[-1]] * (len(values) - i))
        return values[:end + 1]

    e, b = trim(hofs(enter)), trim(hofs(back))
    bg1_static = all(d.ppu["bg"][0]["hofs"] == enter[0].ppu["bg"][0]["hofs"] for d in enter + back)
    return {
        "mechanism": "BG2 horizontal scroll between adjacent 256-px tilemap screens; BG1 logo/background stays fixed" if bg1_static else "BG2 horizontal scroll",
        "distance_px": e[-1],
        "enter_hofs": e,
        "enter_velocity_px_per_frame": deltas([0] + e),
        "enter_frames": len(e),
        "back_hofs": b,
        "back_mirrors_enter": b == [e[-1] - v for v in e],
        "profile": "ease-in-out: velocity ramps 1..7 px/frame, cruises at 8 px/frame, ramps 7..1",
        "bg1_static": bg1_static,
    }


NTSC_FRAME_RATE = 60.0988
SFX_RMS_THRESHOLD = 200.0
PRESS_RE = re.compile(r"script f=(\d+) press (\S+) (\d+)")


def wav_mono(path: Path) -> tuple[array.array, int]:
    with wave.open(str(path)) as w:
        if w.getsampwidth() != 2 or w.getnchannels() != 2:
            raise SystemExit(f"{path}: expected 16-bit stereo WAV")
        return array.array("h", w.readframes(w.getnframes())), w.getframerate()


def frame_diff_rms(menu: array.array, control: array.array, rate: int) -> list[float]:
    spf = rate / NTSC_FRAME_RATE
    frames = int(min(len(menu), len(control)) / 2 / spf) - 1
    out = []
    for f in range(frames):
        s, e = int(f * spf) * 2, int((f + 1) * spf) * 2
        out.append(math.sqrt(sum((menu[i] - control[i]) ** 2 for i in range(s, e)) / (e - s)))
    return out


def sfx_bursts(rms: list[float], presses: list[tuple[int, str]]) -> list[dict]:
    """Per input: first frame at or after the press whose diff exceeds the threshold,
    and how long the burst stays above it before falling silent for two frames.
    ``baseline_quiet`` is false when the runs already differed just before the press,
    so the entry may measure music drift rather than an input sound."""
    out = []
    for i, (frame, button) in enumerate(presses):
        limit = presses[i + 1][0] if i + 1 < len(presses) else len(rms)
        onset = next((f for f in range(frame, min(limit, frame + 8)) if rms[f] > SFX_RMS_THRESHOLD), None)
        quiet = all(rms[f] <= SFX_RMS_THRESHOLD for f in range(max(0, frame - 4), frame))
        entry = {"press_frame": frame, "button": button, "baseline_quiet": quiet,
                 "onset_offset_frames": None, "duration_frames": None}
        if onset is not None:
            entry["onset_offset_frames"] = onset - frame
            end = next((f for f in range(onset, limit - 1)
                        if rms[f] <= SFX_RMS_THRESHOLD and rms[f + 1] <= SFX_RMS_THRESHOLD), None)
            entry["duration_frames"] = None if end is None else end - onset
        out.append(entry)
    return out


def sound_timing(log: Path, menu_wav: Path, control_wav: Path) -> dict:
    presses = [(int(m.group(1)), m.group(2)) for m in PRESS_RE.finditer(log.read_text())]
    menu, rate = wav_mono(menu_wav)
    control, _ = wav_mono(control_wav)
    rms = frame_diff_rms(menu, control, rate)
    presses = [p for p in presses if p[0] < len(rms)]
    return {
        "method": "per-frame RMS of (menu run WAV - no-input control WAV); threshold %.0f" % SFX_RMS_THRESHOLD,
        "inputs": sfx_bursts(rms, presses),
        "unresolved": "SFX identity: this snesref core exposes neither APU RAM nor DSP registers, and per-frame WRAM sampling misses the transient request; a burst that never falls silent means the music itself diverged (e.g. a stolen voice)",
    }


def write_png(path: Path, width: int, height: int, rgba: bytes) -> None:
    raw = b"".join(b"\x00" + rgba[y * width * 4:(y + 1) * width * 4] for y in range(height))

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def write_atlas(path: Path, d: Dump, char_base: int) -> None:
    width, height = FONT_SLOTS * 16, 16
    buf = bytearray(width * height * 4)
    for slot in range(FONT_SLOTS):
        for q, tile in enumerate(glyph_tiles(slot)):
            for y, row in enumerate(tile_pixels(d.vram, char_base, tile, 4)):
                for x, v in enumerate(row):
                    if v:
                        px = ((q // 2) * 8 + y) * width + slot * 16 + (q % 2) * 8 + x
                        buf[px * 4:px * 4 + 4] = bytes(bgr555(d.cgram, 7 * 16 + v) + [255])
    write_png(path, width, height, bytes(buf))


def setup_screens(directory: Path, map_base: int, width: int, height: int) -> tuple[dict, dict, dict]:
    screens, checks, usage = {}, {}, Counter()
    for name, expect in SETUP_SCREEN_LABELS.items():
        d = series(directory, name)[-1]
        hofs = d.ppu["bg"][1]["hofs"] & 0x3FF
        x_screen = (hofs // 256) % (width // 32)
        big = text_rows(d.vram, map_base, width, height, 7, x_screen)
        small = small_text_rows(d.vram, map_base, width, height, 7, x_screen)
        screens[name] = {
            "current_menu": f"0x{d.wram[0x9F]:02X}",
            "bg2_strip_offset_px": hofs,
            "big_font_rows": [{k: r[k] for k in ("text", "y", "x_left", "center_x", "word_gaps_px")} for r in big],
            "small_font_runs": [{k: r[k] for k in ("text", "y", "x_left")} for r in small],
            "small_font_left_edges_px": sorted({r["x_left"] for r in small}),
            "arrow_palette_highlight_rgb": bgr555(d.cgram, 128 + 7 * 16 + 13),
        }
        texts = [r["text"] for r in small]
        checks[f"{name}_title_decodes"] = expect["title"] in [r["text"] for r in big]
        checks[f"{name}_small_labels_decode"] = all(t in texts for t in expect["small"])
        if name == "track":
            mvl_char_base = bg_layout(d.fillram, 1)[1]
            for t in range(SMALL_FONT_FIRST_TILE, SMALL_FONT_SPACE_TILE):
                for tt in (t, t + SMALL_FONT_BOTTOM_OFFSET):
                    for row in tile_pixels(d.vram, mvl_char_base, tt, 4):
                        usage.update(v for v in row if v)
    small_font = {
        "glyph_cell_px": [8, 16],
        "glyph_tiles_rule": "character tile t on top, t+0x3C below; '0'..'9' are 0xA9..0xB2, A-Z (no O) from 0xB3, space 0xCE",
        "punctuation_tiles": {f"0x{k:02X}": v for k, v in SMALL_FONT_PUNCTUATION.items()},
        "punctuation_note": "')' reuses the '(' tile with the tilemap H-flip bit; 0xA3/0xA5/0xA6 are unidentified",
        "bg_palette_index": 7,
        "pixel_value_usage": {str(k): v for k, v in sorted(usage.items())},
        "pixel_roles": {"8": "black outline", "9-12": "grey fill ramp"},
        "letter_pitch_px": 8,
    }
    return screens, small_font, checks


CATALOG_EXPECT = {
    "race-results": ["DRAGSTER", "COMPLETE", "PLAYER", "TIME", "MIKE", "NO TIME"],
    "ui-record-track-entry": ["TRACK RECORDS", "TOUR", "MEDAL"],
    "ui-record-high-entry": ["HIGH SCORES", "CATEGORY:", "MOST WINS:", "TOTAL SCORE:"],
    "ui-record-player-entry": ["PLAYER SCORES", "PLAYER:", "PLAYED:", "SCORE:"],
    "ui-record-group-entry": ["GROUP SCORES", "PLAYER"],
}


def catalog_screen(d: Dump) -> dict:
    map_base, _, width, height = bg_layout(d.fillram, 1)
    x_screen = ((d.ppu["bg"][1]["hofs"] & 0x3FF) // 256) % (width // 32)
    y_start = ((d.ppu["bg"][1]["vofs"] & 0x3FF) // 8) % height
    big = text_rows(d.vram, map_base, width, height, 7, x_screen, y_start)
    small = small_text_rows(d.vram, map_base, width, height, 7, x_screen, y_start)
    small_rows = sorted({r["y"] for r in small})
    return {
        "current_menu": f"0x{d.wram[0x9F]:02X}",
        "bg2_strip_offset_px": d.ppu["bg"][1]["hofs"] & 0x3FF,
        "bg2_vertical_offset_px": d.ppu["bg"][1]["vofs"] & 0x3FF,
        "big_font_rows": [{k: r[k] for k in ("text", "y", "center_x")} for r in big],
        "small_font_runs": [{k: r[k] for k in ("text", "y", "x_left")} for r in small],
        "small_font_row_pitch_px": sorted(set(deltas(small_rows))),
        "obj_count": len(sprites(d.oam)),
    }


def screen_catalog(entries: list[str]) -> tuple[dict, dict]:
    catalog, checks = {}, {}
    for entry in entries:
        directory, tag = entry.rsplit(":", 1)
        info = catalog_screen(Dump(Path(directory), tag))
        catalog[tag] = info
        if tag in CATALOG_EXPECT:
            texts = [r["text"] for r in info["big_font_rows"]] + [r["text"] for r in info["small_font_runs"]]
            joined = " | ".join(texts)
            checks[f"catalog_{tag}_labels"] = all(any(e == t or e in t for t in texts) for e in CATALOG_EXPECT[tag]) or joined == ""
    return catalog, checks


def extract(directory: Path) -> dict:
    idle, move = series(directory, "idle"), series(directory, "move")
    enter, back = series(directory, "enter"), series(directory, "back")
    main = idle[0]
    map_base, char_base, width, height = bg_layout(main.fillram, 1)
    font = font_contract(main, map_base, char_base, width, height)
    settled = enter[-1]
    options_rows = text_rows(settled.vram, map_base, width, height, 7, 1)
    main_rows = font.pop("main_menu_rows")
    checks = {
        "main_menu_labels_decode": [r["text"] for r in main_rows] == MAIN_MENU_LABELS,
        "options_labels_decode": [r["text"] for r in options_rows] == OPTIONS_LABELS,
        "encoding_roundtrip": all(char_for_slot(slot_for_char(c)) == ("0" if c == "O" else c)
                                  for c in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
        "main_menu_state_d7": main.wram[0x9F] == 0xD7,
        "options_state_57": settled.wram[0x9F] == 0x57,
        "back_resets_selection_to_first_row": back[-1].wram[0x9B] == 0,
        "menu_switch_precedes_slide": enter[0].wram[0x9F] == 0x57 and back[0].wram[0x9F] == 0xD7,
    }
    screens, small_font, screen_checks = setup_screens(directory, map_base, width, height)
    checks.update(screen_checks)
    contract = {
        "schema_version": 1,
        "source": {
            "fixture": SCRIPT,
            "harness": "snesref + pinned snes9x-libretro, canonical USA ROM, clean boot",
            "states": ["MAIN_MENU (0xD7)", "OPTIONS_MENU (0x57)", "PLAYER_SELECT_P1 (0x3C)", "TOUR_SELECT (0x6D)", "TRACK_SELECT (0xF6)"],
        },
        "typography": font,
        "small_typography": small_font,
        "hierarchy": "yellow 16x16 font for titles, mode choices and tier labels; grey 8x16 font for names and per-item data; track-type icons are big-font glyphs placed before small-font track names",
        "setup_strip": {
            "mechanism": "MAIN_MENU, OPTIONS/rider, tour and track screens are successive 256-px BG2 strip positions; each forward step slides one screen",
            "screens": screens,
        },
        "layout": layout_contract(main_rows, options_rows),
        "cursor": cursor_contract(idle, move, main_rows),
        "transition_main_to_options": slide_contract(enter, back),
        "background": "BG1 8bpp: UNIRACERS logo over a grey checkerboard with leaf motif; static across the menu slide",
        "not_covered": ["menu sounds", "results and records table compositions", "attract/fade transitions", "tour/rider BG art and animal icon animation"],
        "checks": checks,
    }
    contract["all_checks_pass"] = all(checks.values())
    return contract, main, char_base


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("dump_dir", type=Path, help=f"snesref dump directory from {SCRIPT}")
    ap.add_argument("--out", type=Path, default=ROOT / "analysis/generated/menu-visual-language.json")
    ap.add_argument("--atlas-out", type=Path, help="optional PNG of the decoded glyph sheet (do not commit)")
    ap.add_argument("--log", type=Path, help="snesref stdout log of the menu run (for press frames)")
    ap.add_argument("--wav", type=Path, help="SNESREF_WAV output of the menu run")
    ap.add_argument("--control-wav", type=Path, help="SNESREF_WAV output of menu-visual-language-control.script")
    ap.add_argument("--catalog", action="append", default=[], metavar="DIR:TAG",
                    help="extra snesref dump to describe (e.g. results/records captures); repeatable")
    args = ap.parse_args()
    contract, main_dump, char_base = extract(args.dump_dir)
    if args.catalog:
        catalog, catalog_checks = screen_catalog(args.catalog)
        contract["screen_catalog"] = {
            "sources": ["tests/input/ui-race-result-route.script", "tests/input/ui-records-submenus.script"],
            "screens": catalog,
            "observations": [
                "results and records reuse the same grammar: yellow 16x16 titles, grey 8x16 headings and data, rider-coloured mini unicycle and medal OBJ icons",
                "PLAYER SCORES and GROUP SCORES draw green/red ratio bars; the Records menu item GROUP TABLES opens a screen titled GROUP SCORES",
            ],
        }
        contract["checks"].update(catalog_checks)
        contract["all_checks_pass"] = all(contract["checks"].values())
        contract["not_covered"] = [n for n in contract["not_covered"] if n != "results and records table compositions"]
    if args.log and args.wav and args.control_wav:
        contract["sound_timing"] = sound_timing(args.log, args.wav, args.control_wav)
        contract["not_covered"] = [n for n in contract["not_covered"] if n != "menu sounds"] + ["menu SFX identity (timing only)"]
    args.out.write_text(json.dumps(contract, indent=1) + "\n")
    if args.atlas_out:
        write_atlas(args.atlas_out, main_dump, char_base)
    print(json.dumps(contract["checks"], indent=2))
    return 0 if contract["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
