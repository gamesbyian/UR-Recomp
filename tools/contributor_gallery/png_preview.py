#!/usr/bin/env python3
"""Conservative dependency-free downscaling of 8-bit noninterlaced PNG references.

The original art remains untouched. Public Pages carries only RGB previews;
the exact original GitHub blobs remain available via source links.

No network, subprocess, external image-codec library, palette changes to source,
or side effects other than writing the explicitly requested preview.
"""
from __future__ import annotations

import struct
import zlib
from pathlib import Path

SIGNATURE = bytes((137, 80, 78, 71, 13, 10, 26, 10))


def _chunk(tag: bytes, body: bytes) -> bytes:
    data = tag + body
    return struct.pack(">I", len(body)) + data + struct.pack(">I", zlib.crc32(data) & 0xFFFFFFFF)


def dimensions(data: bytes) -> tuple[int, int]:
    if len(data) < 33 or data[:8] != SIGNATURE or data[12:16] != b"IHDR":
        raise ValueError("invalid PNG signature or IHDR")
    width, height = struct.unpack(">II", data[16:24])
    if not (100 <= width <= 10000 and 100 <= height <= 10000):
        raise ValueError("PNG dimensions out of bounds")
    return width, height


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    da, db, dc = abs(p-a), abs(p-b), abs(p-c)
    if da <= db and da <= dc:
        return a
    if db <= dc:
        return b
    return c


def _source_rows(raw: bytes, width: int, height: int, channels: int) -> list[bytes]:
    stride = width * channels
    expected = (stride + 1) * height
    if len(raw) != expected:
        raise ValueError("unexpected PNG raster size")
    result = []
    prev = bytearray(stride)
    cursor = 0
    for _ in range(height):
        filt = raw[cursor]
        cursor += 1
        row = bytearray(raw[cursor:cursor+stride])
        cursor += stride
        if filt not in (0, 1, 2, 3, 4):
            raise ValueError("unsupported PNG filter")
        if filt:
            for i in range(stride):
                a = row[i-channels] if i >= channels else 0
                b = prev[i]
                c = prev[i-channels] if i >= channels else 0
                if filt == 1:
                    predictor = a
                elif filt == 2:
                    predictor = b
                elif filt == 3:
                    predictor = (a+b)//2
                else:
                    predictor = _paeth(a,b,c)
                row[i] = (row[i] + predictor) & 255
        prev = row
        result.append(bytes(row))
    return result


def _rgba_to_rgb(rows: list[bytes], color_type: int, width: int, palette: bytes | None, transparency: bytes | None) -> list[bytes]:
    rgb_rows = []
    for row in rows:
        if color_type == 2:
            rgb_rows.append(row)
            continue
        dest = bytearray(width*3)
        for col in range(width):
            p = col*3
            if color_type == 6:
                q = col*4
                r,g,b,a = row[q:q+4]
            elif color_type == 0:
                r = g = b = row[col]
                a = 255
            elif color_type == 4:
                q = col*2
                r = g = b = row[q]
                a = row[q+1]
            elif color_type == 3:
                idx = row[col]
                if palette is None or 3*idx+3 > len(palette):
                    raise ValueError("invalid indexed palette")
                r,g,b = palette[3*idx:3*idx+3]
                a = transparency[idx] if transparency is not None and idx < len(transparency) else 255
            else:
                raise ValueError("unsupported PNG color type")
            if a != 255:
                r = (r*a + 255*(255-a) + 127)//255
                g = (g*a + 255*(255-a) + 127)//255
                b = (b*a + 255*(255-a) + 127)//255
            dest[p:p+3] = bytes((r,g,b))
        rgb_rows.append(bytes(dest))
    return rgb_rows


def preview(source: Path, destination: Path, max_width: int = 960, max_height: int = 720) -> dict:
    """Convert an exact-source PNG to a bounded, box-averaged RGB PNG preview."""
    if max_width < 64 or max_height < 64:
        raise ValueError("too-small preview dimensions")
    if source.is_symlink() or not source.is_file() or destination.exists() or destination.is_symlink():
        raise ValueError("unsafe source/destination")
    payload = source.read_bytes()
    width, height = dimensions(payload)
    pos = 8
    compressed = []
    palette = transparency = None
    color_type = bit_depth = interlace = None
    saw_iend = False
    compressed_size = 0
    while pos + 12 <= len(payload):
        length = struct.unpack(">I", payload[pos:pos+4])[0]
        if length > 20_000_000 or pos + 12 + length > len(payload):
            raise ValueError("oversized or truncated PNG chunk")
        kind = payload[pos+4:pos+8]
        data = payload[pos+8:pos+8+length]
        checksum = struct.unpack(">I", payload[pos+8+length:pos+12+length])[0]
        if zlib.crc32(kind+data) & 0xFFFFFFFF != checksum:
            raise ValueError("PNG chunk CRC mismatch")
        if kind == b"IHDR":
            bit_depth = data[8]
            color_type = data[9]
            interlace = data[12]
            if data[10:12] != b"\x00\x00":
                raise ValueError("unsupported PNG compression/filter method")
        elif kind == b"PLTE":
            palette = data
        elif kind == b"tRNS":
            transparency = data
        elif kind == b"IDAT":
            compressed.append(data)
            compressed_size += len(data)
            if compressed_size > 16_000_000:
                raise ValueError("oversized PNG raster data")
        elif kind == b"IEND":
            saw_iend = True
            break
        elif kind[:1].isupper() and kind not in (b"cHRM", b"gAMA", b"sRGB"):
            raise ValueError("unknown critical PNG chunk")
        pos += length + 12
    if not saw_iend or not compressed or bit_depth != 8 or interlace != 0 or color_type not in (0,2,3,4,6):
        raise ValueError("unsupported 8-bit PNG configuration")
    channels = {0:1,2:3,3:1,4:2,6:4}[color_type]
    raw = zlib.decompress(b"".join(compressed))
    rows = _rgba_to_rgb(_source_rows(raw,width,height,channels),color_type,width,palette,transparency)
    # Integral box averaging, deterministic, no original pixel or byte changes.
    scale = max(1, (width+max_width-1)//max_width, (height+max_height-1)//max_height)
    out_width = (width+scale-1)//scale
    out_height = (height+scale-1)//scale
    compressed_rows = bytearray()
    for oy in range(out_height):
        src_y = oy*scale
        y_limit = min(height,src_y+scale)
        dest = bytearray(out_width*3)
        for ox in range(out_width):
            src_x = ox*scale
            x_limit = min(width,src_x+scale)
            total = [0,0,0]
            count = (y_limit-src_y)*(x_limit-src_x)
            for yy in range(src_y,y_limit):
                row = rows[yy]
                for xx in range(src_x,x_limit):
                    idx = xx*3
                    total[0] += row[idx]
                    total[1] += row[idx+1]
                    total[2] += row[idx+2]
            pos3 = ox*3
            dest[pos3:pos3+3] = bytes(( (v+count//2)//count for v in total ))
        compressed_rows.append(0)
        compressed_rows.extend(dest)
    ihdr = struct.pack(">IIBBBBB",out_width,out_height,8,2,0,0,0)
    result = SIGNATURE+_chunk(b"IHDR",ihdr)+_chunk(b"IDAT",zlib.compress(compressed_rows,9))+_chunk(b"IEND",b"")
    if len(result) > 2_500_000:
        raise ValueError("PNG preview exceeds 2.5MB budget; use smaller dimensions")
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_bytes(result)
    return {"source_bytes":len(payload),"preview_bytes":len(result),"width":out_width,"height":out_height,"scale":scale}
