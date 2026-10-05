#pragma once
#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace ur::product {

struct LegacyRacerPreset {
    std::uint8_t rider_index;
    std::string_view name;
    std::string_view colour_label;
};

struct HostRacerIdentity {
    std::string name;
    std::uint8_t rider_index = 0;

    bool operator==(const HostRacerIdentity& other) const noexcept {
        return name == other.name && rider_index == other.rider_index;
    }
};

const std::array<LegacyRacerPreset, 16>& legacy_racer_presets() noexcept;
bool valid_racer_name(std::string_view name) noexcept;
bool valid_racer_identity(const HostRacerIdentity& identity) noexcept;
bool stock_forbidden_name_match(std::string_view name) noexcept;
std::optional<HostRacerIdentity> make_legacy_racer_identity(
    std::size_t preset_index) noexcept;

}  // namespace ur::product
