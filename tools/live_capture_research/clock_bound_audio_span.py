"""H25 first-party 48-kHz PCM / presentation-time span admission pilot.

Adapted from Agent4 H25 'h25/live_capture_clock.py' to the existing merged
'ByteSpanWitness'. Checks that contiguous supplied audio samples cover each
successive frame interval *and* the final frame-to-terminal interval. This
is synthetic host-tap evidence only: no independent device clock, renderer,
encoder, playback, hardware or release acceptance is established.
"""
from live_audio_span_witness import ByteSpanWitness


class ClockBoundWitness(ByteSpanWitness):
    def __post_init__(self):
        super().__post_init__()
        self._pending_audio = None
        self._pending_pts = None
        # Current main's ByteSpanWitness is unsealed; use a local one-shot guard.
        self._clock_sealed = False

    @staticmethod
    def _samples(duration_ns):
        if type(duration_ns) is not int or duration_ns <= 0:
            raise ValueError('invalid frame/audio duration')
        return (duration_ns * 48000 + 500_000_000) // 1_000_000_000

    def add(self, *, attempt, frame_number, pts_ns, bgra, audio_first_sample, pcm_s16le):
        if self._clock_sealed:
            raise ValueError('finalized witness cannot admit another frame')
        if self._pending_pts is not None:
            expected = self._samples(pts_ns - self._pending_pts)
            if abs(self._pending_audio - expected) > 1:
                self.incomplete_reason = 'audio span does not match presentation interval'
                raise ValueError(self.incomplete_reason)
        # The existing ByteSpanWitness rejects wrong attempt, frame, raw bytes,
        # PCM alignment, PTS ordering and discontinuous sample offsets.
        super().add(attempt=attempt, frame_number=frame_number, pts_ns=pts_ns,
                    bgra=bgra, audio_first_sample=audio_first_sample, pcm_s16le=pcm_s16le)
        self._pending_audio = len(pcm_s16le) // 4
        self._pending_pts = pts_ns

    def finish(self, *, attempt, profile, terminal_frame, terminal_pts_ns):
        if self._clock_sealed:
            raise ValueError('finalized witness cannot issue another receipt')
        if self.frame_count < 2 or type(terminal_pts_ns) is not int:
            raise ValueError('insufficient timestamped frames to validate audio clock')
        expected = self._samples(terminal_pts_ns - self._pending_pts)
        if abs(self._pending_audio - expected) > 1:
            self.incomplete_reason = 'terminal audio span does not match presentation interval'
            raise ValueError(self.incomplete_reason)
        receipt = super().finish(attempt=attempt, profile=profile,
                                 terminal_frame=terminal_frame)
        self._clock_sealed = True
        receipt['terminal_pts_ns'] = terminal_pts_ns
        receipt['clock_checked_against_48k_samples'] = True
        receipt['encoded_video_verified'] = False
        receipt['independent_device_clock_observed'] = False
        receipt['release_gate_credit'] = 0
        return receipt
