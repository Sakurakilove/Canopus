/* Exact P65 3.100.043 experimental call boundaries; not production approval. */
#ifndef CANOPUS_P65_ABI_H
#define CANOPUS_P65_ABI_H
#include <stdint.h>
#include "canopus_target_config.h"
#include "canopus_p65_safety.h"
/* The experimental P65 path uses its recovered stock ET_REL loader. */
#undef CANOPUS_SUP_CUSTOM_LOADER

#ifndef CANOPUS_SUP_P65_RESIDENT
#error "P65 firmware hooks require the resident experimental build"
#endif

/* AP SHA-256: a19b601477569765103eaf468b937bd8026b4d68ffa5c896bde222a79e475858.
 * Read/write dispatch accesses fops +8/+12; unused trailing slots stay null.
 * register_driver is the four-argument P65 trampoline, not Band11's ABI. */
typedef struct {
    void *open;
    void *close;
    void *read;
    void *write;
    void *lseek;
    void *ioctl;
    uint8_t tail[24];
} file_operations;

#define CANOPUS_SUP_NUTTX_OPEN UINT32_C(0x0C8BEF01)
#define CANOPUS_SUP_NUTTX_CLOSE UINT32_C(0x0C8BDBA9)
#define CANOPUS_SUP_NUTTX_READ UINT32_C(0x0C8BEAF1)
/* Use the same live veneers as stock modlib/LVGL, not initializer-copy
 * storage at 0x0C24xxxx. Their runtime code aliases are 0x1C15xxxx.
 * Plain fd write: permission check and fops +12 dispatch, no seek.
 * 0x0C248455 is pwrite with a stack-passed 64-bit offset, NOT this ABI. */
#define CANOPUS_SUP_NUTTX_WRITE UINT32_C(0x0C8BE041)
#define CANOPUS_SUP_NUTTX_ERRNO_LOCATION UINT32_C(0x0C4F793D)
#define CANOPUS_SUP_NUTTX_RENAME UINT32_C(0x0C8BDF89)
#define CANOPUS_SUP_NUTTX_UNLINK UINT32_C(0x0C8BEFD1)
#define CANOPUS_SUP_INSMOD UINT32_C(0x0C4C49AD)
#define P65_REGISTER_DRIVER UINT32_C(0x0C8BD0D1)
#define CANOPUS_SUP_REGISTER_DRIVER(path, fops, mode, priv) \
    ((int (*)(const char *, const void *, uint32_t, void *)) \
        (uintptr_t)P65_REGISTER_DRIVER)((path), (fops), (mode), (priv))

int canopus_p65_registry_firmware_persist(const uint8_t *data, uint32_t size);
int canopus_p65_registry_firmware_restore(uint8_t *data, uint32_t size);

#define P65_NOTIFICATION_INSERT UINT32_C(0x0CA60099)
/* Startup copy: raw 0x0c0efdc4 -> executable alias 0x1c000000.
 * These entries are copied functions, not callable flash storage. */
#define P65_APP_INSTALL UINT32_C(0x1C151AE5)
#define P65_APP_LOOKUP UINT32_C(0x1C15165D)
/* C7EC450 consumes r0 as a uint16 app ID, calls the ID lookup at
 * manager +24/+4, then C7EBD10 creates its launcher record. It is NOT
 * a void(void) refresh. The list getter's false branch does not reload names. */
#define P65_LAUNCHER_ADD UINT32_C(0x0C7EC451)
#define P65_LAUNCHER_LIST UINT32_C(0x0C7ECAE5)
#define P65_LIST_FIRST UINT32_C(0x0C73E1C5)
#define P65_LIST_NEXT UINT32_C(0x0C73E1E5)
/* Exact all_list caller C764170: create(parent), then set_title(list,text).
 * C8BE008 was previously misidentified as the list factory. */
#define P65_LIST_CREATE UINT32_C(0x0C8BC759)
#define P65_LIST_SET_TITLE UINT32_C(0x0C8BE009)
#define P65_LIST_CONFIGURE UINT32_C(0x0C8BEF61)
#define P65_LIST_FINALIZE UINT32_C(0x0C8BEBC1)
#define P65_LIST_REFRESH UINT32_C(0x1C147055)
#define P65_ROW_CREATE UINT32_C(0x0C8BEB71)
#define P65_ROW_CLASS UINT32_C(0x3C21B55C)
#define P65_LABEL_CREATE UINT32_C(0x0C78BCB5)
#define P65_LABEL_TEXT UINT32_C(0x0C78C879)
#define P65_OBJECT_SIZE UINT32_C(0x0C8BDEC9)
#define P65_OBJECT_ALIGN UINT32_C(0x0C8BC7C9)
#define P65_EVENT_ADD UINT32_C(0x0C8BCE79)
#define P65_EVENT_REMOVE UINT32_C(0x0C8BD6D9)
#define P65_OBJECT_ADD_FLAG UINT32_C(0x0C8BCCA1)
#endif
