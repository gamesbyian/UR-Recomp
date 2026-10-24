#!/usr/bin/env python3
"""Bounded live-frame/audio byte witness for a future Save/Discard recorder.

ROM-free proof of observed byte continuity, not an encoder, GPU capture,
media decode, Windows audio device or durable publication. Never reconstructs
video from .urrun; the authoritative game record is independent.
"""
import hashlib
import unicodedata
from qa07_live_capture_eligibility import LiveCapture, State


def _safe_identity(value):
    # Verify the byte identity before handing it to the capture state.
    # Surrogates and other unencodable text must fail as invalid input,
    # rather than leaking UnicodeEncodeError out of the public API.
    if (type(value) is not str or not value.strip() or
            unicodedata.normalize('NFC', value) != value):
        return False
    try:
        encoded = value.encode('utf-8', 'strict')
    except UnicodeEncodeError:
        return False
    return (len(encoded) <= 128 and
            not any(unicodedata.category(ch) in ('Cc', 'Cf') for ch in value))


class LiveMediaWitness:
    def __init__(self, *, width, height, audio_samples_per_frame=800):
        if (any(type(v) is not int for v in (width,height,audio_samples_per_frame)) or
                not 1 <= width <= 8192 or not 1 <= height <= 8192 or
                not 1 <= audio_samples_per_frame <= 96000):
            raise ValueError('invalid capture geometry or PCM contract')
        self.width=width;self.height=height
        self.audio_samples_per_frame=audio_samples_per_frame
        self.frames=0
        self.video_digest=hashlib.sha256()
        self.audio_digest=hashlib.sha256()
        self.capture=LiveCapture()

    def start(self, *, attempt, profile, race_entry_frame, capture_start_frame):
        if not _safe_identity(attempt) or not _safe_identity(profile):
            raise ValueError('invalid live attempt/profile identity')
        self.capture.start(attempt=attempt,profile=profile,
                           race_entry_frame=race_entry_frame,
                           capture_start_frame=capture_start_frame)

    def append(self, *, attempt, frame_number, bgra, pcm_stereo_s16):
        if self.capture.state != State.RECORDING:
            raise ValueError('not actively recording')
        frame_ok = type(bgra) is bytes and len(bgra)==self.width*self.height*4
        audio_ok = (type(pcm_stereo_s16) is bytes and
                    len(pcm_stereo_s16)==self.audio_samples_per_frame*4)
        self.capture.frame(attempt=attempt,frame_number=frame_number,
                           composed_frame_present=frame_ok,
                           audio_span_complete=audio_ok)
        if self.capture.state != State.RECORDING:
            return
        self.video_digest.update(bgra)
        self.audio_digest.update(pcm_stereo_s16)
        self.frames+=1

    def finish(self, *, attempt, profile, terminal_frame):
        self.capture.finish(attempt=attempt,profile=profile,terminal_frame=terminal_frame)
        if self.capture.state != State.READY:
            raise ValueError('incomplete live audiovisual span')
        return {'schema':'ur-live-av-byte-witness/1',
                'attempt':self.capture.attempt,'profile':self.capture.profile,
                'entry_frame':self.capture.entry_frame,
                'terminal_frame':self.capture.terminal_frame,
                'frames':self.frames,'width':self.width,'height':self.height,
                'pcm_samples_per_frame':self.audio_samples_per_frame,
                'bgra_sha256':self.video_digest.hexdigest(),
                'pcm_sha256':self.audio_digest.hexdigest(),
                'encoded_video_verified':False,
                'physical_capture_accepted':False,'release_gate_credit':0}
