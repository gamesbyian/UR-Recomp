#include "modern_controller_prompt.hpp"

#include <cassert>
#include <string>

using namespace ur::product;

int main() {
    constexpr const char* expected[] = {
        "[UP]", "[DOWN]", "[LEFT]", "[RIGHT]",
        "[SELECT]", "[START]", "[A]", "[B]",
        "[X]", "[Y]", "[L]", "[R]",
    };
    constexpr const char* names[] = {
        "UP", "DOWN", "LEFT", "RIGHT",
        "SELECT", "START", "A", "B",
        "X", "Y", "L", "R",
    };

    for (int i = 0; i < 12; ++i) {
        ModernControllerSemanticControl semantic{};
        assert(modern_controller_semantic_control_from_index(i, &semantic));
        assert(static_cast<int>(semantic) == i);
        assert(std::string(modern_controller_semantic_name(semantic)) ==
               names[i]);
        assert(std::string(modern_controller_semantic_prompt(semantic)) ==
               expected[i]);
        assert(std::string(modern_controller_prompt_from_index(i)) ==
               expected[i]);
    }

    ModernControllerSemanticControl semantic{};
    assert(!modern_controller_semantic_control_from_index(-1, &semantic));
    assert(!modern_controller_semantic_control_from_index(12, &semantic));
    assert(!modern_controller_semantic_control_from_index(0, nullptr));
    assert(std::string(modern_controller_prompt_from_index(-1)) == "[?]");
    assert(std::string(modern_controller_prompt_from_index(12)) == "[?]");

    const auto invalid =
        static_cast<ModernControllerSemanticControl>(255);
    assert(std::string(modern_controller_semantic_name(invalid)) ==
           "UNKNOWN");
    assert(std::string(modern_controller_semantic_prompt(invalid)) ==
           "[?]");

    return 0;
}
