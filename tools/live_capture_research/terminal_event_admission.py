"""ROM-free admission pilot: bound the captured audio tail to a distinct race exit clock.

An observed host race-exit event is required; no host tap, encoder or MP4 is supplied.
"""
from capture_clock_admission import ClockBoundWitness

class TerminalEventWitness(ClockBoundWitness):
    def finish_terminal_bound(self, *, terminal_event_pts_ns, independent_terminal_event,
                              tolerance_ns=5_000_000, **kwargs):
        if (independent_terminal_event is not True or
                type(terminal_event_pts_ns) is not int or
                type(tolerance_ns) is not int or not 0 <= tolerance_ns <= 100_000_000 or
                self.first_pts_ns is None or terminal_event_pts_ns <= self.last_pts_ns):
            raise ValueError('unqualified terminal presentation event')
        # Exact rational arithmetic, no float drift. Capture spans from first PTS
        # through the end of all submitted 48-kHz PCM samples.
        duration_ns_times_hz = (terminal_event_pts_ns - self.first_pts_ns) * 48_000
        captured_ns_times_hz = self.next_audio_sample * 1_000_000_000
        if abs(duration_ns_times_hz - captured_ns_times_hz) > tolerance_ns * 48_000:
            raise ValueError('audio tail not aligned with independent terminal event')
        result = self.finish_device_bound(**kwargs)
        result['independent_terminal_event_matched'] = True
        return result
