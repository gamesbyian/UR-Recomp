"""Isolated, ROM-free live capture clock/device admission prototype.

Checks a recorded source-byte witness against presentation time and a separately
observed audio-device cursor. Neither this nor a passing test proves an MP4.
"""
from live_audio_span_witness import ByteSpanWitness

class ClockBoundWitness(ByteSpanWitness):
    def __post_init__(self):
        super().__post_init__()
        self.first_pts_ns = None
        self.tolerance_ns = 5_000_000

    def add(self, *, pts_ns, audio_first_sample, **kwargs):
        # Clock correlation is independent of merely monotonic PTS and PCM bytes.
        if self.first_pts_ns is None:
            first = pts_ns
        else:
            first = self.first_pts_ns
        if (type(pts_ns) is not int or type(audio_first_sample) is not int or
                type(first) is not int or
                abs((pts_ns-first)*48_000 - audio_first_sample*1_000_000_000)
                > self.tolerance_ns*48_000):
            self.incomplete_reason = 'presentation/audio clock drift'
            raise ValueError(self.incomplete_reason)
        super().add(pts_ns=pts_ns,audio_first_sample=audio_first_sample,**kwargs)
        if self.first_pts_ns is None:self.first_pts_ns = pts_ns

    def finish_device_bound(self, *, device_entry_cursor, device_end_cursor,
                            independent_device_observation, **kwargs):
        if (independent_device_observation is not True or
                type(device_entry_cursor) is not int or
                type(device_end_cursor) is not int or
                device_entry_cursor < 0 or device_end_cursor < device_entry_cursor or
                device_end_cursor-device_entry_cursor != self.next_audio_sample):
            raise ValueError('independent audio device cursor mismatch')
        receipt=super().finish(**kwargs)
        receipt['independent_device_cursor_matched']=True
        receipt['encoded_video_verified']=False
        return receipt
