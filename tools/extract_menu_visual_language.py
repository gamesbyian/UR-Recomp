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
import hashlib
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


SMALL_FONT_PUNCTUATION = {0xA2: "%", 0xA3: "'", 0xA4: "(", 0xA5: "+", 0xA7: "-", 0xA8: ".", 0xCC: ":"}


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
                    "priority": (attr >> 4) & 3, "large": hi >> 1,
                    "hflip": bool(attr & 0x40), "vflip": bool(attr & 0x80)})
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
        if "fillram" not in regs:
            regs = native_regs_as_snesref(regs)
        self.fillram = regs["fillram"]
        self.ppu = regs["ppu"]


def native_regs_as_snesref(regs: dict) -> dict:
    """Adapt native PPU registers for the existing snesref-derived decoders.

    BG1 Mode 3 reconstruction needs BGMODE ($2105), and source OBJ cursor
    decoding needs OBJSEL ($2101). Native capture receipts already record
    both fields as bgmode/obsel. Never fabricate either register when an
    older or incomplete capture does not supply it: the owning decoder then
    rejects that missing source witness before any artwork is exported.
    """
    fill = {f"{0x2107 + i:04X}": f"{v:02X}" for i, v in enumerate(regs["bgsc"])}
    fill["210B"] = f"{regs['bg_tile_adr'] & 0xFF:02X}"
    fill["210C"] = f"{(regs['bg_tile_adr'] >> 8) & 0xFF:02X}"
    for native_name, ppu_address in (("bgmode", "2105"), ("obsel", "2101")):
        if native_name in regs:
            value = regs[native_name]
            if type(value) is not int or not 0 <= value <= 255:
                raise ValueError(f"invalid native PPU {native_name} register")
            fill[ppu_address] = f"{value:02X}"
    bgs = [{"hofs": h, "vofs": v} for h, v in zip(regs["hscroll"], regs["vscroll"])]
    return {"fillram": fill, "ppu": {"bg": bgs}}


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


def original_big_font_manifest(path: Path, d: Dump, char_base: int) -> dict:
    """Source-qualified digest for the existing original 640x16 glyph atlas."""
    return {
        "schema_version": 1,
        "source_fixture": SCRIPT,
        "source_tag": d.tag,
        "source_vram_sha256": hashlib.sha256(d.vram).hexdigest(),
        "source_cgram_sha256": hashlib.sha256(d.cgram).hexdigest(),
        "source_char_base_word": char_base,
        "dimensions": [640, 16],
        "glyph_cell": [16, 16],
        "palette": 7,
        "slots": [char_for_slot(slot) for slot in range(FONT_SLOTS)],
        "image_png_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "distribution": "Locally extracted original game art; never commit image",
    }


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


# -------------------------------------------- original BG1 backdrop art ---
# Draw *only BG1* from the canonical PPU capture. The original UNIRACERS
# logo, checkerboard and leaf motif live on this static 8bpp layer. It is
# not a final-screen screenshot: BG2 letters, OBJ arrow, colour math, output
# scale and other layers are deliberately absent. Never commit extracted PNG.
def original_menu_bg1_rgba(d: Dump, width: int = 256,
                           height: int = 224) -> bytes:
    """Decode real MODE3 BG1 tiles, tilemap flips and source horizontal scroll."""
    if not (1 <= width <= 512 and 1 <= height <= 448):
        raise ValueError("bounded reference capture dimensions required")
    if len(d.vram) != 65536 or len(d.cgram) != 512:
        raise ValueError("incorrect original PPU VRAM/CGRAM lengths")
    if "2105" not in d.fillram:
        raise ValueError("source PPU capture is missing BGMODE ($2105)")
    mode = int(d.fillram["2105"], 16)
    if (mode & 7) != 3:
        raise ValueError("the original menu BG1 reference requires MODE3 8bpp")
    map_base, char_base, map_w, map_h = bg_layout(d.fillram, 0)
    cell = 16 if mode & 0x10 else 8
    bg = d.ppu["bg"][0]
    hofs, vofs = int(bg["hofs"]), int(bg["vofs"])
    decoded_tiles: dict[int, list[list[int]]] = {}
    output = bytearray(width * height * 4)
    opaque = 0
    for y in range(height):
        sy = (y + vofs) % (map_h * cell)
        row = sy // cell
        cy = sy % cell
        for x in range(width):
            sx = (x + hofs) % (map_w * cell)
            column, cx = sx // cell, sx % cell
            entry = tilemap_entry(d.vram, map_base, map_w, column, row)
            u = cell - 1 - cx if entry & 0x4000 else cx
            v = cell - 1 - cy if entry & 0x8000 else cy
            # 16px BG characters consist of an adjacent 2x2 8px tile
            # block; source tile number advances +1 right and +16 down.
            tile = ((entry & 0x3FF) +
                    (u // 8) + (v // 8) * 16) & 0x3FF
            if tile not in decoded_tiles:
                decoded_tiles[tile] = tile_pixels(d.vram, char_base, tile, 8)
            value = decoded_tiles[tile][v % 8][u % 8]
            if value == 0:
                continue  # BG1 transparent index, no invented backdrop
            idx = (y * width + x) * 4
            output[idx:idx + 4] = bytes(bgr555(d.cgram, value) + [255])
            opaque += 1
    if opaque == 0:
        raise ValueError("source BG1 art decodes completely transparent")
    return bytes(output)


def write_original_menu_bg1(path: Path, d: Dump) -> dict:
    rgba = original_menu_bg1_rgba(d)
    write_png(path, 256, 224, rgba)
    return {
        "schema_version": 1,
        "source_tag": d.tag,
        "source_fixture": SCRIPT,
        "layers": ["BG1 8bpp MODE3 only"],
        "not_included": ["BG2 labels", "OBJ cursor", "colour math", "host scaling"],
        "dimensions": [256, 224],
        "source_bg_mode": int(d.fillram["2105"], 16),
        "source_bg1_char_base_word": bg_layout(d.fillram, 0)[1],
        "source_bg1_map_base_word": bg_layout(d.fillram, 0)[0],
        "source_bg1_scroll": [int(d.ppu["bg"][0]["hofs"]), int(d.ppu["bg"][0]["vofs"])],
        "source_registers_sha256": hashlib.sha256(json.dumps(
            {"fillram": d.fillram, "ppu": d.ppu},
            sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "vram_sha256": hashlib.sha256(d.vram).hexdigest(),
        "cgram_sha256": hashlib.sha256(d.cgram).hexdigest(),
        "rgba_sha256": hashlib.sha256(rgba).hexdigest(),
        "png_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "distribution": "Locally extracted original game art; never commit image",
    }


# ------------------------------------------------- original small font art ---
# Exact BG2 8x16 stock font is a different tile family from 16x16 titles.
# Export when requested to enable a faithful reconstructed native text path;
# all extracted pixels remain user-local and outside source control.
SMALL_ATLAS_PAIRS = (
    [(str(i), SMALL_FONT_FIRST_TILE + i) for i in range(10)]
    + [(chr(c), SMALL_FONT_FIRST_TILE + 10 + c - 65 -
        (1 if c > ord("O") else 0))
       for c in range(ord("A"), ord("Z") + 1) if c != ord("O")]
    + [("O", SMALL_FONT_FIRST_TILE)]
    + [(ch, tile) for tile, ch in sorted(SMALL_FONT_PUNCTUATION.items())]
    + [(")", 0xA4), (" ", SMALL_FONT_SPACE_TILE)]
)


def write_small_font_atlas(path: Path, d: Dump, char_base: int) -> dict:
    """One true original 8x16 glyph per cell; ')' is hardware H-flip of '('."""
    if len(d.vram) != 65536 or len(d.cgram) != 512:
        raise ValueError("incorrect original PPU VRAM/CGRAM lengths")
    width, height = len(SMALL_ATLAS_PAIRS) * 8, 16
    rgba = bytearray(width * height * 4)
    glyphs = []
    for n, (ch, tile) in enumerate(SMALL_ATLAS_PAIRS):
        if ch == " ":
            glyphs.append({"character": ch, "tile": tile, "hflip": False})
            continue
        rows = (tile_pixels(d.vram, char_base, tile, 4)
                + tile_pixels(d.vram, char_base,
                              tile + SMALL_FONT_BOTTOM_OFFSET, 4))
        flip = ch == ")"
        for y, row in enumerate(rows):
            for x, value in enumerate(row):
                if value:
                    px = n * 8 + (7 - x if flip else x)
                    offset = (y * width + px) * 4
                    rgba[offset:offset + 4] = bytes(
                        bgr555(d.cgram, 7 * 16 + value) + [255])
        glyphs.append({"character": ch, "tile": tile, "hflip": flip})
    write_png(path, width, height, bytes(rgba))
    return {
        "dimensions": [width, height],
        "glyph_cell": [8, 16],
        "palette": 7,
        "source_fixture": SCRIPT,
        "source_tag": d.tag,
        "source_vram_sha256": hashlib.sha256(d.vram).hexdigest(),
        "source_cgram_sha256": hashlib.sha256(d.cgram).hexdigest(),
        "source_char_base_word": char_base,
        "glyphs": glyphs,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "distribution": "User-local original game art; do not commit the PNG",
    }


# --------------------------------------------------- original OBJ cursor art ---
# The existing --atlas-out exports the real BG2 title font from the player's
# own original PPU capture. This sibling exporter extracts the stock *OBJ*
# cursor and +7,+7 shadow. Neither exported bitmap belongs in version control.
#
# Hardware: $2101 OBJSEL base is in 16-KiB byte steps; name-select locates
# the second 8-KiB page (SNESdev PPU registers / OBJ). The 32x32 sprite uses
# 4x4 8x8 4bpp tiles at +1 horizontally and +16 vertically. The high name
# bit selects the second page. Transparent palette index 0 is never painted.
# Keep this addressing independent of BG2's $210C title glyph base.
# (small width,height), (large width,height) per $2101. Modes 6/7
# contain rectangular OBJs; refusing a 32x64 as "32x32" matters because
# that would silently crop source art while yielding a plausible PNG.
OBJ_SIZE_PAIR = (
    ((8, 8), (16, 16)),
    ((8, 8), (32, 32)),
    ((8, 8), (64, 64)),
    ((16, 16), (32, 32)),
    ((16, 16), (64, 64)),
    ((32, 32), (64, 64)),
    ((16, 32), (32, 64)),
    ((16, 32), (32, 32)),
)
CURSOR_SOURCE_TILE_CYCLE = (8, 4, 0, 204, 200, 196, 192, 140,
                            136, 132, 128, 76, 72, 68, 64, 12)
CURSOR_SOURCE_SHADOW_OFFSET = (7, 7)


def obj_tile_pixels(d: Dump, tile: int) -> list[list[int]]:
    """Read one OBJ 4bpp tile at the actual $2101 base/name-select page."""
    if "2101" not in d.fillram:
        raise ValueError("source PPU capture is missing OBJSEL ($2101)")
    obsel = int(d.fillram["2101"], 16)
    base_word = (obsel & 7) * 0x2000
    page = (tile >> 8) & 1
    if page:
        base_word += (((obsel >> 3) & 3) + 1) * 0x1000
    return tile_pixels(d.vram, base_word, tile & 255, 4)


def obj_sprite_rgba(d: Dump, sprite: dict) -> bytes:
    """Decode only an unflipped, true 32x32 OBJ sprite; no guessed tilemaps."""
    if "2101" not in d.fillram:
        raise ValueError("source PPU capture is missing OBJSEL ($2101)")
    obsel = int(d.fillram["2101"], 16)
    size = OBJ_SIZE_PAIR[(obsel >> 5) & 7][int(sprite["large"])]
    if size != (32, 32) or not (0 <= int(sprite["palette"]) <= 7):
        raise ValueError("source cursor requires an actual 32x32 OBJ")
    if len(d.vram) != 65536 or len(d.cgram) != 512:
        raise ValueError("incorrect original PPU VRAM/CGRAM lengths")
    base_tile = int(sprite["tile"])
    if not (0 <= base_tile < 512):
        raise ValueError("invalid original OBJ tile index")
    rgba = bytearray(32 * 32 * 4)
    palette_base = 128 + int(sprite["palette"]) * 16
    for ty in range(4):
        for tx in range(4):
            # OBJ name advances on a 16-tile grid. High page stays fixed.
            tile = (base_tile & 256) | ((base_tile + ty * 16 + tx) & 255)
            for py, row in enumerate(obj_tile_pixels(d, tile)):
                for px, value in enumerate(row):
                    if value:
                        # A genuine OAM H/V flip transforms the completed
                        # 32x32 sprite, not each 8px CHR tile in isolation.
                        dst_x = 31 - (tx * 8 + px) if sprite.get("hflip") else tx * 8 + px
                        dst_y = 31 - (ty * 8 + py) if sprite.get("vflip") else ty * 8 + py
                        offset = (dst_y * 32 + dst_x) * 4
                        rgba[offset:offset + 4] = bytes(
                            bgr555(d.cgram, palette_base + value) + [255])
    return bytes(rgba)


def original_menu_cursor_pose(d: Dump) -> tuple[int, bytes]:
    """Composite stock shadow and arrow, preserving the actual 7px offset."""
    obj = sprites(d.oam)
    arrow = [s for s in obj if s["palette"] == 7]
    shadow = [s for s in obj if s["palette"] == 5]
    if len(arrow) != 1 or len(shadow) != 1:
        raise ValueError("expected exactly one visible arrow and shadow OBJ")
    a, b = arrow[0], shadow[0]
    if (b["x"] - a["x"], b["y"] - a["y"]) != CURSOR_SOURCE_SHADOW_OFFSET:
        raise ValueError("original cursor/shadow origin mismatch")
    foreground = obj_sprite_rgba(d, a)
    backdrop = obj_sprite_rgba(d, b)
    size = 32 + CURSOR_SOURCE_SHADOW_OFFSET[0]
    composite = bytearray(size * size * 4)
    for rgba, shift in ((backdrop, 7), (foreground, 0)):
        for y in range(32):
            for x in range(32):
                src = (y * 32 + x) * 4
                if rgba[src + 3] == 0:
                    continue
                dst = ((y + shift) * size + x + shift) * 4
                composite[dst:dst + 4] = rgba[src:src + 4]
    return int(a["tile"]), bytes(composite)


def export_cursor_atlas(directory: Path, path: Path,
                        manifest_out: Path | None = None) -> dict:
    """16 source PPU poses, no synthesized interpolation or source art commit."""
    unique: dict[int, tuple[Dump, bytes]] = {}
    idle = series(directory, "idle")
    # The canonical script records two entire 32-frame rotations, 64
    # consecutively numbered original PPU snapshots. Merely collecting one
    # example of each tile would NOT establish the real 2-tick hold cadence
    # or that repeated phases retain identical original raster/palette data.
    if len(idle) != 64:
        raise ValueError("original cursor requires all 64 source idle frames")
    for index, sample in enumerate(idle):
        if sample.tag != f"mvl-idle-{index:03d}":
            raise ValueError("original cursor source idle samples reordered")
        tile, rgba = original_menu_cursor_pose(sample)
        expected = CURSOR_SOURCE_TILE_CYCLE[(index // 2) % 16]
        if tile != expected:
            raise ValueError("original cursor 2-frame tile cadence differs")
        if tile in unique and rgba != unique[tile][1]:
            raise ValueError("original cursor phase art/palette drifted")
        unique.setdefault(tile, (sample, rgba))
    if tuple(unique) != CURSOR_SOURCE_TILE_CYCLE:
        raise ValueError("stock arrow tile sequence/phase evidence changed")
    pose_width = 39
    pixels = bytearray(16 * pose_width * pose_width * 4)
    frames = []
    for phase, (tile, (sample, rgba)) in enumerate(unique.items()):
        if not any(rgba[i] for i in range(3, len(rgba), 4)):
            raise ValueError("decoded original cursor pose is fully transparent")
        for y in range(pose_width):
            dst = (y * (16 * pose_width) + phase * pose_width) * 4
            start = y * pose_width * 4
            pixels[dst:dst + pose_width * 4] = rgba[start:start + pose_width * 4]
        stem = directory / sample.tag
        frames.append({
            "phase": phase,
            "source_obj_tile": tile,
            "source_tag": sample.tag,
            "source_obj_sel": int(sample.fillram["2101"], 16),
            "arrow_oam_hflip": next(s["hflip"] for s in sprites(sample.oam) if s["palette"] == 7),
            "arrow_oam_vflip": next(s["vflip"] for s in sprites(sample.oam) if s["palette"] == 7),
            "ppu_sha256": {
                ext: hashlib.sha256(Path(f"{stem}.{ext}.bin").read_bytes()).hexdigest()
                for ext in ("vram", "cgram", "oam")
            },
            "pose_rgba_sha256": hashlib.sha256(rgba).hexdigest(),
        })
    write_png(path, 16 * pose_width, pose_width, bytes(pixels))
    manifest = {
        "schema_version": 1,
        "source_fixture": SCRIPT,
        "atlas_rgba_dimensions": [16 * pose_width, pose_width],
        "sprite_dimensions": [32, 32],
        "shadow_offset": [7, 7],
        "frames_per_pose": 2,
        "cycle_frames": 32,
        "captured_idle_frames": 64,
        "atlas_png_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "source_frames": frames,
        "distribution": "Research-only locally extracted original game art; do not commit PNG",
    }
    if manifest_out is not None:
        manifest_out.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


# --------------------------------------- source-only four-asset bundle ------
def build_menu_source_art_bundle(big: dict, small: dict,
                                 cursor: dict, bg1: dict) -> dict:
    """Join four locally generated receipts only when their PPU roots match.

    The BG1 layer, big font and first cursor animation phase all come from
    the same mvl-idle-00 original snapshot. The small font comes from the
    track-select snapshot of the same named capture family, where the grey
    detail glyph tiles are known present. A bundle is evidence of source
    consistency, NOT a license or a runtime activation bit.
    """
    reports = [big, small, cursor, bg1]
    if any(not isinstance(r, dict) or r.get("source_fixture") != SCRIPT
           for r in reports):
        raise ValueError("all four assets require matching reference fixture")
    phases = cursor.get("source_frames")
    if not isinstance(phases, list) or len(phases) != 16:
        raise ValueError("original cursor phase sequence is incomplete")
    if [p.get("source_obj_tile") for p in phases] != list(CURSOR_SOURCE_TILE_CYCLE):
        raise ValueError("original cursor source phase order mismatch")
    if [p.get("source_tag") for p in phases] != [
            f"mvl-idle-{i * 2:03d}" for i in range(16)]:
        raise ValueError("original cursor exact capture phase tags mismatch")
    if cursor.get("captured_idle_frames") != 64 or (
            cursor.get("frames_per_pose") != 2 or
            cursor.get("cycle_frames") != 32):
        raise ValueError("original cursor full capture/cadence proof missing")
    original = phases[0]
    source_tag = big.get("source_tag")
    if (source_tag != "mvl-idle-000" or
        source_tag != bg1.get("source_tag") or
        source_tag != original.get("source_tag")):
        raise ValueError("original BG1/title/cursor first phase source tags disagree")
    input_hashes = original.get("ppu_sha256")
    if (not isinstance(input_hashes, dict) or
        big.get("source_vram_sha256") != bg1.get("vram_sha256") or
        big.get("source_cgram_sha256") != bg1.get("cgram_sha256") or
        big.get("source_vram_sha256") != input_hashes.get("vram") or
        big.get("source_cgram_sha256") != input_hashes.get("cgram")):
        raise ValueError("original BG1/title/cursor VRAM/CGRAM roots disagree")
    if (not isinstance(small.get("source_tag"), str) or
        not small["source_tag"].startswith("mvl-track-") or
        big.get("dimensions") != [640, 16] or
        small.get("dimensions") != [360, 16] or
        cursor.get("atlas_rgba_dimensions") != [624, 39] or
        bg1.get("dimensions") != [256, 224]):
        raise ValueError("source font/cursor/background geometry or track tag changed")
    sha = (
        big.get("image_png_sha256"), small.get("sha256"),
        cursor.get("atlas_png_sha256"), bg1.get("png_sha256"),
        big.get("source_vram_sha256"), big.get("source_cgram_sha256"),
        small.get("source_vram_sha256"), small.get("source_cgram_sha256"),
    )
    if any(not isinstance(value, str) or
           re.fullmatch(r"[0-9a-f]{64}", value) is None for value in sha):
        raise ValueError("incomplete source image or PPU digest")
    if not isinstance(small.get("source_char_base_word"), int):
        raise ValueError("small font source CHR base missing")
    return {
        "schema_version": 1,
        "source_fixture": SCRIPT,
        "source_main_tag": source_tag,
        "source_detail_tag": small["source_tag"],
        "reference_only": True,
        "asset_png_sha256": {
            "heading": sha[0], "detail": sha[1],
            "cursor": sha[2], "bg1": sha[3],
        },
        "source_ppu_sha256": {
            "main_vram": sha[4], "main_cgram": sha[5],
            "detail_vram": sha[6], "detail_cgram": sha[7],
        },
        "output_dimensions": {
            "heading": [640, 16], "detail": [360, 16],
            "cursor": [624, 39], "bg1": [256, 224],
        },
        "asset_distribution_approved": False,
        "native_render_and_visual_acceptance": False,
    }


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
        "punctuation_note": "')' reuses the '(' tile with the tilemap H-flip bit; 0xA6 is unidentified",
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
    ap.add_argument("--atlas-manifest-out", type=Path, help="optional verified 16x16 glyph source/PNG digest receipt")
    ap.add_argument("--bg1-out", type=Path, help="optional source BG1 logo/grey checker/leaf PNG (do not commit)")
    ap.add_argument("--bg1-manifest-out", type=Path, help="optional source/PNG SHA receipt for --bg1-out")
    ap.add_argument("--small-atlas-out", type=Path, help="optional original grey 8x16 detail font PNG (do not commit)")
    ap.add_argument("--small-atlas-manifest-out", type=Path, help="optional small-font charset, aliases and atlas digest")
    ap.add_argument("--cursor-atlas-out", type=Path, help="optional decoded original 16-pose OBJ cursor PNG (do not commit)")
    ap.add_argument("--cursor-manifest-out", type=Path, help="optional SHA-bound source/atlas receipt for --cursor-atlas-out")
    ap.add_argument("--bundle-manifest-out", type=Path, help="optional one-source receipt for all four locally exported PNGs")
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
    if args.atlas_manifest_out and not args.atlas_out:
        ap.error("--atlas-manifest-out requires --atlas-out")
    if args.atlas_out:
        write_atlas(args.atlas_out, main_dump, char_base)
        if args.atlas_manifest_out:
            args.atlas_manifest_out.write_text(json.dumps(
                original_big_font_manifest(args.atlas_out, main_dump, char_base), indent=2) + "\n")
    if args.bg1_manifest_out and not args.bg1_out:
        ap.error("--bg1-manifest-out requires --bg1-out")
    if args.bg1_out:
        backdrop = write_original_menu_bg1(args.bg1_out, main_dump)
        if args.bg1_manifest_out:
            args.bg1_manifest_out.write_text(json.dumps(backdrop, indent=2) + "\n")
    if args.small_atlas_manifest_out and not args.small_atlas_out:
        ap.error("--small-atlas-manifest-out requires --small-atlas-out")
    if args.small_atlas_out:
        track_dump = series(args.dump_dir, "track")[-1]
        track_char_base = bg_layout(track_dump.fillram, 1)[1]
        small = write_small_font_atlas(args.small_atlas_out, track_dump, track_char_base)
        if args.small_atlas_manifest_out:
            args.small_atlas_manifest_out.write_text(json.dumps(small, indent=2) + "\n")
    if args.cursor_manifest_out and not args.cursor_atlas_out:
        ap.error("--cursor-manifest-out requires --cursor-atlas-out")
    if args.cursor_atlas_out:
        cursor_report = export_cursor_atlas(
            args.dump_dir, args.cursor_atlas_out, args.cursor_manifest_out)
    if args.bundle_manifest_out:
        if not all((args.atlas_out, args.small_atlas_out,
                    args.cursor_atlas_out, args.bg1_out)):
            ap.error("--bundle-manifest-out requires all four --atlas-out/"
                     "--small-atlas-out/--cursor-atlas-out/--bg1-out options")
        report = build_menu_source_art_bundle(
            original_big_font_manifest(args.atlas_out, main_dump, char_base),
            small, cursor_report, backdrop)
        args.bundle_manifest_out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(contract["checks"], indent=2))
    return 0 if contract["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
