#pragma once

#include <cstdint>

namespace ur::product {

enum class CompletedRunGhostTarget : std::uint8_t {
    Off,
    Previous,
    PersonalBest,
};

}  // namespace ur::product
