#include "baldosa_native_run_save_feedback.hpp"

#include <cassert>
#include <cstdio>
#include <cstdint>
#include <string>
#include <vector>

using namespace ur::product;

namespace {
std::string label;
unsigned fill_calls = 0;
unsigned border_calls = 0;
int fill_x = -1;
int border_x = -1;
int label_x = -1;
void fill(std::uint32_t*, int, int, int x, int, int, int, std::uint32_t) {
    ++fill_calls;
    fill_x = x;
}
void stroke(std::uint32_t*, int, int, int x, int, int, int, std::uint32_t) {
    ++border_calls;
    border_x = x;
}
void text(std::uint32_t*, int, int, int x, int,
          const char* value, std::uint32_t, int) {
    label = value ? value : "";
    label_x = x;
}
}

int main() {
    std::vector<std::uint32_t> pixels(344u * 224u, 0u);
    const ModernRootOverlayPainter painter{&fill, &stroke, &text};
    assert(!render_baldosa_native_run_save_feedback(
        painter, pixels.data(), 256, 224,
        BaldosaNativeRunSaveFeedback::None));
    assert(label.empty() && fill_calls == 0 && border_calls == 0);
    assert(render_baldosa_native_run_save_feedback(
        painter, pixels.data(), 256, 224,
        BaldosaNativeRunSaveFeedback::Pending));
    assert(label == "RECORD SAVE PENDING");
    assert(fill_calls == 1 && border_calls == 1);
    assert(fill_x == 32 && border_x == 32 && label_x == 45);
    assert(render_baldosa_native_run_save_feedback(
        painter, pixels.data(), 256, 224,
        BaldosaNativeRunSaveFeedback::Saved));
    assert(label == "RECORD SAVED");
    assert(render_baldosa_native_run_save_feedback(
        painter, pixels.data(), 256, 224,
        BaldosaNativeRunSaveFeedback::NotSaved));
    assert(label == "RECORD NOT SAVED");
    // Physical row pitch is independent of the source's visible width.
    // A padded 4:3 row remains centred at 32; a padded 342-wide row
    // moves to 75, without changing the status or guest-owned result.
    assert(render_baldosa_native_run_save_feedback(
        painter, pixels.data(), 344, 224,
        BaldosaNativeRunSaveFeedback::Saved, 256));
    assert(fill_x == 32 && border_x == 32 && label_x == 45);
    assert(render_baldosa_native_run_save_feedback(
        painter, pixels.data(), 344, 224,
        BaldosaNativeRunSaveFeedback::NotSaved, 342));
    assert(fill_x == 75 && border_x == 75 && label_x == 88);
    const auto previous_fill = fill_calls;
    assert(!render_baldosa_native_run_save_feedback(
        painter, pixels.data(), 256, 224,
        BaldosaNativeRunSaveFeedback::Saved, 342));
    assert(!render_baldosa_native_run_save_feedback(
        painter, pixels.data(), 344, 224,
        BaldosaNativeRunSaveFeedback::Saved, 320));
    assert(!render_baldosa_native_run_save_feedback(
        painter, pixels.data(), 255, 224,
        BaldosaNativeRunSaveFeedback::Saved));
    assert(!render_baldosa_native_run_save_feedback(
        ModernRootOverlayPainter{}, pixels.data(), 256, 224,
        BaldosaNativeRunSaveFeedback::Saved));
    assert(fill_calls == previous_fill && border_calls == previous_fill);
    std::puts("PASS: native 1P/2P result save feedback uses source-width-centred host-only strip");
}
