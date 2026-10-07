#include "reduced_flashing_frame_blend.hpp"

#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>

using namespace ur::product;

namespace {

constexpr int kWidth = 4;
constexpr int kHeight = 2;
constexpr std::size_t kRowBytes = kWidth * 4u;
constexpr std::size_t kPitch = kRowBytes + 8u;
constexpr std::size_t kBytes = kPitch * kHeight;

void fill_pixels(std::array<std::uint8_t, kBytes>& frame, std::uint8_t value) {
    frame.fill(0xCCu);
    for (int y = 0; y < kHeight; ++y) {
        for (std::size_t x = 0; x < kRowBytes; ++x) {
            frame[static_cast<std::size_t>(y) * kPitch + x] = value;
        }
    }
}

void expect_pixels(
    const std::array<std::uint8_t, kBytes>& frame,
    std::uint8_t value) {
    for (int y = 0; y < kHeight; ++y) {
        for (std::size_t x = 0; x < kRowBytes; ++x) {
            assert(frame[static_cast<std::size_t>(y) * kPitch + x] == value);
        }
        for (std::size_t x = kRowBytes; x < kPitch; ++x) {
            assert(frame[static_cast<std::size_t>(y) * kPitch + x] == 0xCCu);
        }
    }
}

}  // namespace

int main() {
    ReducedFlashingFrameBlend blend;
    std::array<std::uint8_t, kBytes> frame{};

    fill_pixels(frame, 0x00u);
    assert(!blend.apply(
        frame.data(), kWidth, kHeight, kPitch, true));
    assert(blend.has_reference());
    expect_pixels(frame, 0x00u);

    // Floor mean matches the established recomp-ui semantics: 0 + 255 -> 127.
    fill_pixels(frame, 0xFFu);
    assert(blend.apply(
        frame.data(), kWidth, kHeight, kPitch, true));
    expect_pixels(frame, 0x7Fu);

    // The retained reference is the unblended 0xFF frame.
    fill_pixels(frame, 0xFFu);
    assert(blend.apply(
        frame.data(), kWidth, kHeight, kPitch, true));
    expect_pixels(frame, 0xFFu);

    // Holding presents blend against the same reference without advancing it.
    fill_pixels(frame, 0x00u);
    assert(blend.apply(
        frame.data(), kWidth, kHeight, kPitch, false));
    expect_pixels(frame, 0x7Fu);
    fill_pixels(frame, 0x00u);
    assert(blend.apply(
        frame.data(), kWidth, kHeight, kPitch, false));
    expect_pixels(frame, 0x7Fu);

    // A normal present advances the reference.
    fill_pixels(frame, 0x00u);
    assert(blend.apply(
        frame.data(), kWidth, kHeight, kPitch, true));
    expect_pixels(frame, 0x7Fu);
    fill_pixels(frame, 0x00u);
    assert(blend.apply(
        frame.data(), kWidth, kHeight, kPitch, false));
    expect_pixels(frame, 0x00u);

    // Reset prevents blending across a scene cut.
    blend.reset();
    fill_pixels(frame, 0xFFu);
    assert(!blend.apply(
        frame.data(), kWidth, kHeight, kPitch, false));
    expect_pixels(frame, 0xFFu);
    fill_pixels(frame, 0x00u);
    assert(!blend.apply(
        frame.data(), kWidth, kHeight, kPitch, true));
    expect_pixels(frame, 0x00u);

    // Geometry change automatically drops the stale reference.
    std::array<std::uint8_t, 8u * 4u> resized{};
    resized.fill(0xFFu);
    assert(!blend.apply(resized.data(), 8, 1, 8u * 4u, true));
    assert(blend.width() == 8);
    assert(blend.height() == 1);

    // Invalid surfaces fail closed and do not claim a blend.
    assert(!blend.apply(nullptr, 8, 1, 8u * 4u, true));
    assert(!blend.apply(resized.data(), 0, 1, 8u * 4u, true));
    assert(!blend.apply(resized.data(), 8, 1, 8u * 4u - 1u, true));

    return 0;
}
