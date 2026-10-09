#pragma once

#include "modern_host_input_release_latch.hpp"

#include <cstdint>

namespace ur::product {

// Two independent 12-button seats, with the framework's high presence bits
// passed through unchanged. Input is already mapped by the owning host.
// Never feed raw SDL controls or scripted/debug masks to host navigation.
class BaldosaGuestInputAuthority {
public:
    void host_focus(bool owned) noexcept {
        if (host_owns_ == owned) return;
        host_owns_ = owned;
        // A paused host may receive NO filter_frame_inputs samples. Force a
        // complete physical release observation before resuming any button.
        for (auto& latch : latches_) latch.held = 0x0fffu;
    }

    bool host_owns_input() const noexcept { return host_owns_; }

    std::uint32_t filter(std::uint32_t word) noexcept {
        constexpr std::uint32_t buttons = 0x0fffu;
        std::uint32_t result = word & ~0x00ffffffu;
        for (unsigned seat = 0; seat < 2; ++seat) {
            const auto shift = seat * 12;
            const auto in = (word >> shift) & buttons;
            auto filtered = modern_host_input_filter(latches_[seat],
                                                      host_owns_, in);
            latches_[seat] = filtered.latch;
            result |= (filtered.inputs & buttons) << shift;
        }
        return result;
    }

    void reset() noexcept {
        host_owns_ = false;
        // A reset/restart may leave a physical Start/Return held.
        for (auto& latch : latches_) latch.held = 0x0fffu;
    }

private:
    bool host_owns_ = false;
    ModernHostInputReleaseLatch latches_[2]{};
};

enum class BaldosaBackendPhase : std::uint8_t {
    Cold, Ready, Running, Paused, Frontend, Finished
};

enum class BaldosaBackendStatus : std::uint8_t {
    Applied, MissingHook, InvalidPhase, Rejected
};

// Deliberately no input source, SRAM or record-writing API. The Modern host
// retains those authorities. An operation succeeds only after the real native
// host acknowledges it. An unconnected hook is never a simulated success.
struct BaldosaBackendHooks {
    void* context = nullptr;
    bool (*launch_event)(void* context, unsigned players) = nullptr;
    bool (*set_paused)(void* context, bool paused) = nullptr;
    bool (*restart_event)(void* context) = nullptr;
    bool (*exit_to_frontend)(void* context) = nullptr;
    // True only for the actual game's settled result condition. Never
    // infer a completion from elapsed frames or a requested exit.
    bool (*has_settled_result)(void* context) = nullptr;
};

class BaldosaExecutionBackend {
public:
    explicit BaldosaExecutionBackend(BaldosaBackendHooks hooks = {}) noexcept
        : hooks_(hooks) {}

    BaldosaBackendPhase phase() const noexcept { return phase_; }
    unsigned players() const noexcept { return players_; }
    std::uint64_t observed_guest_frames() const noexcept { return frames_; }
    BaldosaGuestInputAuthority& input() noexcept { return input_; }

    BaldosaBackendStatus initialize() noexcept {
        if (phase_ != BaldosaBackendPhase::Cold)
            return BaldosaBackendStatus::InvalidPhase;
        phase_ = BaldosaBackendPhase::Ready;
        return BaldosaBackendStatus::Applied;
    }

    BaldosaBackendStatus select_players(unsigned players) noexcept {
        if (phase_ != BaldosaBackendPhase::Ready &&
            phase_ != BaldosaBackendPhase::Frontend)
            return BaldosaBackendStatus::InvalidPhase;
        if (players != 1 && players != 2)
            return BaldosaBackendStatus::Rejected;
        players_ = players;
        return BaldosaBackendStatus::Applied;
    }

    BaldosaBackendStatus start_event() noexcept {
        if (players_ == 0 || (phase_ != BaldosaBackendPhase::Ready &&
                             phase_ != BaldosaBackendPhase::Frontend))
            return BaldosaBackendStatus::InvalidPhase;
        if (!hooks_.launch_event) return BaldosaBackendStatus::MissingHook;
        if (!hooks_.launch_event(hooks_.context, players_))
            return BaldosaBackendStatus::Rejected;
        input_.reset();
        frames_ = 0;
        phase_ = BaldosaBackendPhase::Running;
        return BaldosaBackendStatus::Applied;
    }

    void observe_guest_frame() noexcept {
        if (phase_ == BaldosaBackendPhase::Running) ++frames_;
    }

    BaldosaBackendStatus pause() noexcept {
        if (phase_ != BaldosaBackendPhase::Running)
            return BaldosaBackendStatus::InvalidPhase;
        if (!hooks_.set_paused) return BaldosaBackendStatus::MissingHook;
        if (!hooks_.set_paused(hooks_.context, true))
            return BaldosaBackendStatus::Rejected;
        input_.host_focus(true);
        phase_ = BaldosaBackendPhase::Paused;
        return BaldosaBackendStatus::Applied;
    }

    BaldosaBackendStatus resume() noexcept {
        if (phase_ != BaldosaBackendPhase::Paused)
            return BaldosaBackendStatus::InvalidPhase;
        if (!hooks_.set_paused) return BaldosaBackendStatus::MissingHook;
        if (!hooks_.set_paused(hooks_.context, false))
            return BaldosaBackendStatus::Rejected;
        input_.host_focus(false);
        phase_ = BaldosaBackendPhase::Running;
        return BaldosaBackendStatus::Applied;
    }

    BaldosaBackendStatus restart() noexcept {
        if (phase_ != BaldosaBackendPhase::Running)
            return BaldosaBackendStatus::InvalidPhase;
        if (!hooks_.restart_event) return BaldosaBackendStatus::MissingHook;
        if (!hooks_.restart_event(hooks_.context))
            return BaldosaBackendStatus::Rejected;
        input_.reset();
        frames_ = 0;
        return BaldosaBackendStatus::Applied;
    }

    BaldosaBackendStatus finish_from_guest_result() noexcept {
        if (phase_ != BaldosaBackendPhase::Running)
            return BaldosaBackendStatus::InvalidPhase;
        if (!hooks_.has_settled_result)
            return BaldosaBackendStatus::MissingHook;
        if (!hooks_.has_settled_result(hooks_.context))
            return BaldosaBackendStatus::Rejected;
        // A true guest result may now be read by the existing Modern
        // Records capture. We still never manufacture .urrun or a receipt.
        phase_ = BaldosaBackendPhase::Finished;
        input_.host_focus(true);
        return BaldosaBackendStatus::Applied;
    }

    BaldosaBackendStatus exit_to_frontend() noexcept {
        if (phase_ != BaldosaBackendPhase::Running &&
            phase_ != BaldosaBackendPhase::Paused &&
            phase_ != BaldosaBackendPhase::Finished)
            return BaldosaBackendStatus::InvalidPhase;
        if (!hooks_.exit_to_frontend) return BaldosaBackendStatus::MissingHook;
        if (!hooks_.exit_to_frontend(hooks_.context))
            return BaldosaBackendStatus::Rejected;
        input_.host_focus(true);
        phase_ = BaldosaBackendPhase::Frontend;
        return BaldosaBackendStatus::Applied;
    }

private:
    BaldosaBackendHooks hooks_{};
    BaldosaGuestInputAuthority input_{};
    BaldosaBackendPhase phase_ = BaldosaBackendPhase::Cold;
    unsigned players_ = 0;
    std::uint64_t frames_ = 0;
};

} // namespace ur::product
