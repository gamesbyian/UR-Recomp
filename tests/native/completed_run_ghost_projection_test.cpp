#include "completed_run_ghost_projection.hpp"

#include <array>
#include <cassert>
#include <cstdint>

using namespace ur::product;

namespace {

void write_le16(
    std::array<std::uint8_t, 0x20000>& wram,
    std::size_t offset,
    std::uint16_t value) {
    wram[offset] = static_cast<std::uint8_t>(value & 0xFFu);
    wram[offset + 1] = static_cast<std::uint8_t>(value >> 8);
}

CompletedRunGhostWorldSample sample(std::uint16_t x, std::uint16_t y) {
    return {0, x, y, 0, 0x0541, 1, 0x66};
}

}  // namespace

int main() {
    std::array<std::uint8_t, 0x20000> wram{};
    write_le16(wram, 0x03ED, 0);
    write_le16(wram, 0x0419, 1000);
    write_le16(wram, 0x041D, 800);
    write_le16(wram, 0x0421, 0xFFD7); // -41
    write_le16(wram, 0x0423, 0x00E1); // 225
    write_le16(wram, 0x0D49, 0x00FF);
    wram[0x0DDB] = 0;

    const auto context =
        read_completed_run_ghost_projection_context(
            wram.data(), wram.size());
    assert(context);
    assert(context->camera_x == 1000);
    assert(context->camera_y == 800);

    const auto center =
        project_completed_run_ghost_sample(sample(1088, 859), *context);
    assert(center);
    assert(center->screen_x == 88);
    assert(center->screen_y == 59);
    assert(!center->oam_x_high);

    const auto left =
        project_completed_run_ghost_sample(sample(990, 790), *context);
    assert(left);
    assert(left->screen_x == -10);
    assert(left->screen_y == -10);
    assert(left->oam_x_high);

    assert(!project_completed_run_ghost_sample(
        sample(958, 800), *context)); // x = -42, left of bound
    assert(!project_completed_run_ghost_sample(
        sample(1000, 758), *context)); // y = -42
    assert(!project_completed_run_ghost_sample(
        sample(1000, 1025), *context)); // y = 225

    // The stock routine scales only for horizontal culling; screen X still
    // comes from the unscaled raw delta.
    auto scaled = *context;
    scaled.horizontal_scale_shifts = 1;
    scaled.horizontal_lower_bound = 0;
    scaled.horizontal_upper_bound = 101;
    const auto scaled_visible =
        project_completed_run_ghost_sample(sample(1050, 800), scaled);
    assert(scaled_visible && scaled_visible->screen_x == 50);
    scaled.horizontal_upper_bound = 100;
    assert(!project_completed_run_ghost_sample(
        sample(1050, 800), scaled));

    wram[0x0DDB] = 1;
    assert(!read_completed_run_ghost_projection_context(
        wram.data(), wram.size()));

    wram[0x0DDB] = 0;
    write_le16(wram, 0x03ED, 16);
    assert(!read_completed_run_ghost_projection_context(
        wram.data(), wram.size()));

    return 0;
}
