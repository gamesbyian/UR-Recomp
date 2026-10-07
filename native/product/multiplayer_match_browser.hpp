#pragma once

#include "multiplayer_match_catalog.hpp"
#include "multiplayer_match_presentation.hpp"

#include <cstddef>
#include <optional>
#include <vector>

namespace ur::product {

enum class MultiplayerMatchBrowserView {
    List = 0,
    Detail = 1,
};

class MultiplayerMatchBrowser {
public:
    void set_matches(std::vector<StoredMultiplayerMatch> matches);

    MultiplayerMatchBrowserView view() const noexcept { return view_; }
    std::size_t size() const noexcept { return matches_.size(); }
    bool empty() const noexcept { return matches_.empty(); }
    std::size_t selected_index() const noexcept { return selected_; }

    const StoredMultiplayerMatch* selected_match() const noexcept;
    std::optional<MultiplayerMatchRowPresentation>
    row_presentation(std::size_t index) const;
    std::optional<MultiplayerMatchRowPresentation>
    selected_row_presentation() const;
    std::optional<MultiplayerMatchDetailPresentation>
    selected_detail_presentation() const;

    bool move(int delta) noexcept;
    bool open_selected() noexcept;
    bool back() noexcept;

private:
    std::vector<StoredMultiplayerMatch> matches_;
    MultiplayerMatchBrowserView view_ = MultiplayerMatchBrowserView::List;
    std::size_t selected_ = 0;
};

}  // namespace ur::product
