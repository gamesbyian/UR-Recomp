#pragma once

#include "host_profile_state.hpp"

#include <array>
#include <cstddef>
#include <cstdint>

namespace ur::product {

// Exact stock clean SRAM image used only to initialize a brand-new Modern
// profile. Progression remains guest-owned after this one-time seed.
const std::array<std::uint8_t, kStockSramBytes>& clean_stock_sram() noexcept;

// Number of leading bytes the stock cold-boot check compares. 80:8C4E compares
// SRAM 0x0000..0x000B (six words) with ROM 83:8000 ("ASJIver3.30" + 0xFF) and
// reformats the whole cartridge on any mismatch; it validates no checksum.
constexpr std::size_t kStockSramFormatSignatureBytes = 12;

// True when an exact 8 KiB image carries the stock format signature, i.e. the
// stock boot would keep it rather than reformat it. A host install that
// bypasses the guest boot (profile activation/rollback writing g_sram live)
// must not admit an image the stock boot would have reformatted. This is the
// guest's own acceptance predicate, not a host reinterpretation of progress.
bool stock_sram_format_signature_present(
    const std::uint8_t* data, std::size_t size) noexcept;

}  // namespace ur::product
