#include "internal_render_scale_policy.hpp"

#include <cassert>

int main() {
    using ur::product::resolve_internal_render_scale;

    assert(resolve_internal_render_scale(true, false, 1) == 1);
    assert(resolve_internal_render_scale(true, false, 4) == 4);
    assert(resolve_internal_render_scale(true, true, 4) == 1);
    assert(resolve_internal_render_scale(false, false, 4) == 1);
    assert(resolve_internal_render_scale(true, false, 0) == 1);
    assert(resolve_internal_render_scale(true, false, 5) == 1);
    return 0;
}
