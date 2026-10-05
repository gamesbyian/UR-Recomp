#include "modern_controls_binding_authority.hpp"

namespace ur::product {

bool apply_modern_controls_command(
    const ModernControlsCommand& command,
    const ModernControlsBindingAuthority& authority) {
    switch (command.kind) {
    case ModernControlsCommandKind::ApplyCapturedKey:
        if (!authority.set_button || !authority.save ||
            command.key_scancode <= 0) {
            return false;
        }
        authority.set_button(
            static_cast<int>(command.binding),
            command.key_scancode);
        authority.save();
        return true;

    case ModernControlsCommandKind::ClearBinding:
        if (!authority.set_button || !authority.save) return false;
        authority.set_button(
            static_cast<int>(command.binding),
            0);
        authority.save();
        return true;

    case ModernControlsCommandKind::ResetPlayer:
        if (!authority.reset_player || !authority.save) return false;
        authority.reset_player();
        authority.save();
        return true;

    case ModernControlsCommandKind::None:
    case ModernControlsCommandKind::BeginCapture:
    case ModernControlsCommandKind::Close:
        return false;
    }
    return false;
}

}  // namespace ur::product
