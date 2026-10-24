"""ROM-free optional independent source-presentation clock witness.

The existing byte/frame identity chain can be self-consistent even when a host
capture tap timestamps the frames differently from their independent source
presentation events. This class requires both clocks for every admitted frame.
It does not attest to a real GPU present, an encoder, or an MP4.
"""
from presented_frame_admission import PresentedFrameWitness

class SourceClockPresentedWitness(PresentedFrameWitness):
    def __post_init__(self):
        super().__post_init__()
        self.independent_source_clock_count = 0
        self.last_independent_source_pts_ns = -1

    def add_clock_bound_source_frame(self, *, independent_source_pts_ns,
                                     independent_source_present_clock, **kwargs):
        pts = kwargs.get('pts_ns')
        if (independent_source_present_clock is not True or
                type(independent_source_pts_ns) is not int or
                type(pts) is not int or
                independent_source_pts_ns < 0 or
                independent_source_pts_ns <= self.last_independent_source_pts_ns or
                independent_source_pts_ns != pts):
            self.incomplete_reason = 'independent source presentation clock mismatch'
            raise ValueError(self.incomplete_reason)
        super().add_source_frame(**kwargs)
        self.last_independent_source_pts_ns = independent_source_pts_ns
        self.independent_source_clock_count += 1

    def finish_clock_bound(self, **kwargs):
        if (self.independent_source_clock_count == 0 or
                self.independent_source_clock_count != self.frame_count):
            raise ValueError('not all captured frames have independent source clocks')
        result = self.finish_presented_bound(**kwargs)
        result['independent_source_clock_census_matched'] = True
        result['encoded_video_verified'] = False
        return result
