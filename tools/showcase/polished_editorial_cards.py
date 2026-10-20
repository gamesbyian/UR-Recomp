#!/usr/bin/env python3
"""Reproducible, source-identified Uniracers-inspired editorial cards.

Draws typography and geometric decoration over a blurred authentic *still* from
the previously accepted native-race poster. No footage, sprites, course terrain,
game UI or release capabilities are invented. Editorial cards only.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

W, H = 1920, 1080
DARK = "#07121e"
WHITE = "#f4f5ed"
MUTED = "#bdcbd1"
YELLOW = "#ffd35d"
PALETTE = ("#f34b5d", "#ff983c", "#f7d34c", "#5dcc71", "#49c4d5", "#5778e3", "#aa68d3")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
POSTER_SHA = "d9bcbda5335a2656f81c79607be1fd540ca7403acba403111ad12f4b4270189a"


def font(n, strong=False):
    return ImageFont.truetype(BOLD if strong else FONT, n)


def wrap(draw, words, size, width):
    lines, line = [], ""
    for word in words.split():
        next_line = f"{line} {word}".strip()
        if draw.textbbox((0, 0), next_line, font=font(size))[2] > width and line:
            lines.append(line)
            line = word
        else:
            line = next_line
    if line:
        lines.append(line)
    return lines


def line_text(draw, text, xy, size, colour=WHITE, strong=False):
    draw.text(xy, text, font=font(size, strong), fill=colour, stroke_width=0)


def accented_canvas(poster):
    # Authentic recorded race still, cropped away from the old poster lettering,
    # purposefully defocused to read as background photography not new gameplay.
    with Image.open(poster) as raw:
        race = raw.convert("RGB").crop((110, 66, 1810, 1018))
    backdrop = ImageOps.fit(race, (W, H), method=Image.Resampling.LANCZOS)
    backdrop = backdrop.filter(ImageFilter.GaussianBlur(24))
    img = Image.blend(backdrop, Image.new("RGB", (W, H), DARK), 0.83)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, 24), fill="#07121e")
    stripe = W // len(PALETTE)
    for i, colour in enumerate(PALETTE):
        d.rectangle((i * stripe, 0, (i + 1) * stripe + 2, 12), fill=colour)
    # Subtle course-contour motif, visibly abstract and distinct from gameplay.
    d.arc((1440, 70, 2220, 920), 115, 310, fill="#33617b", width=3)
    d.arc((1475, 108, 2200, 890), 115, 310, fill="#23475d", width=3)
    d.line((112, 960, 1808, 960), fill="#63818c", width=2)
    line_text(d, "UR-RECOMP  /  DEVELOPMENT NOTES", (112, 59), 26, "#a8bdc9", True)
    line_text(d, "SOURCE-BACKED EDITORIAL GRAPHIC", (111, 994), 21, "#b5cad3")
    return img, d


def headline(d, lines):
    y = 193
    for line in lines:
        line_text(d, line, (113, y), 78, WHITE, True)
        y += 101
    return y


def body(d, words, y, width=1590, size=34, spacing=53):
    lines = wrap(d, words, size, width)
    for line in lines:
        line_text(d, line, (116, y), size, MUTED)
        y += spacing
    return y


def subject_marker(d, text):
    line_text(d, text.upper(), (115, 140), 27, YELLOW, True)


def evidence_card(poster):
    img, d = accented_canvas(poster)
    subject_marker(d, "Native Windows")
    headline(d, ["A race you can", "come back to."])
    body(d, "The native frontend can create racers, run a two-player event, and reopen earned records after a fresh launch.", 454, width=1390)
    # A deliberate process timeline; no fake screenshots or invented UI.
    labels = (("01", "Choose a racer"), ("02", "Finish a race"), ("03", "Reopen Records"))
    for i, (num, title) in enumerate(labels):
        x = 114 + i * 565
        d.rounded_rectangle((x, 708, x + 515, 850), radius=13, fill="#102c40", outline="#438094", width=2)
        line_text(d, num, (x + 23, 736), 41, PALETTE[i * 2], True)
        line_text(d, title, (x + 102, 744), 29, WHITE, True)
        if i < 2:
            d.polygon((x + 519, 769, x + 539, 781, x + 519, 793), fill=YELLOW)
    line_text(d, "Verified scripted journeys. New full-session Windows footage is still needed.", (116, 894), 23, "#d0d9d7")
    return img


def resolution_card(poster):
    img, d = accented_canvas(poster)
    subject_marker(d, "Original-mode output")
    headline(d, ["3840 × 2160"])
    line_text(d, "Actual framebuffer. Pixel-checked.", (116, 330), 49, YELLOW, True)
    body(d, "A genuine SDL output readback shows the original game presented at UHD resolution. The evidence is a checked frame, not a 4K gameplay recording.", 448, width=1420)
    columns = (
        ("342 × 224", "Recorded logical world"),
        ("7:6", "Original pixel aspect"),
        ("8,294,400", "Output pixels checked"),
    )
    for i, (value, caption) in enumerate(columns):
        x = 115 + i * 568
        d.rectangle((x, 720, x + 506, 855), fill="#102c40", outline="#477b90", width=2)
        line_text(d, value, (x + 18, 741), 40, PALETTE[i * 2 + 1], True)
        line_text(d, caption, (x + 18, 803), 22, "#dbe6e6")
    line_text(d, "Original presentation only  •  Verified SDL readback  •  No simulated gameplay", (115, 899), 23, "#d0d9d7")
    return img


def contributor_card(poster):
    img, d = accented_canvas(poster)
    subject_marker(d, "Contribute to UR-Recomp")
    headline(d, ["There's a running game.", "There's work to finish."])
    body(d, "The next gains depend on people who enjoy difficult problems and care how the original plays.", 440, width=1470)
    work = ("Reverse engineering", "C++ and native platforms", "Character art and animation", "Independent testing")
    for i, line in enumerate(work):
        x = 115 + (i % 2) * 855
        y = 663 + (i // 2) * 79
        d.ellipse((x, y + 9, x + 18, y + 27), fill=PALETTE[i * 2])
        line_text(d, line, (x + 34, y), 31, WHITE, True)
    d.rounded_rectangle((108, 852, 1798, 938), radius=15, fill="#f1efe2")
    line_text(d, "github.com/gamesbyian/UR-Recomp", (158, 867), 47, "#102332", True)
    return img


def render_cards(folder, poster):
    import hashlib
    digest = hashlib.sha256(Path(poster).read_bytes()).hexdigest()
    if digest != POSTER_SHA:
        raise ValueError(f"Unexpected poster SHA: {digest}")
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    result = {}
    for name, fn in (
        ("card_windows", evidence_card),
        ("card_4k", resolution_card),
        ("card_cta", contributor_card),
    ):
        path = folder / f"polished-{name}.png"
        image = fn(poster)
        image.save(path, optimize=True)
        result[name] = path
    return result


if __name__ == "__main__":
    import argparse, json
    parser = argparse.ArgumentParser()
    parser.add_argument("--poster", required=True, type=Path)
    parser.add_argument("--outdir", required=True, type=Path)
    args = parser.parse_args()
    paths = render_cards(args.outdir, args.poster)
    print(json.dumps({k: str(v) for k, v in paths.items()}, indent=2))
