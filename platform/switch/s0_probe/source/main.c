#include <switch.h>
#include <SDL2/SDL.h>

#include <stdio.h>

int main(int argc, char **argv) {
    (void)argc;
    (void)argv;

    SDL_version version;
    SDL_GetVersion(&version);

    const AppletOperationMode operation_mode = appletGetOperationMode();
    printf(
        "UR_SWITCH_S0 libnx=linked sdl=%u.%u.%u operation_mode=%d\n",
        (unsigned)version.major,
        (unsigned)version.minor,
        (unsigned)version.patch,
        (int)operation_mode
    );

    /*
     * Gate S0 is compile/link/package only. Runtime lifecycle, display, input,
     * audio, storage and suspend/resume belong to S1 hardware acceptance.
     */
    return 0;
}
