#!/usr/bin/env python3
"""Synthetic-frame contract for the Modern visual diagnostics tool."""
import contextlib
import io
import json
import struct
import zlib
from pathlib import Path
import tempfile
import unittest

from tools import qa_modern_visual_diagnostics as d

BG = (47, 47, 47)
FG = (200, 200, 200)
BAR = (160, 208, 248)


def p7(width, height, pixels):
    head = (f"P7\nWIDTH {width}\nHEIGHT {height}\nDEPTH 4\nMAXVAL 255\n"
            "TUPLTYPE RGB_ALPHA\nENDHDR\n").encode()
    cache = {}
    body = bytearray()
    for px in pixels:
        enc = cache.get(px)
        if enc is None:
            enc = cache[px] = bytes((*px[:3], 255))
        body += enc
    return head + bytes(body)


def logical_canvas(w=342, h=224):
    grid = [BG] * (w * h)
    return grid, w, h


def render(grid, lw, lh, out_w, out_h):
    f, vx, vy, _, _ = d.integer_scale(lw, lh, out_w, out_h)
    black = (0, 0, 0)
    cols = [(x - vx) // f if vx <= x < vx + lw * f else None for x in range(out_w)]
    out = []
    for y in range(out_h):
        ly = (y - vy) // f if vy <= y < vy + lh * f else None
        if ly is None:
            out += [black] * out_w
            continue
        row = grid[ly * lw:(ly + 1) * lw]
        out += [black if c is None else row[c] for c in cols]
    return d.Frame(p7(out_w, out_h, out))


def put(grid, lw, x, y, w, h, c):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            grid[yy * lw + xx] = c


ROOT = Path(__file__).resolve().parents[2]


def render_fit(grid, lw, lh, out_w, out_h):
    # Nearest-neighbour fractional fit with 7:6 pixel aspect (what ships);
    # nearest maps pixel centres.
    m = d.mapping(lw, lh, out_w, out_h)
    black = (0, 0, 0)
    cols = []
    for x in range(out_w):
        lx = int((x + 0.5 - m.vx) / m.sx)
        cols.append(lx if 0 <= lx < lw else None)
    out = []
    for y in range(out_h):
        ly = int((y + 0.5 - m.vy) / m.sy)
        if not 0 <= ly < lh:
            out += [black] * out_w
            continue
        row = grid[ly * lw:(ly + 1) * lw]
        out += [black if c is None else row[c] for c in cols]
    return d.Frame(p7(out_w, out_h, out))


def png(width, height, pixels, ctype=6, filt=0):
    bpp = 4 if ctype == 6 else 3
    rows, prev = b"", bytes(width * bpp)
    for y in range(height):
        line = b"".join(bytes(pixels[y * width + x][:3]) + (b"\xff" if bpp == 4 else b"")
                        for x in range(width))
        enc = bytearray()
        for i, v in enumerate(line):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if filt == 1:
                pred = a
            elif filt == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pred = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
            else:
                pred = 0
            enc.append((v - pred) & 255)
        rows += bytes([filt]) + bytes(enc)
        prev = line

    def chunk(tag, body):
        return struct.pack(">I", len(body)) + tag + body + struct.pack(
            ">I", zlib.crc32(tag + body))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, ctype, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


class DiagnosticsTest(unittest.TestCase):
    def test_fit_model_matches_real_fractional_output(self):
        # Production output fits the canvas with 7:6 pixel aspect and
        # nearest sampling, so blocks are fractional, never integer.
        grid, w, h = logical_canvas()
        put(grid, w, 30, 30, 40, 8, FG)
        put(grid, w, 100, 100, 5, 5, BAR)
        a = render_fit(grid, w, h, 1280, 720)
        b = render_fit(grid, w, h, 1920, 1080)
        rep = d.compare_resolutions(a, b, w, h)
        self.assertTrue(rep["pass"], rep)
        self.assertAlmostEqual(rep["a"]["scale"][0] / rep["a"]["scale"][1], 7 / 6, 3)
        put(grid, w, 200, 150, 3, 1, FG)
        c = render_fit(grid, w, h, 1920, 1080)
        rep = d.compare_resolutions(a, c, w, h)
        self.assertFalse(rep["pass"])
        self.assertEqual(rep["differing_logical_pixels"], 3)
        # The integer model must not be mistaken for the real mapping.
        self.assertFalse(d.compare_resolutions(a, b, w, h, mode="integer")["pass"])

    def test_diff_png_marks_exactly_the_differing_logical_pixels(self):
        grid, w, h = logical_canvas()
        put(grid, w, 30, 30, 40, 8, FG)
        a = render_fit(grid, w, h, 1280, 720)
        put(grid, w, 100, 100, 3, 2, BAR)
        b = render_fit(grid, w, h, 1920, 1080)
        data = d.diff_png(a, b, w, h, zoom=2)
        width, height, rgba = d.unpack_png(data)
        self.assertEqual((width, height), (w * 2, h * 2))
        red = {(x // 2, y // 2) for y in range(height) for x in range(width)
               if tuple(rgba[(y * width + x) * 4:(y * width + x) * 4 + 3]) == (255, 0, 0)}
        self.assertEqual(red, {(x, y) for x in range(100, 103) for y in range(100, 102)})
        # identical inputs -> no red at all
        none = d.unpack_png(d.diff_png(a, a, w, h, zoom=1))[2]
        self.assertNotIn((255, 0, 0), {tuple(none[i:i + 3]) for i in range(0, len(none), 4)})

    def test_cli_compare_writes_diff_png(self):
        grid, w, h = logical_canvas()
        put(grid, w, 30, 30, 4, 4, FG)
        a = render_fit(grid, w, h, 1280, 720)
        put(grid, w, 60, 60, 2, 2, BAR)
        b = render_fit(grid, w, h, 1280, 720)
        with tempfile.TemporaryDirectory() as tmp:
            pa, pb, out = (Path(tmp) / n for n in ("a.p7", "b.p7", "d.png"))
            for path, fr in ((pa, a), (pb, b)):
                path.write_bytes(p7(fr.width, fr.height,
                                    [fr.rgb(x, y) for y in range(fr.height)
                                     for x in range(fr.width)]))
            with contextlib.redirect_stdout(io.StringIO()) as buf:
                code = d.main(["compare", str(pa), str(pb), "--logical", "342", "224",
                               "--diff-png", str(out)])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(buf.getvalue())["differing_logical_pixels"], 4)
            self.assertEqual(d.unpack_png(out.read_bytes())[:2], (342 * 3, 224 * 3))

    def test_detect_distinguishes_native_logical_widths(self):
        wide, ww, hh = logical_canvas(342, 224)
        narrow, nw, nh = logical_canvas(256, 224)
        for grid, lw in ((wide, ww), (narrow, nw)):
            for i in range(0, lw - 4, 7):
                put(grid, lw, i, (i * 5) % 200, 3, 4, FG if i % 14 else BAR)
        det = d.detect_logical(render_fit(wide, ww, hh, 1280, 720))
        self.assertEqual(det["consistent_widths"], [342], det)
        det = d.detect_logical(render_fit(narrow, nw, nh, 1024, 768))
        self.assertEqual(det["consistent_widths"], [256], det)
        self.assertTrue(det["pass"])

    def test_detect_prefers_clearly_better_width_but_flat_frames_stay_ambiguous(self):
        from unittest import mock
        frame = d.Frame(p7(2, 1, [(0, 0, 0), (1, 1, 1)]))

        def detect(scores):
            with mock.patch.object(
                    d, "extract_logical",
                    side_effect=lambda f, w, h, m, p: {"nonuniform_fraction": scores[w]}):
                return d.detect_logical(frame)

        # Sparse content: the wrong width is only slightly non-uniform, but
        # measurably worse than the exact fit.
        det = detect({256: 0.0015, 342: 0.0})
        self.assertEqual(det["consistent_widths"], [342])
        self.assertTrue(det["pass"])
        # Both fit (flat frame) -> ambiguous; neither within tolerance -> none.
        self.assertEqual(detect({256: 0.0, 342: 0.0002})["consistent_widths"], [256, 342])
        self.assertFalse(detect({256: 0.0, 342: 0.0002})["pass"])
        self.assertEqual(detect({256: 0.03, 342: 0.02})["consistent_widths"], [])
        # Real wide capture shape: 256 exact, 342 clearly off.
        self.assertEqual(detect({256: 0.0, 342: 0.0183})["consistent_widths"], [256])

    def test_explain_finds_the_mapping_a_standard_check_missed(self):
        # A 256-wide canvas presented with SQUARE pixels (par 1.0), not 7:6.
        grid, w, h = logical_canvas(256, 224)
        seed = 7
        for y in range(10, 210):
            for x in range(10, 246):
                seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
                if (seed >> 16) % 3 == 0:
                    grid[y * w + x] = FG if (seed >> 8) % 2 else BAR
        m = d.mapping(256, 224, 1280, 720, "fit", 1.0)
        cols = [int((x + 0.5 - m.vx) / m.sx) for x in range(1280)]
        rows = []
        for y in range(720):
            ly = int((y + 0.5 - m.vy) / m.sy)
            if not 0 <= ly < 224:
                rows += [(0, 0, 0)] * 1280
                continue
            row = grid[ly * 256:(ly + 1) * 256]
            rows += [row[c] if 0 <= c < 256 else (0, 0, 0) for c in cols]
        frame = d.Frame(p7(1280, 720, rows))
        self.assertFalse(d.detect_logical(frame)["pass"])
        best = d.explain_mapping(frame, widths=(256, 342), pars=(7 / 6, 1.0), top=2)[0]
        self.assertEqual((best["logical_width"], best["par"], best["mode"]),
                         (256, 1.0, "fit"))
        self.assertEqual(best["nonuniform_fraction"], 0.0)

    def test_fit_clip_and_focus_on_fractional_output(self):
        grid, w, h = logical_canvas()
        put(grid, w, 30, 30, 40, 8, FG)
        put(grid, w, 20, 60, 3, 16, BAR)
        frame = render_fit(grid, w, h, 1280, 720)
        self.assertTrue(d.clip_audit(frame, w, h, [FG, BAR], "action")["pass"])
        m = d.mapping(w, h, 1280, 720)
        self.assertTrue(d.focus_audit(frame, BAR, m.sx, scale_y=m.sy)["pass"])
        put(grid, w, 0, 100, 4, 8, FG)
        edge = d.clip_audit(render_fit(grid, w, h, 1280, 720), w, h, [FG], "action")
        self.assertFalse(edge["pass"])

    def test_real_committed_capture_is_a_fractional_256_wide_canvas(self):
        path = ROOT / "media/showcase/2026-10-10/recruitment/modern-root/frame-300.png"
        frame = d.load(path)
        self.assertEqual((frame.width, frame.height), (960, 540))
        det = d.detect_logical(frame, (256, 342))
        self.assertIn(256, det["consistent_widths"], det)
        self.assertNotIn(342, det["consistent_widths"], det)
        self.assertGreater(det["nonuniform_fraction"][342], 0.01)

    def test_png_input_matches_p7_and_rejects_bad_files(self):
        px = [(i * 7 % 256, i * 13 % 256, i * 29 % 256) for i in range(12 * 9)]
        ref = d.Frame(p7(12, 9, px)).rgba
        for ctype in (2, 6):
            for filt in (0, 1, 4):
                self.assertEqual(d.Frame(png(12, 9, px, ctype, filt)).rgba, ref,
                                 (ctype, filt))
        good = png(12, 9, px)
        with self.assertRaises(ValueError):
            d.Frame(good[:-20])
        corrupt = bytearray(good)
        corrupt[40] ^= 1
        with self.assertRaises(ValueError):
            d.Frame(bytes(corrupt))
        with self.assertRaises(ValueError):
            d.Frame(b"\x89PNG\r\n\x1a\n")

    def test_scale_and_safe_area_mirror_native_header(self):
        self.assertEqual(d.integer_scale(342, 224, 1280, 720), (3, 127, 24, 1026, 672))
        self.assertEqual(d.integer_scale(342, 224, 3840, 2160)[0], 9)
        self.assertEqual(d.integer_scale(256, 224, 1024, 768)[0], 3)
        self.assertIsNone(d.integer_scale(342, 224, 300, 700))
        self.assertEqual(d.title_safe(342, 224), (18, 12, 306, 200))
        self.assertEqual(d.action_safe(256, 224), (7, 6, 242, 212))
        self.assertIsNone(d.title_safe(10, 10))

    def test_multi_resolution_logical_equivalence(self):
        grid, w, h = logical_canvas()
        put(grid, w, 30, 30, 40, 8, FG)
        a = render(grid, w, h, 1280, 720)
        b = render(grid, w, h, 1920, 1080)
        rep = d.compare_resolutions(a, b, w, h, mode="integer")
        self.assertTrue(rep["pass"], rep)
        self.assertEqual((rep["a"]["scale"][0], rep["b"]["scale"][0]), (3, 4))
        put(grid, w, 100, 100, 2, 1, FG)
        c = render(grid, w, h, 1920, 1080)
        rep = d.compare_resolutions(a, c, w, h, mode="integer")
        self.assertFalse(rep["pass"])
        self.assertEqual(rep["differing_logical_pixels"], 2)
        self.assertEqual(rep["difference_bbox"], [100, 100, 102, 101])

    def test_blur_is_detected_as_nonuniform_blocks(self):
        grid, w, h = logical_canvas()
        put(grid, w, 30, 30, 40, 8, FG)
        a = render(grid, w, h, 1280, 720)
        pixels = [a.rgb(x, y) for y in range(a.height) for x in range(a.width)]
        pixels[(24 + 30 * 3) * a.width + 127 + 30 * 3] = (1, 2, 3)
        blurred = d.Frame(p7(a.width, a.height, pixels))
        self.assertGreater(d.extract_logical(blurred, w, h, "integer")["nonuniform_blocks"], 0)

    def test_clip_inside_and_outside_safe_area(self):
        grid, w, h = logical_canvas()
        put(grid, w, 30, 30, 40, 8, FG)
        ok = d.clip_audit(render(grid, w, h, 1280, 720), w, h, [FG], mode="integer")
        self.assertTrue(ok["pass"], ok)
        put(grid, w, 12, 100, 20, 8, FG)  # intrudes into title-unsafe margin
        bad = d.clip_audit(render(grid, w, h, 1280, 720), w, h, [FG], mode="integer")
        self.assertFalse(bad["pass"])
        self.assertTrue(d.clip_audit(render(grid, w, h, 1280, 720), w, h, [FG],
                                     "action", "integer")["pass"])
        put(grid, w, 0, 100, 4, 8, FG)  # touches viewport edge: clipped
        edge = d.clip_audit(render(grid, w, h, 1280, 720), w, h, [FG], "action", "integer")
        self.assertFalse(edge["pass"])
        self.assertGreater(edge["viewport_edge_pixels"], 0)
        with self.assertRaises(ValueError):
            d.clip_audit(render(grid, w, h, 1280, 720), w, h, [(9, 9, 9)], mode="integer")

    def test_focus_requires_exactly_one_bar(self):
        grid, w, h = logical_canvas(256, 224)
        self.assertFalse(d.focus_audit(render(grid, w, h, 1024, 768), BAR, 3)["pass"])
        put(grid, w, 20, 60, 3, 16, BAR)
        rep = d.focus_audit(render(grid, w, h, 1024, 768), BAR, 3)
        self.assertTrue(rep["pass"], rep)
        self.assertEqual(len(rep["bars"]), 1)
        put(grid, w, 20, 100, 3, 16, BAR)
        self.assertFalse(d.focus_audit(render(grid, w, h, 1024, 768), BAR, 3)["pass"])

    def test_local_contrast_flags_low_contrast_text(self):
        grid, w, h = logical_canvas()
        put(grid, w, 30, 30, 40, 8, (152, 152, 152))
        put(grid, w, 50, 20, 8, 30, (80, 80, 80))
        frame = render(grid, w, h, 1280, 720)
        roi = (127 + 90, 24 + 60, 127 + 3 * 80, 24 + 3 * 60)
        low = d.local_contrast(frame, roi, (152, 152, 152))
        self.assertFalse(low["pass"])
        self.assertLess(low["worst_ratio"], 4.5)
        grid2, _, _ = logical_canvas()
        put(grid2, w, 30, 30, 40, 8, (200, 200, 200))
        put(grid2, w, 50, 20, 8, 30, (80, 80, 80))
        good = d.local_contrast(render(grid2, w, h, 1280, 720), roi, (200, 200, 200))
        self.assertTrue(good["pass"], good)

    def test_provenance_pin_and_cli(self):
        grid, w, h = logical_canvas()
        put(grid, w, 30, 30, 40, 8, FG)
        frame = render(grid, w, h, 1280, 720)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "f.p7"
            path.write_bytes(p7(frame.width, frame.height,
                                [frame.rgb(x, y) for y in range(frame.height)
                                 for x in range(frame.width)]))
            argv = ["clip", str(path), "--logical", "342", "224",
                    "--colour", "#c8c8c8", "--require", "--mode", "integer"]
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(d.main(argv + ["--expect-sha256", frame.sha256]), 0)
            self.assertEqual(json.loads(out.getvalue())["input_sha256"], frame.sha256)
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(d.main(argv + ["--expect-sha256", "0" * 64]), 1)
            report = json.loads(out.getvalue())
            self.assertFalse(report["human_visual_approved"])
            self.assertEqual(report["release_gate_credit"], 0)


if __name__ == "__main__":
    unittest.main()
