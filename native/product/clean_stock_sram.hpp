#pragma once

#include "host_profile_state.hpp"

#include <array>
#include <cstdint>

namespace ur::product {

// Exact stock clean SRAM image used only to initialize a brand-new Modern
// profile. Progression remains guest-owned after this one-time seed.
const std::array<std::uint8_t, kStockSramBytes>& clean_stock_sram() noexcept;

}  // namespace ur::product
