# Redmi Watch 6 manual runtime candidate

This adaptation targets P65 firmware **3.100.043** only. It corrects the NuttX
write veneer, app installation/lookup and list refresh code aliases. It keeps
escaped callbacks resident until power-off and persists module intent in a
separate dual-slot registry. The historical P65 installer remains disabled.

The new `CANOPUS_P65_RECOVERED_RUNTIME` profile is an installable candidate,
not a claim that the earlier device boot-loop incident is resolved on hardware.
No global boot hook or firmware modification is included. After each reboot,
manually open the RW6 bootstrap watchface. It loads the native Supervisor,
registers the native Canopus Manager, then restores enabled modules from a
later UI timer turn. You can switch to any other watchface afterwards.

```sh
export CANOPUS_P65_FIRMWARE=/path/to/vela_ap.bin
export CC=clang LD=ld.lld
sh scripts/build_p65_runtime.sh
```

Python needs cryptography for a local Ed25519 installer trust key. The script
creates it under the ignored build directory; never publish its private half.
Use the matching key to sign module receipts. This candidate does not use the
upstream production release signing key. Its public key accompanies the build.

The bootstrap template is
`watchfaces/canopus-installer-prod/xiaomi-p65-runtime/main.lua`; substitute its
Supervisor byte count and CRC and inline the shared progress runner when
packing. Include `supervisor.bin` and the existing `manager_icon.bin`.
Corona uses the restricted `/canopus/install` CMI1 endpoint. Enable it and
choose **Immediately activate** in Canopus Manager after first installation.
Enabled-module intent survives reboot; restoration occurs when you reopen the
bootstrap, rather than through a system startup script.

AstroBox's official Canopus/Corona modules also use `.bin` Lua installers for
the native-component bootstrap; these files are not firmware updates. The
separate `Corona-Manager-RW6.rpk` is a QuickApp and must use AstroBox's
QuickApp/Application installation entry, while `.crpack` themes use the
resource-pack entry. The RW6 adaptation has not been added to the official
resource catalog; use the adapted local files rather than the Band installers
currently listed there.

Offline checks exercise the exact firmware ELF parser, section layout, symbol
binding and module entry with modeled allocation and device registration. They
do not establish native app registration, physical cold-boot behavior or UI
stability on a real watch. Do not mix this runtime with a standalone RW6 icon
module loaded earlier in the same boot; restart before changing runtimes.

## 0.3.2: publish the native Manager in the launcher

The earlier bootstrap reported ready after internal package registration even
though Canopus was absent from the device application list. Firmware entry
`0x0C7EC451` takes a `uint16_t` application ID, not `void(void)`: it looks up
that ID, allocates a 24-byte launcher record and inserts it in the launcher
list. The corrected call supplies `0x00CA`. The installer now checks for that
ID in the launcher before reporting success, skips an existing launcher entry,
and permits retry after publication fails without duplicating the package.
An existing package with foreign resident callbacks is rejected.

`python scripts/verify_p65_launcher.py /path/to/vela_ap.bin` runs the exact
firmware add/record-allocation/list-getter code under Unicorn (install Unicorn
and pass the pinned AP hash). It checks that ID 0xCA reaches the app lookup and
creates the expected ID/name/icon record; ID zero creates no entry. Allocator,
app lookup, logging and UI refresh are modeled. This is offline ABI evidence,
not confirmation of physical launcher visibility or native UI stability.

Replace the first bootstrap BIN and restart the watch before opening it. The
new code cannot replace an already resident Supervisor in the same boot. Keep
the existing Corona installation/registry and themes. The native application
entry is titled **Canopus**; it is created by this BIN, not a fourth package.

## 0.3.3: correct the native Manager title callback ABI

Device feedback confirms the 0.3.2 launcher entry appears, but opening Canopus
reboots the watch. The P65 list title entry `0x0C8BE009` is a five-argument
factory, not a two-argument text setter: its wrappers at `1C14885C` and
`1C14FB64` forward `(list, text, mode, event_callback, cookie)`, with the cookie
on the caller's stack. The old call left the mode and callback unspecified.
The native adapter now passes mode zero and explicit null callback/cookie and
checks the returned header. List refresh uses its one-argument signature. Page
creation rejects a null page/root and clears live/event state on init failure.
Module restoration stays in the bootstrap rather than the page-create path.

Offline verification executed the actual compiled `list_create` from the
updated Supervisor, with the exact firmware title wrappers and modeled widget
allocation/title leaf/style application. The five arguments were observed as
Canopus / mode=0 / callback=NULL / cookie=NULL with caller-saved registers and
stack cookie poisoned before the call. It does not execute the complete page
or verify physical stability. Update the bootstrap BIN and restart before
opening it; the device result still needs user confirmation.

### Native list text styles (0.3.4)

Stock row creation at `0x0C764638` applies primary style `0x3C47984C`
and secondary style `0x3C479888` through `0x0C8BCF21` with arguments
`(label, style, 255, 0)`. The P65 row adapter now uses these same styles
so Chinese text uses the firmware's font fallback instead of the default
label font. Row geometry, entry order and text remain unchanged. Compiled
call arguments were checked with modeled widget/style leaves; physical
glyph rendering and module activation still require device confirmation.
