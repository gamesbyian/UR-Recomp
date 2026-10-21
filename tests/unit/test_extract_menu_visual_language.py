import copy
import hashlib
import json
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import extract_menu_visual_language as mvl  # noqa: E402


def put_entry(vram: bytearray, map_base: int, tx: int, ty: int, tile: int, palette: int) -> None:
    addr = (map_base + (ty % 32) * 32 + tx % 32) * 2
    entry = tile | palette << 10 | 0x2000
    vram[addr], vram[addr + 1] = entry & 0xFF, entry >> 8


def write_label(vram: bytearray, map_base: int, tx: int, ty: int, text: str) -> None:
    for ch in text:
        if ch != " ":
            slot = mvl.slot_for_char(ch)
            for dx, dy, tile in ((0, 0, 0), (1, 0, 1), (0, 1, 0x50), (1, 1, 0x51)):
                put_entry(vram, map_base, tx + dx, ty + dy, 2 * slot + tile, 7)
        tx += 2


class MenuVisualLanguageTests(unittest.TestCase):
    def test_encoding_matches_recovered_slots(self) -> None:
        # Slots observed in the MAIN_MENU tilemap: 1P, LEAGUE, OPTIONS.
        self.assertEqual([2 * mvl.slot_for_char(c) for c in "1P"], [0x02, 0x30])
        self.assertEqual([2 * mvl.slot_for_char(c) for c in "LEAGUE"],
                         [0x2A, 0x1C, 0x14, 0x20, 0x3A, 0x1C])
        self.assertEqual([2 * mvl.slot_for_char(c) for c in "OPTIONS"],
                         [0x00, 0x30, 0x38, 0x24, 0x00, 0x2E, 0x36])
        self.assertEqual(mvl.char_for_slot(35), "OK")
        self.assertEqual(mvl.char_for_slot(39), "ICON_STUNT_HOOK")
        self.assertEqual(mvl.glyph_tiles(3), [6, 7, 0x56, 0x57])

    def test_text_rows_decode_spacing_and_centering(self) -> None:
        vram = bytearray(0x10000)
        write_label(vram, 0x1000, 3, 19, "DEFINE PLAYER")
        write_label(vram, 0x1000, 14, 10, "1P")
        rows = mvl.text_rows(bytes(vram), 0x1000, 64, 64, 7, 0)
        self.assertEqual([r["text"] for r in rows], ["1P", "DEFINE PLAYER"])
        self.assertEqual(rows[0]["center_x"], 128)
        self.assertEqual(rows[1]["center_x"], 128)
        self.assertEqual(rows[1]["x_left"], 24)

    def test_text_rows_handle_single_tile_gaps(self) -> None:
        vram = bytearray(0x10000)
        write_label(vram, 0x1000, 4, 1, "PICK")
        put_entry(vram, 0x1000, 12, 1, 0xCE, 7)  # 8-px small-font space between words
        write_label(vram, 0x1000, 13, 1, "UNI")
        rows = mvl.text_rows(bytes(vram), 0x1000, 64, 64, 7, 0)
        self.assertEqual(rows[0]["text"], "PICK UNI")
        self.assertEqual(rows[0]["word_gaps_px"], [8])

    def test_small_font_runs(self) -> None:
        vram = bytearray(0x10000)
        for i, ch in enumerate("ZOOM ZOO"):
            tile = 0xCE if ch == " " else (0xA9 if ch == "O" else 0xB3 + ord(ch) - ord("A") - (1 if ch > "O" else 0))
            put_entry(vram, 0x1000, 10 + i, 11, tile, 7)
        self.assertEqual(mvl.small_char_for_tile(0xBF), "M")
        self.assertEqual(mvl.small_char_for_tile(0xCA), "Y")
        runs = mvl.small_text_rows(bytes(vram), 0x1000, 64, 64, 7, 0)
        self.assertEqual([(r["text"], r["x_left"]) for r in runs], [("ZOOM ZOO", 80)])

    def test_sfx_bursts_onset_duration_and_quiet_baseline(self) -> None:
        rms = [0.0] * 40
        for f in range(10, 15):
            rms[f] = 900.0  # move sound on the press frame
        for f in range(23, 30):
            rms[f] = 900.0  # confirm sound three frames late
        bursts = mvl.sfx_bursts(rms, [(10, "down"), (20, "a"), (28, "x")])
        self.assertEqual((bursts[0]["onset_offset_frames"], bursts[0]["duration_frames"]), (0, 5))
        self.assertTrue(bursts[0]["baseline_quiet"])
        self.assertEqual(bursts[1]["onset_offset_frames"], 3)
        self.assertFalse(bursts[2]["baseline_quiet"])

    def test_letter_o_is_word_local(self) -> None:
        self.assertEqual(mvl.letter_o("Z00M Z00"), "ZOOM ZOO")
        self.assertEqual(mvl.letter_o("MOST WINS:    0"), "MOST WINS:    0")
        self.assertEqual(mvl.letter_o("0:28.56 0%"), "0:28.56 0%")

    def test_small_font_punctuation_and_flipped_paren(self) -> None:
        self.assertEqual(mvl.small_char_for_tile(0xCC), ":")
        self.assertEqual(mvl.small_char_for_tile(0xA4), "(")
        self.assertEqual(mvl.small_char_for_tile(0xA4, hflip=True), ")")
        self.assertEqual(mvl.small_char_for_tile(0xA7), "-")
        self.assertEqual(mvl.small_char_for_tile(0xA3), "'")
        self.assertEqual(mvl.small_char_for_tile(0xA5), "+")
        self.assertIsNone(mvl.small_char_for_tile(0xA6))

    def test_run_lengths_and_deltas(self) -> None:
        self.assertEqual(mvl.run_lengths([8, 8, 4, 4, 0]), [[8, 2], [4, 2], [0, 1]])
        self.assertEqual(mvl.deltas([0, 1, 3, 6]), [1, 2, 3])

    def test_four_atlas_bundle_rejects_mixed_source_captures(self) -> None:
        # Synthetic SHA-only fixtures, never game or exported asset bytes.
        h = lambda c: c * 64
        tag = "mvl-idle-000"
        big = {"source_fixture": mvl.SCRIPT, "source_tag": tag,
               "dimensions": [640, 16], "image_png_sha256": h("a"),
               "source_vram_sha256": h("b"), "source_cgram_sha256": h("c")}
        small = {"source_fixture": mvl.SCRIPT, "source_tag": "mvl-track-00",
                 "dimensions": [360, 16], "sha256": h("d"),
                 "source_vram_sha256": h("e"), "source_cgram_sha256": h("f"),
                 "source_char_base_word": 0}
        cursor = {"source_fixture": mvl.SCRIPT, "atlas_rgba_dimensions": [624, 39],
                  "atlas_png_sha256": h("a"), "captured_idle_frames": 64,
                  "frames_per_pose": 2, "cycle_frames": 32,
                  "source_frames": [
                      {"source_tag": f"mvl-idle-{i * 2:03d}",
                       "source_obj_tile": tile,
                       "ppu_sha256": {"vram": h("b"), "cgram": h("c"), "oam": h("f")}}
                      for i, tile in enumerate(mvl.CURSOR_SOURCE_TILE_CYCLE)]}
        bg1 = {"source_fixture": mvl.SCRIPT, "source_tag": tag,
               "dimensions": [256, 224], "png_sha256": h("d"),
               "vram_sha256": h("b"), "cgram_sha256": h("c")}
        receipt = mvl.build_menu_source_art_bundle(big, small, cursor, bg1)
        self.assertTrue(receipt["reference_only"])
        self.assertFalse(receipt["asset_distribution_approved"])
        self.assertFalse(receipt["native_render_and_visual_acceptance"])
        self.assertEqual(receipt["source_main_tag"], tag)
        self.assertEqual(receipt["output_dimensions"]["cursor"], [624, 39])
        self.assertEqual(len(receipt["asset_png_sha256"]), 4)

        def rejects(source, mutation):
            copies = [copy.deepcopy(x) for x in (big, small, cursor, bg1)]
            mutation(copies[source])
            with self.assertRaises(ValueError):
                mvl.build_menu_source_art_bundle(*copies)

        rejects(0, lambda a: a.update(source_vram_sha256=h("f")))
        rejects(1, lambda a: a.update(source_tag="mvl-idle-00"))
        rejects(1, lambda a: a.update(source_char_base_word=None))
        rejects(2, lambda a: a.update(atlas_rgba_dimensions=[623, 39]))
        rejects(2, lambda a: a["source_frames"][0].update(source_obj_tile=4))
        rejects(2, lambda a: a["source_frames"][1].update(
            source_tag="mvl-idle-003"))
        rejects(2, lambda a: a["source_frames"][0]["ppu_sha256"].update(vram=h("f")))
        rejects(3, lambda a: a.update(source_tag="mvl-idle-09"))
        rejects(3, lambda a: a.update(cgram_sha256=""))
        rejects(3, lambda a: a.update(dimensions=[256, 216]))
        rejects(0, lambda a: a.update(source_fixture="other reference"))

    def test_original_big_font_atlas_has_source_identity_receipt(self) -> None:
        class Sample:
            pass

        d = Sample()
        d.tag = "mvl-idle-00"
        d.vram = bytearray(65536)
        d.cgram = bytearray(512)
        with tempfile.TemporaryDirectory() as td:
            atlas = Path(td) / "main-title.png"
            mvl.write_atlas(atlas, d, 0)
            receipt = mvl.original_big_font_manifest(atlas, d, 0)
            self.assertEqual(receipt["dimensions"], [640, 16])
            self.assertEqual(receipt["glyph_cell"], [16, 16])
            self.assertEqual(receipt["source_char_base_word"], 0)
            self.assertEqual(len(receipt["slots"]), 40)
            self.assertEqual(receipt["slots"][0], "0")
            self.assertNotIn("O", receipt["slots"])
            self.assertEqual(receipt["slots"][35], "OK")
            self.assertEqual(receipt["source_tag"], "mvl-idle-00")
            self.assertEqual(receipt["image_png_sha256"],
                             hashlib.sha256(atlas.read_bytes()).hexdigest())
            self.assertEqual(receipt["source_vram_sha256"],
                             hashlib.sha256(d.vram).hexdigest())
            self.assertEqual(receipt["source_cgram_sha256"],
                             hashlib.sha256(d.cgram).hexdigest())

    def test_original_bg1_mode3_8bpp_source_flips_scroll_and_16px(self) -> None:
        class Sample:
            pass

        d = Sample()
        d.tag = "mvl-idle-00"
        d.vram = bytearray(65536)
        d.cgram = bytearray(512)
        d.fillram = {"2105": "03", "2107": "04", "210B": "00"}
        d.ppu = {"bg": [{"hofs": 0, "vofs": 0}]}
        # Tilemap starts at 0x400 words (0x800 bytes), separate from
        # BG1 8bpp tile1's VRAM character address 0x40.
        d.vram[0x800:0x802] = (1).to_bytes(2, "little")
        d.vram[1 * 64] = 0x80  # tile1 x0/y0, palette index 1
        d.cgram[2:4] = (0x001F).to_bytes(2, "little")  # red = 248
        rgba = mvl.original_menu_bg1_rgba(d)
        self.assertEqual(rgba[0:4], bytes([248, 0, 0, 255]))
        self.assertEqual(rgba[4:8], bytes(4))  # transparent BG1 index 0
        # Hardware H-flip mirrors the real tile sample to the last column.
        d.vram[0x800:0x802] = (1 | 0x4000).to_bytes(2, "little")
        rgba = mvl.original_menu_bg1_rgba(d)
        self.assertEqual(rgba[0:4], bytes(4))
        self.assertEqual(rgba[7 * 4:8 * 4], bytes([248, 0, 0, 255]))
        # The source hscroll register moves that rightmost red source
        # pixel to host x6, never a duplicate overlay.
        d.ppu["bg"][0]["hofs"] = 1
        rgba = mvl.original_menu_bg1_rgba(d)
        self.assertEqual(rgba[6 * 4:7 * 4], bytes([248, 0, 0, 255]))
        d.ppu["bg"][0]["hofs"] = 0
        # 16x16 BG tiles are 2x2 8x8 tiles, with right tile at +1.
        d.fillram["2105"] = "13"
        d.vram[0x800:0x802] = (1).to_bytes(2, "little")
        d.vram[2 * 64] = 0x80
        rgba = mvl.original_menu_bg1_rgba(d)
        self.assertEqual(rgba[8 * 4:9 * 4], bytes([248, 0, 0, 255]))
        with self.assertRaisesRegex(ValueError, "MODE3"):
            d.fillram["2105"] = "01"
            mvl.original_menu_bg1_rgba(d)
        with self.assertRaisesRegex(ValueError, "BGMODE"):
            d.fillram.pop("2105")
            mvl.original_menu_bg1_rgba(d)

    def test_bg1_source_art_output_manifest_is_layer_specific(self) -> None:
        class Sample:
            pass

        d = Sample()
        d.tag = "mvl-idle-00"
        d.vram = bytearray(65536)
        d.cgram = bytearray(512)
        d.fillram = {"2105": "03", "2107": "04", "210B": "00"}
        d.ppu = {"bg": [{"hofs": 0, "vofs": 0}]}
        d.vram[0x800:0x802] = (1).to_bytes(2, "little")
        d.vram[1 * 64] = 0x80
        d.cgram[2:4] = (0x001F).to_bytes(2, "little")
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "bg1.png"
            info = mvl.write_original_menu_bg1(out, d)
            self.assertEqual(info["dimensions"], [256, 224])
            self.assertEqual(info["layers"], ["BG1 8bpp MODE3 only"])
            self.assertEqual(info["source_bg_mode"], 3)
            self.assertEqual(info["source_bg1_map_base_word"], 0x400)
            self.assertEqual(info["source_bg1_char_base_word"], 0)
            self.assertEqual(info["source_bg1_scroll"], [0, 0])
            self.assertEqual(info["source_registers_sha256"], hashlib.sha256(
                json.dumps({"fillram": d.fillram, "ppu": d.ppu},
                           sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest())
            self.assertEqual(info["png_sha256"], hashlib.sha256(out.read_bytes()).hexdigest())
            self.assertEqual(info["rgba_sha256"],
                             hashlib.sha256(mvl.original_menu_bg1_rgba(d)).hexdigest())

    def test_original_small_font_atlas_uses_real_vram_and_hflip(self) -> None:
        class Sample:
            pass

        sample = Sample()
        sample.tag = "mvl-track-00"
        sample.vram = bytearray(65536)
        sample.cgram = bytearray(512)
        pal = 7 * 16 + 9  # measured small-font grey ramp
        sample.cgram[2 * pal:2 * pal + 2] = (0x4210).to_bytes(2, "little")
        for tile in (mvl.SMALL_FONT_FIRST_TILE, 0xA4):
            sample.vram[tile * 32] = 0x80
            sample.vram[(tile + mvl.SMALL_FONT_BOTTOM_OFFSET) * 32] = 0x80
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "detail.png"
            info = mvl.write_small_font_atlas(path, sample, 0)
            glyphs = info["glyphs"]
            positions = {g["character"]: idx for idx, g in enumerate(glyphs)}
            self.assertEqual(glyphs[positions["0"]]["tile"],
                             glyphs[positions["O"]]["tile"])
            self.assertEqual(glyphs[positions[")"]]["tile"], 0xA4)
            self.assertTrue(glyphs[positions[")"]]["hflip"])
            self.assertEqual(info["glyph_cell"], [8, 16])
            self.assertEqual(info["source_char_base_word"], 0)
            self.assertEqual(info["source_vram_sha256"], hashlib.sha256(
                sample.vram).hexdigest())
            self.assertEqual(info["source_cgram_sha256"], hashlib.sha256(
                sample.cgram).hexdigest())
            self.assertEqual(info["dimensions"], [len(glyphs) * 8, 16])
            self.assertEqual(info["sha256"],
                             hashlib.sha256(path.read_bytes()).hexdigest())
            raw = path.read_bytes()
            start = raw.index(b"IDAT")
            count = struct.unpack(">I", raw[start - 4:start])[0]
            pixels = zlib.decompress(raw[start + 4:start + 4 + count])
            line_size = len(glyphs) * 8 * 4 + 1

            def rgba_for(ch: str, local_x: int, y: int = 0) -> bytes:
                glyph_idx = positions[ch]
                pos = y * line_size + 1 + (glyph_idx * 8 + local_x) * 4
                return pixels[pos:pos + 4]

            self.assertEqual(rgba_for("0", 0), rgba_for("O", 0))
            self.assertEqual(rgba_for("(", 0)[3], 255)
            self.assertEqual(rgba_for(")", 0)[3], 0)
            self.assertEqual(rgba_for(")", 7), rgba_for("(", 0))
            self.assertEqual(rgba_for(" ", 0), bytes(4))

    def test_real_obj_vram_page_palette_and_transparency_contract(self) -> None:
        # Synthetic ORIGINAL-PPU-format bytes; no ROM/binary art in tests.
        class Sample:
            pass

        sample = Sample()
        sample.fillram = {"2101": "29"}  # base=1, OBJ size 8/32, name select=1
        sample.vram = bytearray(65536)
        sample.cgram = bytearray(512)
        # Tile 0x100 names the second OBJ tile page at base + 16 KiB.
        # 4bpp pixel0=palette index1: first bit set in plane 0.
        # base=0x2000 words; name-select=1 => +0x2000 words.
        second_page_byte = ((0x2000 + 0x2000) * 2) % 65536
        sample.vram[second_page_byte] = 0x80
        pal = 128 + 7 * 16 + 1
        sample.cgram[2 * pal:2 * pal + 2] = (0x7FFF).to_bytes(2, "little")
        rgba = mvl.obj_sprite_rgba(
            sample, {"tile": 256, "palette": 7, "large": 1})
        self.assertEqual(len(rgba), 32 * 32 * 4)
        self.assertEqual(rgba[:4], bytes([248, 248, 248, 255]))
        self.assertEqual(rgba[4:8], bytes(4))
        flip_h = mvl.obj_sprite_rgba(
            sample, {"tile": 256, "palette": 7, "large": 1, "hflip": True})
        flip_v = mvl.obj_sprite_rgba(
            sample, {"tile": 256, "palette": 7, "large": 1, "vflip": True})
        flip_both = mvl.obj_sprite_rgba(
            sample, {"tile": 256, "palette": 7, "large": 1,
                     "hflip": True, "vflip": True})
        source_pixel = rgba[:4]
        self.assertEqual(flip_h[31 * 4:32 * 4], source_pixel)
        self.assertEqual(flip_v[31 * 32 * 4:31 * 32 * 4 + 4], source_pixel)
        self.assertEqual(flip_both[(32 * 32 - 1) * 4:], source_pixel)
        self.assertEqual(flip_both[:4], bytes(4))
        # Original OBJSEL size modes 6/7 use rectangular sprite pairs.
        # Mode6 large is 32x64, and mode7 small is 16x32; neither can be
        # falsely exported as an original square 32x32 cursor.
        sample.fillram["2101"] = "C1"  # mode6, base1
        with self.assertRaisesRegex(ValueError, "32x32"):
            mvl.obj_sprite_rgba(sample, {"tile": 256, "palette": 7, "large": 1})
        sample.fillram["2101"] = "E1"  # mode7, base1
        with self.assertRaisesRegex(ValueError, "32x32"):
            mvl.obj_sprite_rgba(sample, {"tile": 256, "palette": 7, "large": 0})
        self.assertEqual(len(mvl.obj_sprite_rgba(
            sample, {"tile": 256, "palette": 7, "large": 1})), 4096)
        sample.fillram["2101"] = "29"
        # A BG character base mistakenly substituted for OBSEL would
        # decode this all-transparent or from the wrong page.
        sample.fillram.clear()
        with self.assertRaisesRegex(ValueError, "OBJSEL"):
            mvl.obj_sprite_rgba(sample, {"tile": 256, "palette": 7, "large": 1})

    def test_oam_sprite_flip_flags_are_preserved(self) -> None:
        oam = bytearray(544)
        oam[0:4] = bytes([79, 70, 8, (7 << 1) | 0xC0])
        oam[512] = 2  # 32x32 large-size sprite
        observed = mvl.sprites(oam)
        self.assertEqual(observed[0]["tile"], 8)
        self.assertTrue(observed[0]["hflip"])
        self.assertTrue(observed[0]["vflip"])
        self.assertEqual(observed[0]["palette"], 7)

    def test_obj_name_base_is_16kib_bytes_not_8kib(self) -> None:
        # SNESdev PPU $2101: name-base WORD address = (bBB << 13).
        # This discriminates a parallel research extractor's erroneous
        # *0x1000-word formula. Do not silently accept a plausible decoy.
        class Sample:
            pass

        source = Sample()
        source.fillram = {"2101": "21"}  # large 8/32 mode, base=1, select=0
        source.vram = bytearray(65536)
        # Real base=0x2000 words -> 0x4000 bytes. Wrong base=0x1000
        # words would read a deliberately distinct second location.
        source.vram[0x4000] = 0x80  # source tile 0, pixel 0 = index 1
        source.vram[0x2001] = 0x80  # decoy wrong-base index 2
        self.assertEqual(mvl.obj_tile_pixels(source, 0)[0][0], 1)
        self.assertEqual(mvl.tile_pixels(
            source.vram, 0x1000, 0, 4)[0][0], 2)
        # High name bit uses (NN+1)*0x1000 WORDS relative to that
        # base. With NN=1, the high-table tile 0x100 moves +0x2000
        # words, not +0x2000 bytes.
        source.fillram["2101"] = "29"  # base1 / name select1
        source.vram[0x8000] = 0x80  # (0x2000+0x2000) words *2 bytes
        self.assertEqual(mvl.obj_tile_pixels(source, 256)[0][0], 1)

    def test_source_cursor_atlas_16_poses_manifest_and_forgery_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            dump_dir = Path(td) / "source"
            dump_dir.mkdir()
            vram = bytearray(65536)
            cgram = bytearray(512)
            arrow = 128 + 7 * 16 + 1
            shadow = 128 + 5 * 16 + 1
            cgram[2 * arrow:2 * arrow + 2] = (0x7FFF).to_bytes(2, "little")
            cgram[2 * shadow:2 * shadow + 2] = (0x4210).to_bytes(2, "little")
            # Stock VRAM is ALREADY POPULATED before the idle animation
            # starts. Filling CHR tiles progressively inside the frame loop
            # falsely makes the cursor shadow acquire new pixels mid-cycle.
            for tile in mvl.CURSOR_SOURCE_TILE_CYCLE:
                vram[tile * 32] = 0x80
                vram[(16 + tile) * 32] = 0x80
                vram[(tile + 4) * 32] = 0x80
            for index in range(64):
                tile = mvl.CURSOR_SOURCE_TILE_CYCLE[(index // 2) % 16]
                # Every source snapshot sees the same preloaded CHR atlas.
                # Only original OAM selects the rotating pose each frame.
                oam = bytearray(544)
                oam[0:4] = bytes([79, 70, tile, 7 << 1])
                oam[4:8] = bytes([86, 77, (tile + 4) & 255, 5 << 1])
                oam[512] = 0x0A  # OAM 0,1 use large=32 mode1
                tag = f"mvl-idle-{index:03d}"
                (dump_dir / f"{tag}.vram.bin").write_bytes(vram)
                (dump_dir / f"{tag}.cgram.bin").write_bytes(cgram)
                (dump_dir / f"{tag}.oam.bin").write_bytes(oam)
                (dump_dir / f"{tag}.wram.bin").write_bytes(bytes(0x20000))
                (dump_dir / f"{tag}.regs.json").write_text(json.dumps(
                    {"fillram": {"2101": "20"}, "ppu": {"bg": []}}
                ))
            png = Path(td) / "cursor.png"
            manifest = Path(td) / "cursor.json"
            receipt = mvl.export_cursor_atlas(dump_dir, png, manifest)
            self.assertEqual(receipt["atlas_rgba_dimensions"], [624, 39])
            self.assertEqual(len(receipt["source_frames"]), 16)
            self.assertEqual(receipt["captured_idle_frames"], 64)
            self.assertEqual(receipt["source_frames"][0]["source_tag"], "mvl-idle-000")
            self.assertEqual({f["source_obj_sel"]
                              for f in receipt["source_frames"]}, {0x20})
            self.assertEqual([f["source_obj_tile"] for f in receipt["source_frames"]],
                             list(mvl.CURSOR_SOURCE_TILE_CYCLE))
            self.assertEqual(hashlib.sha256(png.read_bytes()).hexdigest(),
                             receipt["atlas_png_sha256"])
            self.assertEqual(json.loads(manifest.read_text()), receipt)
            # One syntactically valid wrong tile at sample 003 must fail
            # the original 2-frame CHR cadence, not be silently skipped.
            sample3 = dump_dir / "mvl-idle-003.oam.bin"
            original_oam = sample3.read_bytes()
            wrong_oam = bytearray(original_oam)
            wrong_oam[2] = 8
            sample3.write_bytes(wrong_oam)
            with self.assertRaisesRegex(ValueError, "cadence"):
                mvl.export_cursor_atlas(dump_dir, png)
            sample3.write_bytes(original_oam)
            # The same tile with changed original CGRAM is *not* the same
            # source pose and must fail despite the identical OAM index.
            sample1 = dump_dir / "mvl-idle-001.cgram.bin"
            original_cgram = sample1.read_bytes()
            changed = bytearray(original_cgram)
            changed[2 * arrow:2 * arrow + 2] = (0x001F).to_bytes(2, "little")
            sample1.write_bytes(changed)
            with self.assertRaisesRegex(ValueError, "drifted"):
                mvl.export_cursor_atlas(dump_dir, png)
            sample1.write_bytes(original_cgram)
            # The complete 64-frame sequence is mandatory. A short 16-pose
            # set cannot establish the stock 2-tick hold / 32-tick period.
            (dump_dir / "mvl-idle-063.vram.bin").unlink()
            with self.assertRaisesRegex(ValueError, "all 64 source idle frames"):
                mvl.export_cursor_atlas(dump_dir, png)

    def test_png_writer_emits_valid_stream(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "a.png"
            mvl.write_png(path, 2, 1, bytes([255, 0, 0, 255, 0, 255, 0, 255]))
            data = path.read_bytes()
            self.assertTrue(data.startswith(b"\x89PNG\r\n\x1a\n"))
            width, height = struct.unpack(">II", data[16:24])
            self.assertEqual((width, height), (2, 1))
            idat = data.index(b"IDAT")
            length = struct.unpack(">I", data[idat - 4:idat])[0]
            self.assertEqual(zlib.decompress(data[idat + 4:idat + 4 + length])[:5], b"\x00\xff\x00\x00\xff")


if __name__ == "__main__":
    unittest.main()
