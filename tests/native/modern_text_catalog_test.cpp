#include "modern_text_catalog.hpp"

#include <cassert>
#include <cstring>

using namespace ur::product;

namespace {

bool same(const char* lhs, const char* rhs) {
    return std::strcmp(lhs, rhs) == 0;
}

}  // namespace

int main() {
    assert(same(modern_text_key(ModernTextId::RootPlay), "root.play"));
    assert(same(modern_text_key(ModernTextId::RootPractice), "root.practice"));
    assert(same(modern_text_key(ModernTextId::RootMultiplayer), "root.multiplayer"));
    assert(same(modern_text_key(ModernTextId::RootRecords), "root.records"));
    assert(same(modern_text_key(ModernTextId::RootOptions), "root.options"));

    assert(same(modern_text_default(ModernTextId::RootPlay), "PLAY"));
    assert(same(modern_text_default(ModernTextId::RootPractice), "PRACTICE"));
    assert(same(modern_text_default(ModernTextId::RootMultiplayer), "MULTIPLAYER"));
    assert(same(modern_text_default(ModernTextId::RootRecords), "RECORDS"));
    assert(same(modern_text_default(ModernTextId::RootOptions), "OPTIONS"));

    const auto invalid = static_cast<ModernTextId>(255);
    assert(same(modern_text_key(invalid), "root.play"));
    assert(same(modern_text_default(invalid), "PLAY"));

    return 0;
}
