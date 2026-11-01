#!/usr/bin/env python3
"""RF095: fail-closed receipt for *executed* frame-registered stereo PCM.

This is a diagnostic, never a cross-clock resampler, audio-equivalence verdict,
complete USA event, or release gate. The original libretro WAV and native DSP
post-echo raw stream are distinct output stages. The exact original/native
frame-to-sample maps define slices without guessed 534-samples/frame offsets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import tempfile
import wave
from pathlib import Path

ORIGINAL_START, ORIGINAL_END = 6445, 6452
NATIVE_START, NATIVE_END = 6447, 6457
MAX_FRAMES = 30000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as src:
        for chunk in iter(lambda: src.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def frame_map(path: Path, *, start: int, end: int,
              contiguous_from_zero: bool) -> dict[int, int]:
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 750000:
        raise ValueError('RF095 missing, symlinked or unbounded frame map')
    # The producers emit LF-terminated rows. Python splitlines() also accepts
    # VT/FF/ASCII record separators as line breaks, allowing impossible maps.
    # Read raw bytes so universal-newline translation cannot hide bare CR.
    raw_bytes = path.read_bytes()
    # Both pinned C producers emit a final LF (CRLF on translated streams).
    # Accepting a complete-looking last row without it hides truncated maps.
    if not raw_bytes.endswith(b'\n'):
        raise ValueError('RF095 unterminated frame-map row')
    raw = raw_bytes.decode('ascii').replace('\r\n', '\n')
    if '\r' in raw:
        raise ValueError('RF095 malformed frame-map line ending')
    lines = raw.split('\n')
    lines.pop()
    if any(not line for line in lines):
        raise ValueError('RF095 malformed frame-map row')
    if not lines or lines[0] != 'frame,samples':
        raise ValueError('RF095 malformed frame-map header')
    rows: dict[int, int] = {}
    previous_sample = -1
    previous_frame = -1
    for line in lines[1:]:
        fields = line.split(',')
        if (len(fields) != 2 or any(not v.isascii() or not v.isdecimal()
                                    for v in fields)):
            raise ValueError('RF095 malformed frame-map row')
        frame, sample = map(int, fields)
        if ((contiguous_from_zero and frame != previous_frame + 1) or
                (not contiguous_from_zero and frame <= previous_frame) or
                frame > MAX_FRAMES):
            raise ValueError('RF095 duplicate, missing or unordered frame')
        if sample < previous_sample:
            raise ValueError('RF095 sample counter regressed')
        rows[frame] = sample
        previous_frame, previous_sample = frame, sample
        if len(rows) > MAX_FRAMES:
            raise ValueError('RF095 excessive frame map')
    if (start not in rows or end not in rows or
            (contiguous_from_zero and 0 not in rows) or
            any(frame not in rows for frame in range(start, end + 1))):
        raise ValueError('RF095 required event frame boundaries absent')
    if rows[end] <= rows[start]:
        raise ValueError('RF095 empty event PCM window')
    return rows


def sample_stats(raw: bytes) -> dict:
    if not raw or len(raw) % 4:
        raise ValueError('RF095 incomplete stereo int16 PCM')
    count = len(raw) // 4
    squares = [0, 0]
    peaks = [0, 0]
    nonzero = [0, 0]
    for left, right in struct.iter_unpack('<hh', raw):
        for channel, value in enumerate((left, right)):
            squares[channel] += value * value
            peaks[channel] = max(peaks[channel], abs(value))
            nonzero[channel] += bool(value)
    return {'frames': count, 'rms': [round((v / count) ** .5, 6) for v in squares],
            'peak': peaks, 'nonzero_samples': nonzero,
            'sha256': hashlib.sha256(raw).hexdigest()}


def analyze(original_wav: Path, original_map: Path, native_pcm: Path,
            native_map: Path, original_log: Path, native_log: Path,
            *, original_window_out: Path | None = None) -> dict:
    paths = (original_wav, original_map, native_pcm, native_map,
             original_log, native_log)
    if any(not p.is_file() or p.is_symlink() for p in paths):
        raise ValueError('RF095 actual regular non-symlinked source files required')
    # A single original WAV must never masquerade as native PCM input.
    # Device/inode identity also detects hardlinks with different pathnames.
    identities = {(p.stat().st_dev, p.stat().st_ino) for p in paths}
    if len(identities) != len(paths):
        raise ValueError('RF095 source inputs must be distinct physical files')
    for log, side in ((original_log, 'ORIG'), (native_log, 'NATIVE')):
        text = log.read_text(encoding='utf-8', errors='replace')
        if any('QA01RF095' + side + suffix in text
               for suffix in ('_TRUNCATED', '_OPEN_FAILED', '_WRITE_FAILED',
                              '_FRAME_FAILED', '_INCOMPLETE')):
            raise ValueError('RF095 ' + side + ' producer error/truncation')
        # The pinned native boundary hook runs immediately after this APU
        # synchronization. A timeout makes its sample index incomplete even
        # when the frame map and PCM byte counts look self-consistent.
        if (side == 'NATIVE' and
                '[apu] frame-boundary guest-clock sync timed out' in text):
            raise ValueError('RF095 native APU frame-boundary sync timed out')
        # The pinned guest watchdog longjmps out of an unfinished frame,
        # yet RtlRunFrame still increments its frame counter and synchronizes
        # the APU. A plausible PCM/map pair cannot certify that frame.
        if side == 'NATIVE' and '=== WATCHDOG: Frame ' in text:
            raise ValueError('RF095 native watchdog abandoned a guest frame')
    ref = frame_map(original_map, start=ORIGINAL_START,
                    end=ORIGINAL_END, contiguous_from_zero=True)
    nat = frame_map(native_map, start=NATIVE_START,
                    end=NATIVE_END, contiguous_from_zero=False)
    if set(nat) != set(range(NATIVE_START, NATIVE_END + 1)):
        raise ValueError('RF095 native frame-map population must be exact 6447..6457')
    if ref[0] != 0:
        raise ValueError('RF095 original frame-zero callback count must be zero')
    with wave.open(str(original_wav), 'rb') as wav:
        if (wav.getnchannels(), wav.getsampwidth(), wav.getcomptype()) != (2, 2, 'NONE'):
            raise ValueError('RF095 original WAV must be uncompressed stereo int16')
        if wav.getframerate() < 30000 or wav.getframerate() > 48000:
            raise ValueError('RF095 unexpected original libretro sample rate')
        if ref[max(ref)] != wav.getnframes():
            raise ValueError('RF095 original callback count/WAV frame mismatch')
        # A valid observed event slice does not prove the remainder of the
        # WAV exists: wave.getnframes() trusts the header's declared length.
        # Seek to the final declared sample to reject a truncated tail.
        wav.setpos(wav.getnframes() - 1)
        if len(wav.readframes(1)) != 4:
            raise ValueError('RF095 original WAV truncated after observed window')
        # Pinned snesref/frontend.cpp writes a fixed 44-byte PCM WAV header
        # and exactly four bytes per callback stereo frame, no extra chunks.
        # Reject appended bytes that wave.getnframes() silently ignores.
        if original_wav.stat().st_size != 44 + 4 * wav.getnframes():
            raise ValueError('RF095 unexpected original WAV length')
        wav.setpos(ref[ORIGINAL_START])
        original = wav.readframes(ref[ORIGINAL_END] - ref[ORIGINAL_START])
        rate = wav.getframerate()
    if len(original) != (ref[ORIGINAL_END] - ref[ORIGINAL_START]) * 4:
        raise ValueError('RF095 original short WAV slice')
    if native_pcm.stat().st_size != nat[NATIVE_END] * 4:
        raise ValueError('RF095 native raw sample/map length mismatch')
    if nat[NATIVE_START] != 0 or nat[NATIVE_END] > 8192:
        raise ValueError('RF095 native sample capture not bounded to source window')
    with native_pcm.open('rb') as src:
        native = src.read()
    receipt = {
        'schema': 'ur-qa01-rf095-source-registered-pcm/1',
        'claimed_output_stages': 'libretro callback and native post-echo DSP output',
        'producer_identity_independently_verified': False,
        'original': {'guest_frames': [ORIGINAL_START, ORIGINAL_END],
                     'sample_rate': rate, 'wav_sha256': sha256(original_wav),
                     'map_sha256': sha256(original_map),
                     'first_sample_index': ref[ORIGINAL_START],
                     'last_sample_index': ref[ORIGINAL_END],
                     'frame_sample_indices': {str(f): ref[f] for f in range(ORIGINAL_START, ORIGINAL_END+1)},
                     **sample_stats(original)},
        'native': {'guest_frames': [NATIVE_START, NATIVE_END],
                   'sample_rate_nominal': 32040,
                   'raw_sha256': sha256(native_pcm),
                   'map_sha256': sha256(native_map),
                   'frame_sample_indices': {str(f): nat[f] for f in range(NATIVE_START, NATIVE_END+1)},
                   **sample_stats(native)},
        'guest_frame_clock_equivalence_proven': False,
        'audio_output_pipeline_equivalence_proven': False,
        'per_voice_envelope_observed': False,
        'audible_parity_proven': False,
        'complete_usa_event_admitted': False,
        'usa_event_credit': 0,
        'windows_release_gate_credit': 0,
    }
    # Finish every source read/hash and validate receipt serialization before
    # publishing the optional final-named original PCM window. A late source
    # error must never leave an apparently usable orphan window.
    json.dumps(receipt, indent=2, sort_keys=True)
    if original_window_out is not None:
        if original_window_out.exists() or original_window_out.is_symlink():
            raise ValueError('RF095 refusing stale original PCM window')
        original_window_out.parent.mkdir(parents=True, exist_ok=True)
        with original_window_out.open('xb') as output:
            output.write(original)
    return receipt


def validate_output_paths(inputs: tuple[Path, ...], out: Path,
                          original_window_out: Path | None) -> None:
    """Reject aliased or stale outputs before reading or modifying evidence."""
    outputs = (out,) if original_window_out is None else (out, original_window_out)
    source_paths = {path.resolve(strict=False) for path in inputs}
    destination_paths = [path.resolve(strict=False) for path in outputs]
    if (len(set(destination_paths)) != len(destination_paths) or
            any(path in source_paths for path in destination_paths)):
        raise ValueError('RF095 output path aliases input or another output')
    if out.exists() or out.is_symlink():
        raise ValueError('RF095 refusing stale receipt output')


def preflight_receipt_output(out: Path) -> None:
    """Check receipt-directory writeability before publishing original PCM.

    This catches deterministic parent and write failures; it is not a
    two-file atomic transaction or a substitute for validating both outputs.
    """
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix='.rf095-preflight-', dir=out.parent) as probe:
        probe.write(b'RF095 receipt preflight\\n')
        probe.flush()
        os.fsync(probe.fileno())


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('original_wav', 'original_map', 'native_pcm', 'native_map',
                 'original_log', 'native_log'):
        p.add_argument('--' + name.replace('_', '-'), type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--original-window-out', type=Path)
    args = p.parse_args()
    inputs = tuple(getattr(args, name) for name in
                   ('original_wav', 'original_map', 'native_pcm', 'native_map',
                    'original_log', 'native_log'))
    validate_output_paths(inputs, args.out, args.original_window_out)
    preflight_receipt_output(args.out)
    receipt = analyze(*(getattr(args, name) for name in
                        ('original_wav', 'original_map', 'native_pcm', 'native_map',
                         'original_log', 'native_log')),
                      original_window_out=args.original_window_out)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x', encoding='utf-8') as output:
        output.write(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    print('RF095_SOURCE_REGISTERED_PCM PASS '
          f"original={receipt['original']['frames']} "
          f"native={receipt['native']['frames']} "
          'audible_parity=unproven release_credit=0')


if __name__ == '__main__':
    main()
