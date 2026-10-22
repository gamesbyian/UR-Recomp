"""ROM-free independent race-entry and race-exit capture admission pilot.

A first captured frame can be late even when all *captured* frame and PCM
spans are contiguous. Require a distinct source-observed entry event, not
just an attempt ID and a terminal event. Does not validate an MP4.
"""
from terminal_event_admission import TerminalEventWitness


class EntryExitWitness(TerminalEventWitness):
    def finish_entry_exit_bound(self, *, entry_event_pts_ns,
                                independent_entry_event,
                                entry_attempt, entry_profile,
                                entry_tolerance_ns=5_000_000,
                                **kwargs):
        if (independent_entry_event is not True or
                type(entry_event_pts_ns) is not int or
                type(entry_tolerance_ns) is not int or
                not 0 <= entry_tolerance_ns <= 100_000_000 or
                entry_attempt != self.attempt or
                entry_profile != self.profile or
                self.first_pts_ns is None or
                entry_event_pts_ns < 0 or
                abs(self.first_pts_ns-entry_event_pts_ns) > entry_tolerance_ns):
            raise ValueError('live capture did not begin at independent race entry')
        receipt = self.finish_terminal_bound(**kwargs)
        receipt['independent_race_entry_matched'] = True
        return receipt

    def finish_source_identity_bound(self, *, exit_attempt, exit_profile,
                                     exit_frame, independent_exit_identity,
                                     **kwargs):
        """Require the independent terminal event to name the same race.

        This is a source-witness schema pilot, not authenticated device or
        encoded-video evidence. It cannot self-award a Records/video gate.
        """
        if (independent_exit_identity is not True or
                type(exit_attempt) is not str or exit_attempt != self.attempt or
                type(exit_profile) is not str or exit_profile != self.profile or
                type(exit_frame) is not int or exit_frame != self.next_frame-1 or
                kwargs.get('terminal_frame') != exit_frame):
            raise ValueError('terminal event belongs to another race identity')
        result = self.finish_entry_exit_bound(**kwargs)
        result['independent_race_exit_identity_matched'] = True
        return result
