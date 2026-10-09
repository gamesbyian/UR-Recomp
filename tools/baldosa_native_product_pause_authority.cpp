/* Optional native-pause extension to the already linkable human-only input
 * bridge. Build this only when the pinned Baldosa host has its native
 * set-paused ABI. A rejected host transition must not change input ownership.
 */
extern "C" int snesrecomp_desktop_product_set_paused(int paused);
extern "C" void ur_baldosa_product_set_host_focus(int owned);
extern "C" int ur_baldosa_product_set_paused(int paused) {
    if (!snesrecomp_desktop_product_set_paused(paused != 0))
        return 0;
    ur_baldosa_product_set_host_focus(paused != 0);
    return 1;
}
