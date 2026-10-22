"""ROM-free, not-shipping audio continuity and frame-PTS pilot.

Captures *actual bytes supplied by a host tap*, never reconstructed replay.
No claim about hardware, encoder, presentation, or playback success.
"""
from dataclasses import dataclass, field
import hashlib

@dataclass
class ByteSpanWitness:
    attempt: str
    profile: str
    width: int
    height: int
    entry_frame: int
    next_frame: int = field(init=False)
    next_audio_sample: int = 0
    last_pts_ns: int = -1
    frame_hash: object = field(default_factory=hashlib.sha256, repr=False)
    audio_hash: object = field(default_factory=hashlib.sha256, repr=False)
    frame_count: int = 0
    audio_sample_count: int = 0
    incomplete_reason: str = ''

    def __post_init__(self):
        if (type(self.attempt) is not str or not self.attempt or
                type(self.profile) is not str or not self.profile or
                type(self.width) is not int or not 0 < self.width <= 4096 or
                type(self.height) is not int or not 0 < self.height <= 4096 or
                type(self.entry_frame) is not int or self.entry_frame < 0):
            raise ValueError('invalid capture identity/geometry')
        self.next_frame = self.entry_frame

    def add(self, *, attempt, frame_number, pts_ns, bgra, audio_first_sample, pcm_s16le):
        if self.incomplete_reason:
            raise ValueError('capture already incomplete')
        reason = None
        if (attempt != self.attempt or type(frame_number) is not int or
                frame_number != self.next_frame):
            reason = 'frame/attempt discontinuity'
        elif (type(pts_ns) is not int or pts_ns <= self.last_pts_ns or pts_ns < 0):
            reason = 'nonmonotonic presentation timestamp'
        elif (type(bgra) is not bytes or len(bgra) != self.width*self.height*4):
            reason = 'missing/wrong-sized composed BGRA frame'
        elif (type(audio_first_sample) is not int or
                audio_first_sample != self.next_audio_sample):
            reason = 'audio gap/overlap'
        elif (type(pcm_s16le) is not bytes or not 0 < len(pcm_s16le) <= 384000 or
                len(pcm_s16le) % 4):
            reason = 'missing/unaligned 48k stereo PCM span'
        if reason:
            self.incomplete_reason = reason
            raise ValueError(reason)
        self.frame_hash.update(bgra)
        self.audio_hash.update(pcm_s16le)
        self.last_pts_ns=pts_ns
        self.next_frame+=1
        self.next_audio_sample+=len(pcm_s16le)//4
        self.frame_count+=1
        self.audio_sample_count+=len(pcm_s16le)//4

    def finish(self, *, attempt, profile, terminal_frame):
        if (self.incomplete_reason or attempt!=self.attempt or profile!=self.profile or
                type(terminal_frame) is not int or
                self.frame_count == 0 or terminal_frame != self.next_frame-1):
            raise ValueError('no complete attempt-bound audiovisual witness')
        return {'attempt':self.attempt, 'profile':self.profile,
                'first_frame':self.entry_frame,'last_frame':terminal_frame,
                'frames':self.frame_count,'audio_samples_48k_stereo':self.audio_sample_count,
                'composed_bgra_sha256':self.frame_hash.hexdigest(),
                'mixed_pcm_sha256':self.audio_hash.hexdigest(),
                'recorded_bytes_only':True,'encoded_video_verified':False}
