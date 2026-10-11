# P65 isolated loader probe

This is a separate installation diagnostic, not a re-enable of the withdrawn
P65 Supervisor/Manager. Its exact firmware identity and initialized file-driver
fields are read-only comparisons. It imports/calls no firmware functions and
has no constructors, hooks, app registration, device endpoints or filesystem
writes. On success, it supplies the stock modlib pair with a no-op unload
callback. The accompanying Lua watchface immediately removes the module.

The normal P65 Supervisor deployment guard remains disabled. Do not use this
probe result as proof of Supervisor, native Manager, global theme reload or
cold-boot correctness. This diagnostic itself is NOT_PROBED on hardware.

Build with an ARM Clang/lld and an already built Canopus CLI:

```sh
export CANOPUS_P65_FIRMWARE=/path/to/vela_ap.bin
sh scripts/build_p65_loader_probe.sh
python3 -m unittest scripts.tests.test_p65_loader_probe -v
```

The verifier overlay permits comparison constants only and stays separate from
the SDK target pack. Firmware/driver mismatch returns -211/-212 before any
callback is published. Its compiled entry/unload run in Thumb emulation. Seven
checks include the real AP insertion/removal control flow; filesystem section
load/bind, module registry and allocator leaves are modeled. The test checks
write boundaries, null input, both identity fields, every driver field, success
registration/removal and identity-failure cleanup. It cannot prove real module
relocation, filesystem or physical-device behavior.
