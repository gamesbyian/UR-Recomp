# Modern Continue Tour conversation transcript

Captured: 2026-10-05

Source: project conversation **Add Modern Continue Route**.

The user assigned a Windows x64-only lane for real resumable Modern progression per profile. Existing profile identity, isolated SRAM and host persistence were to remain authoritative; the task was specifically to preserve useful tour/event continuation despite the stock rider-select path clearing transient tour flags.

The implementation became PR #487, **Add profile-safe Modern Continue Tour route**. It added a profile-safe Continue path from Modern main into stock TRACK_SELECT, reapplied the retained tour continuation at the correct seam, kept Authentic behavior unchanged and added fresh-process acceptance that proves a resumable profile restores the expected tour row/flags without auto-starting a race.

Follow-on policy work in PR #490 defined Modern Resume Tour / Restart Tour entry semantics, while later challenge-generation work narrowed the remaining progression questions rather than reopening the persistence substrate.
