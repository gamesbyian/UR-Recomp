#include "multiplayer_match_browser.hpp"

namespace ur::product {

void MultiplayerMatchBrowser::set_matches(
    std::vector<StoredMultiplayerMatch> matches) {
    matches_ = std::move(matches);
    if (matches_.empty()) {
        selected_ = 0;
    } else if (selected_ >= matches_.size()) {
        selected_ = matches_.size() - 1u;
    }
    view_ = MultiplayerMatchBrowserView::List;
}

const StoredMultiplayerMatch*
MultiplayerMatchBrowser::selected_match() const noexcept {
    if (matches_.empty() || selected_ >= matches_.size()) return nullptr;
    return &matches_[selected_];
}

std::optional<MultiplayerMatchRowPresentation>
MultiplayerMatchBrowser::selected_row_presentation() const {
    const auto* match = selected_match();
    if (!match) return std::nullopt;
    return present_multiplayer_match_row(*match);
}

std::optional<MultiplayerMatchDetailPresentation>
MultiplayerMatchBrowser::selected_detail_presentation() const {
    if (view_ != MultiplayerMatchBrowserView::Detail) return std::nullopt;
    const auto* match = selected_match();
    if (!match) return std::nullopt;
    return present_multiplayer_match_detail(*match);
}

bool MultiplayerMatchBrowser::move(int delta) noexcept {
    if (view_ != MultiplayerMatchBrowserView::List ||
        matches_.empty() || delta == 0) {
        return false;
    }

    const std::size_t before = selected_;
    if (delta > 0) {
        selected_ = (selected_ + 1u) % matches_.size();
    } else {
        selected_ =
            selected_ == 0 ? matches_.size() - 1u : selected_ - 1u;
    }
    return selected_ != before;
}

bool MultiplayerMatchBrowser::open_selected() noexcept {
    if (view_ != MultiplayerMatchBrowserView::List || matches_.empty()) {
        return false;
    }
    view_ = MultiplayerMatchBrowserView::Detail;
    return true;
}

bool MultiplayerMatchBrowser::back() noexcept {
    if (view_ != MultiplayerMatchBrowserView::Detail) return false;
    view_ = MultiplayerMatchBrowserView::List;
    return true;
}

}  // namespace ur::product
