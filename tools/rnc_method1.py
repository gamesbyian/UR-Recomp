#!/usr/bin/env python3
"""Minimal RNC ProPack Method 1 decoder used by UR-Recomp research tooling.

The implementation follows the documented RNC1 container/bitstream structure and
is validated against each stream's packed and unpacked CRC16 fields. It does not
invoke the preserved DOS packer or SNES assembly implementation.
"""
from __future__ import annotations
from dataclasses import dataclass

class RNCError(ValueError):
    pass

def crc16(data: bytes) -> int:
    """RNC/IBM CRC-16, polynomial 0xA001, initial value 0."""
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ (0xA001 if crc & 1 else 0)
    return crc & 0xFFFF

class BitReader:
    """RNC1's little-endian 16-bit bit reservoir with interleaved raw bytes."""
    def __init__(self, data: bytes, offset: int = 0, limit: int | None = None):
        self.data = data
        self.pos = offset
        self.limit = len(data) if limit is None else limit
        if not 0 <= offset <= self.limit <= len(data):
            raise RNCError("invalid bit-reader bounds")
        self.bits = 0
        self.nbits = 0

    def _byte(self) -> int:
        if self.pos >= self.limit:
            raise RNCError("unexpected end of packed RNC payload")
        b = self.data[self.pos]
        self.pos += 1
        return b

    def read_bits(self, count: int) -> int:
        if count < 0 or count > 16:
            raise RNCError(f"invalid bit count {count}")
        out = 0
        bit = 1
        for _ in range(count):
            if self.nbits == 0:
                lo = self._byte()
                hi = self._byte()
                look0 = self.data[self.pos] if self.pos < self.limit else 0
                look1 = self.data[self.pos + 1] if self.pos + 1 < self.limit else 0
                self.bits = lo | (hi << 8) | (look0 << 16) | (look1 << 24)
                self.nbits = 16
            if self.bits & 1:
                out |= bit
            self.bits >>= 1
            self.nbits -= 1
            bit <<= 1
        return out

    def read_raw_byte(self) -> int:
        return self._byte()

    def resync_after_raw(self) -> None:
        look0 = self.data[self.pos] if self.pos < self.limit else 0
        look1 = self.data[self.pos + 1] if self.pos + 1 < self.limit else 0
        look2 = self.data[self.pos + 2] if self.pos + 2 < self.limit else 0
        incoming = look0 | (look1 << 8) | (look2 << 16)
        keep_mask = (1 << self.nbits) - 1 if self.nbits else 0
        self.bits = ((incoming << self.nbits) | (self.bits & keep_mask)) & 0xFFFFFFFF

@dataclass(frozen=True)
class HuffmanEntry:
    code: int
    length: int
    value: int

def reverse_bits(value: int, count: int) -> int:
    out = 0
    for _ in range(count):
        out = (out << 1) | (value & 1)
        value >>= 1
    return out

def read_table(br: BitReader) -> list[HuffmanEntry]:
    count = br.read_bits(5)
    if count == 0:
        raise RNCError("empty Huffman table")
    if count > 16:
        raise RNCError(f"invalid Huffman symbol count {count}")
    lengths = [br.read_bits(4) for _ in range(count)]
    code_value = 0
    unit = 0x80000000
    entries: list[HuffmanEntry] = []
    for length in range(1, 17):
        for symbol, symbol_length in enumerate(lengths):
            if symbol_length == length:
                code = reverse_bits(code_value // unit, length)
                entries.append(HuffmanEntry(code, length, symbol))
                code_value += unit
        unit >>= 1
    if not entries:
        raise RNCError("Huffman table has no codes")
    return entries

def read_huffman(br: BitReader, table: list[HuffmanEntry]) -> int:
    for entry in table:
        mask = (1 << entry.length) - 1
        if (br.bits & mask) == entry.code:
            symbol = entry.value
            br.read_bits(entry.length)
            if symbol < 2:
                return symbol
            return br.read_bits(symbol - 1) | (1 << (symbol - 1))
    raise RNCError("no matching Huffman code")

@dataclass(frozen=True)
class Header:
    method: int
    unpacked_size: int
    packed_size: int
    unpacked_crc: int
    packed_crc: int
    leeway: int
    chunks: int

def parse_header(stream: bytes) -> Header:
    if len(stream) < 18 or stream[:3] != b"RNC":
        raise RNCError("not an RNC stream")
    method = stream[3]
    if method != 1:
        raise RNCError(f"unsupported RNC method {method}")
    return Header(
        method=method,
        unpacked_size=int.from_bytes(stream[4:8], "big"),
        packed_size=int.from_bytes(stream[8:12], "big"),
        unpacked_crc=int.from_bytes(stream[12:14], "big"),
        packed_crc=int.from_bytes(stream[14:16], "big"),
        leeway=stream[16],
        chunks=stream[17],
    )

def unpack_method1(stream: bytes) -> bytes:
    h = parse_header(stream)
    end = 18 + h.packed_size
    if end > len(stream):
        raise RNCError("truncated packed payload")
    payload = stream[18:end]
    actual_packed_crc = crc16(payload)
    if actual_packed_crc != h.packed_crc:
        raise RNCError(f"packed CRC mismatch: {actual_packed_crc:04X} != {h.packed_crc:04X}")

    br = BitReader(stream, 18, end)
    br.read_bits(2)
    out = bytearray()

    while len(out) < h.unpacked_size:
        raw_table = read_table(br)
        distance_table = read_table(br)
        length_table = read_table(br)
        chunks = br.read_bits(16)
        if chunks == 0:
            raise RNCError("zero chunk count before output completed")

        while chunks:
            raw_count = read_huffman(br, raw_table)
            for _ in range(raw_count):
                if len(out) >= h.unpacked_size:
                    raise RNCError("raw copy exceeds declared unpacked size")
                out.append(br.read_raw_byte())
            if raw_count:
                br.resync_after_raw()

            chunks -= 1
            if not chunks:
                break

            distance = read_huffman(br, distance_table) + 1
            count = read_huffman(br, length_table) + 2
            if distance > len(out):
                raise RNCError("back-reference precedes output start")
            for _ in range(count):
                if len(out) >= h.unpacked_size:
                    raise RNCError("back-reference exceeds declared unpacked size")
                out.append(out[-distance])

    result = bytes(out)
    actual_unpacked_crc = crc16(result)
    if actual_unpacked_crc != h.unpacked_crc:
        raise RNCError(f"unpacked CRC mismatch: {actual_unpacked_crc:04X} != {h.unpacked_crc:04X}")
    return result
