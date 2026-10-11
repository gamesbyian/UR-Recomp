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
void fill(std::uint32_t*, int, int, int, int, int, int, std::uint32_t) {
    ++fill_calls;
}
void stroke(std::uint32_t*, int, int, int, int, int, int, std::uint32_t) {
    ++border_calls;
}
void text(std::uint32_t*, int, int, int, int,
          const char* value, std::uint32_t, int) {
    label = value ? value : "";
}
}

int main() {
    std::vector<std::uint32_t> pixels(256u * 224u, 0u);
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
    assert(render_baldosa_native_run_save_feedback(
        painter, pixels.data(), 256, 224,
        BaldosaNativeRunSaveFeedback::Saved));
    assert(label == "RECORD SAVED");
    assert(render_baldosa_native_run_save_feedback(
        painter, pixels.data(), 256, 224,
        BaldosaNativeRunSaveFeedback::NotSaved));
    assert(label == "RECORD NOT SAVED");
    assert(!render_baldosa_native_run_save_feedback(
        painter, pixels.data(), 255, 224,
        BaldosaNativeRunSaveFeedback::Saved));
    assert(!render_baldosa_native_run_save_feedback(
        ModernRootOverlayPainter{}, pixels.data(), 256, 224,
        BaldosaNativeRunSaveFeedback::Saved));
    assert(fill_calls == 3 && border_calls == 3);
    std::puts("PASS: real native 1P result save feedback is explicit and host-only");
}
