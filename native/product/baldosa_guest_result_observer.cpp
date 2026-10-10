#include "baldosa_guest_result_observer.hpp"

namespace ur::product {

void BaldosaGuestResultObserver::reset() noexcept {
    players_ = 0;
    saw_race_ = false;
    emitted_ = false;
    first_race_frame_ = 0;
    race_course_index_ = 0;
    previous_line_ = {};
    p1_finish_ticks60_.reset();
    resolved_inputs_.reset();
    captured_input_frames_ = 0;
}

std::optional<BaldosaSettledResult> BaldosaGuestResultObserver::observe(
    unsigned players, const std::uint8_t* wram, std::size_t wram_size,
    const std::uint8_t* sram, std::size_t sram_size,
    std::uint64_t host_frame,
    std::uint32_t mapped_controller_word) {
    // A real stock-menu handoff and full guest memory are mandatory. A
    // preloaded result screen or scripted bare guest startup cannot mint one.
    if ((players != 1u && players != 2u) || !wram ||
        wram_size < 0x20000u || !sram || sram_size < 8192u) {
        reset();
        return std::nullopt;
    }
    if (players_ != players) {
        reset();
        players_ = players;
    }

    const bool active = wram[0x0313u] == 0x01u;
    const std::uint8_t menu = wram[0x009fu];
    if (active) {
        if (!saw_race_ || emitted_) {
            saw_race_ = true;
            emitted_ = false;
            first_race_frame_ = host_frame;
            const auto course = ur_uniracers_identify_course(
                wram + 0x10000u, 0x10000u);
            const int tour_slot = course.valid
                ? (course.course_index - 1) % 5 + 1 : 0;
            race_course_index_ = (tour_slot == 1 || tour_slot == 4)
                ? course.course_index : 0;
            p1_finish_ticks60_.reset();
            resolved_inputs_.reset();
            captured_input_frames_ = 0;
            previous_line_ = ur_uniracers_read_line_snapshot(
                wram, wram_size, 0);
            return std::nullopt;
        }
        resolved_inputs_.observe_input_frame(
            captured_input_frames_++,
            static_cast<std::uint16_t>(mapped_controller_word & 0x0fffu),
            static_cast<std::uint16_t>((mapped_controller_word >> 12) & 0x0fffu));
        if (players == 1u && !p1_finish_ticks60_) {
            const auto line = ur_uniracers_read_line_snapshot(
                wram, wram_size, 0);
            const bool newly_written = !ur_uniracers_line_snapshot_equal(
                previous_line_, line);
            previous_line_ = line;
            if (newly_written && line.valid &&
                ur_uniracers_read_laps_remaining(wram, wram_size, 0) == 0) {
                const auto ticks = ur_uniracers_line_snapshot_ticks60(
                    ur_uniracers_read_run_data(wram, wram_size), line);
                if (ticks > 0)
                    p1_finish_ticks60_ = static_cast<std::uint64_t>(ticks);
            }
        }
        return std::nullopt;
    }

    if (!saw_race_ || emitted_ || race_course_index_ == 0)
        return std::nullopt;
    // Actual guest frames after entry, including the transitional frame:
    // this is the shipping Modern input timeline, not host-only pause pumps.
    resolved_inputs_.observe_input_frame(
        captured_input_frames_++,
        static_cast<std::uint16_t>(mapped_controller_word & 0x0fffu),
        static_cast<std::uint16_t>((mapped_controller_word >> 12) & 0x0fffu));
    if (players == 1u && menu == 0x99u && p1_finish_ticks60_) {
        emitted_ = true;
        return BaldosaSettledResult{
            BaldosaSettledResultKind::TimedOnePlayerRace,
            first_race_frame_, host_frame, *p1_finish_ticks60_,
            race_course_index_, std::nullopt,
            captured_input_frames_, resolved_inputs_.inputs(),
        };
    }
    if (players == 2u &&
        menu == ur::title::kOrdinaryTwoPlayerRaceResultMenu) {
        auto result = ur::title::observe_ordinary_two_player_race_result(
            true, wram, wram_size, sram, sram_size);
        if (result) {
            emitted_ = true;
            return BaldosaSettledResult{
                BaldosaSettledResultKind::OrdinaryTwoPlayerRace,
                first_race_frame_, host_frame, 0u,
                race_course_index_, result,
                captured_input_frames_, resolved_inputs_.inputs(),
            };
        }
    }
    // Interstitial phases are not terminal results. The stock 2P result
    // surface can also precede settled result words in SRAM: keep waiting.
    return std::nullopt;
}

} // namespace ur::product
