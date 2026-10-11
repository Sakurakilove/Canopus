#!/usr/bin/env python3
"""Focused offline proof of P65 launcher ID ABI; no device visibility claim.

Runs the unmodified firmware add, record allocation and list getter code.
Allocator, app lookup, name callback, logging and UI refresh are harness stubs.
"""
import argparse
import hashlib
import struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_LR, UC_ARM_REG_SP, UC_ARM_REG_PC

SHA = 'a19b601477569765103eaf468b937bd8026b4d68ffa5c896bde222a79e475858'
BASE = 0x0c0c0000
LIST = 0x3c3bf9dc
ORDER = 0x3c3bf9f4
APP = 0x20001000
LOOKUP = 0x20000100
NAME = 0x20000110
STOP = 0x20000120

def run(firmware, app_id):
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.mem_map(BASE, 0xc00000)
    u.mem_write(BASE, firmware)
    u.mem_map(0x3c000000, 0x800000)
    u.mem_map(0x20000000, 0x100000)
    def word(a, v): u.mem_write(a, struct.pack('<I', v))
    for a in (LIST, ORDER):
        u.mem_write(a, struct.pack('<3I', 24 if a == LIST else 132, 0, 0))
    word(0x3c3cf91c + 24, 0x20002000)
    word(0x20002004, LOOKUP | 1)
    word(APP + 8, 0x20003000)
    word(APP + 12, 0x20003100)
    word(APP + 28, NAME | 1)
    u.mem_write(APP + 16, struct.pack('<H', 0xca))
    u.mem_write(0x20003000, b'com.canopus.manager\0')
    u.mem_write(0x20003100, b'/data/canopus/manager_icon.bin\0')
    u.mem_write(0x20003200, b'Canopus\0')
    calls = []
    heap = [0x20004000]
    def hook(uc, pc, size, _):
        r0 = uc.reg_read(UC_ARM_REG_R0)
        if pc == STOP:
            uc.emu_stop(); return
        result = None
        if pc == LOOKUP:
            calls.append(r0); result = APP if r0 == 0xca else 0
        elif pc == NAME: result = 0x20003200
        elif pc == 0xc741b0c:
            result = heap[0]; heap[0] += (r0 + 7) & ~7
        elif pc == 0xc8be820:
            from unicorn.arm_const import UC_ARM_REG_R1, UC_ARM_REG_R2
            uc.mem_write(r0, bytes([uc.reg_read(UC_ARM_REG_R1) & 255]) * uc.reg_read(UC_ARM_REG_R2))
            result = r0
        elif pc in (0xc7f070c, 0xc7eba04, 0xc504a54): result = 0
        if result is not None:
            uc.reg_write(UC_ARM_REG_R0, result)
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
    u.hook_add(UC_HOOK_CODE, hook)
    def call(address, argument):
        u.reg_write(UC_ARM_REG_SP, 0x200ff000)
        u.reg_write(UC_ARM_REG_LR, STOP | 1)
        u.reg_write(UC_ARM_REG_R0, argument)
        u.emu_start(address | 1, STOP, count=10000)
        assert u.reg_read(UC_ARM_REG_PC) == STOP, 'firmware call did not return'
        return u.reg_read(UC_ARM_REG_R0)
    call(0xc7ec450, app_id)
    list_address = call(0xc7ecae4, 0)
    assert list_address == LIST
    first = call(0xc73e1c4, list_address)
    if app_id == 0xca:
        assert first and struct.unpack('<H',u.mem_read(first,2))[0] == app_id
        assert struct.unpack('<I',u.mem_read(first + 4,4))[0] == 0x20003200
        assert struct.unpack('<I',u.mem_read(first + 12,4))[0] == 0x20003100
    else: assert first == 0, 'invalid ID must not create a launcher record'
    assert calls == [app_id]
    return {'inputAppId':app_id, 'lookupReceived':calls[0], 'launcherRecordCreated':bool(first)}

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('firmware',type=Path)
    args=parser.parse_args()
    data=args.firmware.read_bytes()
    assert hashlib.sha256(data).hexdigest()==SHA
    import json
    print(json.dumps({'firmwareSha256':SHA, 'cases':[run(data,0xca),run(data,0)],
                     'deviceVerified':False},indent=2))
