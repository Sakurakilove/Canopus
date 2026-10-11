#!/bin/sh
# Build an isolated read-only removable probe; never enables the Supervisor.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
FIRMWARE=${CANOPUS_P65_FIRMWARE:?Set CANOPUS_P65_FIRMWARE to the exact AP or OTA}
CC=${CC:-clang}
LD=${LD:-ld.lld}
OUT="$ROOT/build/p65-loader-probe"
python3 "$ROOT/scripts/audit_p65_firmware.py" "$FIRMWARE" >/dev/null
mkdir -p "$OUT"
"$CC" --target=arm-none-eabi -mcpu=cortex-m33 -mthumb -mfloat-abi=soft \
    -Os -ffreestanding -fno-common -fno-builtin -fno-stack-protector \
    -fno-unwind-tables -fno-asynchronous-unwind-tables -Wall -Wextra -Werror \
    -I"$ROOT/targets/xiaomi-p65-3.100.043/generated" \
    -c "$ROOT/diagnostics/p65-loader-probe/probe.c" -o "$OUT/probe.o"
"$LD" -r -T "$ROOT/scripts/canopus_module_sections.ld" \
    -e canopus_p65_probe_initialize "$OUT/probe.o" -o "$OUT/probe.elf"
python3 "$ROOT/scripts/generate_p65_probe_pack.py" --output "$OUT/targets"
"$ROOT/target/debug/canopus" verify "$OUT/probe.elf" \
    --target xiaomi-p65-3.100.043 --targets-dir "$OUT/targets"
printf 'Built isolated P65 loader probe. No Supervisor, hook or app registration.\n'
