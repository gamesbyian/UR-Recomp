"""Isolated ROM-free live-frame provenance pilot, not a real host capture tap."""
from entry_exit_admission import EntryExitWitness

class PresentedFrameWitness(EntryExitWitness):
    def __post_init__(self):
        super().__post_init__()
        self.next_presented_id = None
        self.first_presented_id = None
        self.presented_count = 0

    def add_source_frame(self, *, presented_frame_id, independent_present_observation,
                         source_attempt, source_profile, **kwargs):
        if (independent_present_observation is not True or
            type(presented_frame_id) is not int or presented_frame_id < 0 or
            source_attempt != self.attempt or source_profile != self.profile):
            self.incomplete_reason = 'unqualified source-presented frame identity'
            raise ValueError(self.incomplete_reason)
        if self.next_presented_id is not None and presented_frame_id != self.next_presented_id:
            self.incomplete_reason = 'source presentation gap/duplicate'
            raise ValueError(self.incomplete_reason)
        # Do not advance the source cursor on failed frame/PCM admission.
        super().add(**kwargs)
        if self.first_presented_id is None:
            self.first_presented_id = presented_frame_id
        self.next_presented_id = presented_frame_id + 1
        self.presented_count += 1

    def finish_presented_bound(self, *, terminal_presented_frame_id,
                               independent_terminal_presented_id,
                               entry_presented_frame_id,
                               independent_entry_presented_id,
                               exit_attempt, exit_profile, exit_frame,
                               independent_exit_identity, **kwargs):
        if (independent_entry_presented_id is not True or
            type(entry_presented_frame_id) is not int or
            entry_presented_frame_id != self.first_presented_id or
            independent_terminal_presented_id is not True or
            type(terminal_presented_frame_id) is not int or
            self.presented_count == 0 or
            terminal_presented_frame_id != self.next_presented_id-1):
            raise ValueError('unqualified terminal source-presented frame')
        result = self.finish_source_identity_bound(
            exit_attempt=exit_attempt, exit_profile=exit_profile,
            exit_frame=exit_frame, independent_exit_identity=independent_exit_identity,
            **kwargs)
        result['independent_presented_frame_census_matched'] = True
        result['independent_entry_presented_frame_matched'] = True
        result['encoded_video_verified'] = False
        return result
