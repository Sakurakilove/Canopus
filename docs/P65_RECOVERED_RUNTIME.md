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

Offline checks exercise the exact firmware ELF parser, section layout, symbol
binding and module entry with modeled allocation and device registration. They
do not establish native app registration, physical cold-boot behavior or UI
stability on a real watch. Do not mix this runtime with a standalone RW6 icon
module loaded earlier in the same boot; restart before changing runtimes.
