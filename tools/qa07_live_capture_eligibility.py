"""ROM-free Modern live audiovisual Save/Discard eligibility pilot.

NOT shipping capture. It decides whether an actual captured candidate may be
presented as a complete recording. It never generates or reconstructs frames.
"""
from dataclasses import dataclass
from enum import Enum

class State(Enum):
    IDLE='idle'; RECORDING='recording'; INCOMPLETE='incomplete'
    READY='ready'; SAVED='saved'; DISCARDED='discarded'

@dataclass
class LiveCapture:
    state: State = State.IDLE
    attempt: str = ''
    profile: str = ''
    next_frame: int = 0
    entry_frame: int = -1
    audio_covered_through: int = -1
    terminal_frame: int = -1
    reason: str = ''

    def start(self, *, attempt, profile, race_entry_frame, capture_start_frame):
        if self.state != State.IDLE: raise ValueError('capture already started')
        if (type(attempt) is not str or not attempt or type(profile) is not str or not profile or
                type(race_entry_frame) is not int or race_entry_frame < 0):
            raise ValueError('invalid attempt identity')
        self.attempt, self.profile = attempt, profile
        self.next_frame = race_entry_frame
        self.entry_frame = race_entry_frame
        if type(capture_start_frame) is not int or capture_start_frame != race_entry_frame:
            self.state=State.INCOMPLETE; self.reason='missing race-entry boundary'
        else:
            self.state=State.RECORDING

    def frame(self, *, attempt, frame_number, composed_frame_present, audio_span_complete):
        if self.state != State.RECORDING: raise ValueError('capture is not recording')
        if attempt != self.attempt or type(frame_number) is not int or frame_number != self.next_frame:
            self.state=State.INCOMPLETE; self.reason='frame gap or wrong attempt'; return
        if composed_frame_present is not True or audio_span_complete is not True:
            self.state=State.INCOMPLETE; self.reason='missing composed frame/audio'; return
        self.audio_covered_through=frame_number
        self.next_frame+=1

    def finish(self, *, attempt, profile, terminal_frame):
        if self.state == State.INCOMPLETE:return
        if self.state != State.RECORDING:raise ValueError('capture not recording')
        if (attempt != self.attempt or profile != self.profile or
                type(terminal_frame) is not int or self.next_frame <= self.entry_frame or
                terminal_frame != self.next_frame-1 or
                terminal_frame != self.audio_covered_through):
            self.state=State.INCOMPLETE;self.reason='incomplete terminal span';return
        self.terminal_frame=terminal_frame
        self.state=State.READY

    def decision(self, action, *, attempt, profile, movie_bytes=None, verified=False):
        if self.state != State.READY:raise ValueError('full-race video unavailable')
        if (attempt,profile)!=(self.attempt,self.profile):raise ValueError('stale attempt/profile')
        if action=='discard':
            self.state=State.DISCARDED;return 'Video discarded'
        if action!='save':raise ValueError('unknown decision')
        if type(movie_bytes) is not bytes or not movie_bytes or verified is not True:
            raise ValueError('movie not verified/published')
        self.state=State.SAVED
        return 'Video saved'
