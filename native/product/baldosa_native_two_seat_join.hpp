#pragma once

// Two explicit human confirmations before a native stock 2P handoff.
// Reuses the existing profile catalog and actual P1/P2 device ownership.
// This is an ephemeral host selection, not a replacement profile store,
// guest rider write or canonical multiplayer result/persistence authority.
#include "host_profile_catalog.hpp"
#include "host_profile_runtime.hpp"

#include <cctype>
#include <cstddef>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace ur::product {

class BaldosaNativeTwoSeatJoin {
public:
    bool begin(std::vector<HostProfileCatalogEntry> catalog,
               std::string_view active_profile_id) {
        cancel();
        if (catalog.size() < 2 || catalog.size() > 128 ||
            !is_safe_profile_storage_id(active_profile_id)) return false;
        std::size_t active = catalog.size();
        for (std::size_t i = 0; i < catalog.size(); ++i) {
            const auto& entry = catalog[i];
            if (!is_safe_profile_storage_id(entry.profile_id) ||
                !valid_racer_identity(entry.identity)) return false;
            for (std::size_t j = 0; j < i; ++j) {
                if (same_id(entry.profile_id, catalog[j].profile_id))
                    return false;
            }
            if (same_id(entry.profile_id, active_profile_id))
                active = i;
        }
        if (active == catalog.size()) return false;
        catalog_ = std::move(catalog);
        active_index_ = active;
        cursor_[0] = cursor_[1] = active;
        cursor_[1] = (active + 1) % catalog_.size();
        open_ = true;
        return true;
    }

    void cancel() noexcept {
        open_ = false;
        catalog_.clear();
        chosen_[0].reset();
        chosen_[1].reset();
        active_index_ = 0;
        cursor_[0] = cursor_[1] = 0;
    }

    bool open() const noexcept { return open_; }
    bool ready() const noexcept {
        return open_ && chosen_[0].has_value() && chosen_[1].has_value();
    }
    bool confirmed(unsigned seat) const noexcept {
        return seat < 2 && chosen_[seat].has_value();
    }
    // A confirmation snapshots identity. Other Modern processes can edit the
    // catalog while this controller-only join panel is open. Revalidate the
    // exact confirmed entries before allowing the guest to start stock 2P.
    // The result writer still performs its own locked admission at finish.
    bool confirmed_profiles_match_catalog(
        const std::vector<HostProfileCatalogEntry>& current) const noexcept {
        if (!ready()) return false;
        for (unsigned seat = 0; seat < 2; ++seat) {
            const auto& selected = *chosen_[seat];
            unsigned matches = 0;
            for (const auto& entry : current) {
                if (!same_id(entry.profile_id, selected.profile_id))
                    continue;
                // Case-fold aliases share Windows storage identity but do
                // not preserve this exact confirmed canonical catalog entry.
                if (++matches != 1 ||
                    entry.profile_id != selected.profile_id ||
                    !(entry.identity == selected.identity))
                    return false;
            }
            if (matches != 1) return false;
        }
        return same_id(chosen_[0]->profile_id,
                       catalog_[active_index_].profile_id) &&
               !same_id(chosen_[0]->profile_id,
                        chosen_[1]->profile_id);
    }
    const HostProfileCatalogEntry* candidate(unsigned seat) const noexcept {
        return open_ && seat < 2 && cursor_[seat] < catalog_.size()
            ? &catalog_[cursor_[seat]] : nullptr;
    }
    const HostProfileCatalogEntry* participant(unsigned seat) const noexcept {
        return open_ && seat < 2 && chosen_[seat].has_value()
            ? &*chosen_[seat] : nullptr;
    }
    // Selection is explicit. Changing a highlighted profile revokes that
    // seat's prior confirmation without implicitly claiming another profile.
    bool move(unsigned seat, int delta) noexcept {
        // Native P1's active SRAM was selected before guest boot. Until a
        // real cross-profile reboot transaction exists, browsing another
        // P1 identity would falsely promise a switch this process cannot do.
        if (!open_ || seat != 1 || !delta || catalog_.empty()) return false;
        // P2 may never own the already-booted P1 profile. Skipping that
        // cursor avoids offering an impossible match that can be confirmed
        // before P1 has even pressed A. With only two profiles, moving is
        // a no-op and must not revoke an already confirmed P2 identity.
        const auto count = catalog_.size();
        if (count == 2) return false;
        auto next = delta > 0
            ? (cursor_[seat] + 1) % count
            : (cursor_[seat] + count - 1) % count;
        if (next == active_index_)
            next = delta > 0
                ? (next + 1) % count
                : (next + count - 1) % count;
        if (next == cursor_[seat]) return false;
        cursor_[seat] = next;
        chosen_[seat].reset();
        return true;
    }
    bool confirm(unsigned seat) noexcept {
        if (!open_ || seat >= 2 || catalog_.empty()) return false;
        const auto& selected = catalog_[cursor_[seat]];
        // The native guest boots exactly one named SRAM; P1 must be the
        // already-authorized active identity. Do not switch SRAM in flight.
        if ((seat == 0 && cursor_[seat] != active_index_) ||
            (seat == 1 && cursor_[seat] == active_index_)) return false;
        const auto& other = chosen_[1 - seat];
        if (other && same_id(selected.profile_id, other->profile_id))
            return false;
        chosen_[seat] = selected;
        return true;
    }
    bool clear(unsigned seat) noexcept {
        if (!open_ || seat >= 2) return false;
        chosen_[seat].reset();
        return true;
    }

private:
    static bool same_id(std::string_view a, std::string_view b) noexcept {
        if (a.size() != b.size()) return false;
        for (std::size_t i = 0; i < a.size(); ++i) {
            const auto left = static_cast<unsigned char>(a[i]);
            const auto right = static_cast<unsigned char>(b[i]);
            if (std::tolower(left) != std::tolower(right)) return false;
        }
        return true;
    }

    bool open_ = false;
    std::vector<HostProfileCatalogEntry> catalog_;
    std::optional<HostProfileCatalogEntry> chosen_[2];
    std::size_t cursor_[2] = {};
    std::size_t active_index_ = 0;
};

} // namespace ur::product
