/* Isolated, removable loader/identity probe. This is not the withdrawn P65
 * Supervisor: no constructors, firmware calls, hooks, app/device registration,
 * filesystem writes, or persistent startup state. */
#include <stdint.h>
#include "canopus_veneer.h"

struct p65_unload_pair {
    int32_t (*callback)(void *);
    void *context;
};
_Static_assert(sizeof(struct p65_unload_pair) == 8, "P65 unload ABI");

static int32_t probe_unload(void *context)
{
    (void)context;
    return 0;
}

__attribute__((used, section(".text.canopus_module_entry")))
int32_t canopus_p65_probe_initialize(struct p65_unload_pair *pair)
{
    const volatile uint32_t *driver;
    if (!pair) return -22;
    pair->callback = 0;
    pair->context = 0;
    if (canopus_identity_guard()) return -211;
    /* Read only the exact driver's initialized fields after identity. */
    driver = (const volatile uint32_t *)(uintptr_t)0x3c4501d0u;
    if ((driver[0] & 255u) != '/' || driver[1] != 0 ||
        driver[3] != 0x0c7357d5u || driver[4] != 0x0c735789u ||
        driver[5] != 0x0c735739u || driver[6] != 0x0c7356e9u ||
        driver[7] != 0x0c73589du || driver[8] != 0x0c735691u) return -212;
    pair->callback = probe_unload;
    return 0;
}
