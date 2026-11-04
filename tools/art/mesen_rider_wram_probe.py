"""Bounded actual-Mesen SNES work-RAM rider graphics state at held frame edges.

Samples source values only; never presumes the active temp rider state belongs
to P1 or P2, nor that NMI has not already cleared the DMA queue.
"""
from __future__ import annotations
import hashlib

MEM_TYPE = "snesWorkRam"
WORDS = (
    ("selected_rider_orientation_0f77", 0x0F77),
    ("selected_rider_animation_phase_0f83", 0x0F83),
    ("selected_rider_motion_delta_0f69", 0x0F69),
    ("selected_rider_angle_0f49", 0x0F49),
    ("selected_rider_graphics_id_0f97", 0x0F97),
    ("p1_queued_graphics_id_0fe9", 0x0FE9),
    ("p2_queued_graphics_id_0feb", 0x0FEB),
    ("dma_queue_pending_0306", 0x0306),
    ("first_dma_source_bank_15a1", 0x15A1),
    ("first_dma_source_address_1645", 0x1645),
    ("first_dma_vram_destination_16e9", 0x16E9),
)
NAMES = tuple(name for name, _ in WORDS)

def valid_word(reply: object, address: int) -> bytes:
    if (not isinstance(reply, dict) or reply.get("memoryType") != MEM_TYPE
            or reply.get("address") != address or reply.get("length") != 2):
        raise ValueError("Mesen actual WRAM address, size or memory provenance mismatch")
    values = reply.get("bytes")
    if (not isinstance(values, list) or len(values) != 2
            or any(type(v) is not int or not 0 <= v <= 255 for v in values)):
        raise ValueError("actual original WRAM byte pair missing or invalid")
    return bytes(values)

def capture(mesen: object, tick: int) -> dict:
    if type(tick) is not int or not 1 <= tick <= 2500:
        raise ValueError("original bridge tick out of bounded replay")
    before = mesen.tool("run.status")
    if not isinstance(before, dict) or before.get("frame") != tick:
        raise ValueError("Mesen did not reach exact requested original frame")
    fields = {}
    raw = bytearray()
    for name, addr in WORDS:
        pair = valid_word(mesen.tool("cpu.read_memory",
            memoryType=MEM_TYPE, address=addr, length=2), addr)
        raw.extend(pair)
        fields[name] = int.from_bytes(pair, "little")
    after = mesen.tool("run.status")
    if not isinstance(after, dict) or after.get("frame") != tick:
        raise ValueError("Mesen advanced during source rider WRAM capture")
    return {
        "original_bridge_tick": tick,
        "memory_type": MEM_TYPE,
        "source_raw_22_bytes_sha256": hashlib.sha256(raw).hexdigest(),
        "source_unattributed_selected_rider_registers": True,
        "source_dma_queue_may_be_cleared_by_NMI": True,
        "original_specific_CPU_writer_PC_verified": False,
        "original_3D_geometry_camera_or_pose_recovered": False,
        "source_u16_le": fields,
    }

def validate(row: object, tick: int) -> None:
    if (not isinstance(row, dict) or row.get("original_bridge_tick") != tick
            or row.get("memory_type") != MEM_TYPE
            or row.get("source_unattributed_selected_rider_registers") is not True
            or row.get("source_dma_queue_may_be_cleared_by_NMI") is not True
            or row.get("original_specific_CPU_writer_PC_verified") is not False
            or row.get("original_3D_geometry_camera_or_pose_recovered") is not False):
        raise ValueError("original source rider WRAM provenance or claim invalid")
    fields = row.get("source_u16_le")
    if not isinstance(fields, dict) or set(fields) != set(NAMES):
        raise ValueError("missing or unexpected original selected rider WRAM fields")
    if any(type(v) is not int or not 0 <= v <= 65535 for v in fields.values()):
        raise ValueError("original 16-bit WRAM values malformed")
    raw = b"".join(fields[name].to_bytes(2, "little") for name in NAMES)
    if hashlib.sha256(raw).hexdigest() != row.get("source_raw_22_bytes_sha256"):
        raise ValueError("original source WRAM sha256 changed")

# A small, source-justified set of original CPU writes. The bridge's existing
# watch callback includes PC and CPU cycles; a held-frame WRAM read does not.
WATCHED_WRITES = (
    ("dma_pending_0306", 0x0306),
    ("selected_graphics_0f97", 0x0F97),
    ("p1_graphics_0fe9", 0x0FE9),
    ("p2_graphics_0feb", 0x0FEB),
    ("first_dma_bank_15a1", 0x15A1),
    ("first_dma_source_address_1645", 0x1645),
    ("first_dma_vram_destination_16e9", 0x16E9),
)
MAX_EVENTS_AT_ONE_BOUNDARY = 128

def start_watches(mesen: object) -> dict:
    result = {}
    for name, address in WATCHED_WRITES:
        reply = mesen.tool("watch.create", memoryType=MEM_TYPE,
                           address=address, length=2, access="write", cpuType="snes")
        handle = reply.get("handle") if isinstance(reply, dict) else None
        if not isinstance(handle, str) or not handle or handle in result:
            raise ValueError("Mesen source writer callback handle invalid")
        result[handle] = {"label": name, "address": address}
    return result

def recent_writes(mesen: object, handles: dict, tick: int) -> dict:
    if not handles or type(tick) is not int or tick < 1:
        raise ValueError("bounded writer watches required")
    reply = mesen.tool("watch.list")
    events = reply.get("events") if isinstance(reply, dict) else None
    if not isinstance(events, list):
        raise ValueError("Mesen source writer callback events absent")
    selected = []
    for event in events:
        if not isinstance(event, dict) or event.get("handle") not in handles:
            continue
        frame = event.get("frame")
        if type(frame) is not int or not tick-1 <= frame <= tick:
            continue
        address = event.get("address")
        if type(address) is not int or not handles[event["handle"]]["address"] <= address <= handles[event["handle"]]["address"] + 1:
            raise ValueError("original writer event address differs from watched WRAM word")
        value = event.get("value")
        if type(value) is not int or not 0 <= value <= 255:
            raise ValueError("original writer callback byte invalid")
        pc = event.get("pcDisplay")
        if pc is not None and (not isinstance(pc, str) or len(pc) > 32):
            raise ValueError("original Mesen CPU PC record malformed")
        selected.append({
            "watched_source_word": handles[event["handle"]]["label"],
            "source_byte_address": address, "byte_written": value,
            "bridge_callback_frame": frame, "source_CPU_PC": pc,
            "source_CPU_master_clock": event.get("masterClock"),
            "source_CPU_cycle_count": event.get("cpuCycleCount"),
        })
    if len(selected) > MAX_EVENTS_AT_ONE_BOUNDARY:
        raise ValueError("source writer activity exceeds bounded event evidence")
    return {
        "original_bridge_capture_tick": tick,
        "watch_event_buffer_retention_may_drop_earlier_events": True,
        "callback_frame_to_held_PPU_snapshot_phase_independently_aligned": False,
        "events": selected,
    }

def validate_recent_writes(row: object, tick: int) -> None:
    if not isinstance(row, dict) or row.get("original_bridge_capture_tick") != tick:
        raise ValueError("source writer callback tick identity differs")
    if (row.get("watch_event_buffer_retention_may_drop_earlier_events") is not True
            or row.get("callback_frame_to_held_PPU_snapshot_phase_independently_aligned") is not False):
        raise ValueError("source callback cannot claim exact PPU phase alignment")
    events = row.get("events")
    if not isinstance(events, list) or len(events) > MAX_EVENTS_AT_ONE_BOUNDARY:
        raise ValueError("unbounded source writer event list")
    legitimate = dict(WATCHED_WRITES)
    for event in events:
        if not isinstance(event, dict) or event.get("watched_source_word") not in legitimate:
            raise ValueError("source writer callback identity unsupported")
        addr = event.get("source_byte_address")
        origin = legitimate[event["watched_source_word"]]
        if type(addr) is not int or addr not in (origin, origin + 1):
            raise ValueError("source callback byte address unsupported")
        val = event.get("byte_written")
        frame = event.get("bridge_callback_frame")
        if type(val) is not int or not 0 <= val <= 255 or type(frame) is not int or not tick-1 <= frame <= tick:
            raise ValueError("source callback byte/frame invalid")
        pc = event.get("source_CPU_PC")
        if pc is not None and (not isinstance(pc, str) or len(pc) > 32):
            raise ValueError("source callback program counter invalid")
