"""Execute the isolated probe and real P65 insertion/removal control flow.

Filesystem/ELF section loading, registry and allocator are modeled. This is
not device validation. The probe itself may only write its caller pair/stack.
"""
import importlib.util
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from elftools.elf.elffile import ELFFile
from unicorn import UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_SP, UC_ARM_REG_LR

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('p65_ap', ROOT/'scripts/tests/test_p65_firmware_io.py')
firmware = importlib.util.module_from_spec(spec)
spec.loader.exec_module(firmware)


class LoaderProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name)
        clang, linker = os.environ.get('CC', 'clang'), os.environ.get('LD', 'ld.lld')
        subprocess.run([clang, '--target=arm-none-eabi', '-mcpu=cortex-m33', '-mthumb',
            '-mfloat-abi=soft', '-Os', '-ffreestanding', '-fno-common', '-fno-builtin',
            '-fno-stack-protector', '-fno-unwind-tables', '-fno-asynchronous-unwind-tables',
            '-I'+str(ROOT/'targets/xiaomi-p65-3.100.043/generated'), '-c',
            str(ROOT/'diagnostics/p65-loader-probe/probe.c'), '-o', str(cls.out/'probe.o')], check=True)
        subprocess.run([linker, '-Ttext=0x20010000', '--entry=canopus_p65_probe_initialize',
            '-T', str(ROOT/'scripts/canopus_module_sections.ld'), str(cls.out/'probe.o'),
            '-o', str(cls.out/'probe.elf')], check=True)
        with (cls.out/'probe.elf').open('rb') as f:
            elf = ELFFile(f)
            cls.sections = [(s['sh_addr'],s.data()) for s in elf.iter_sections()
                            if s['sh_flags']&2 and s['sh_type']!='SHT_NOBITS']
            cls.entry = elf['e_entry']

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def machine(self):
        m = firmware.WriteMachine()
        m.u.mem_map(0x3c450000,0x10000)
        m.u.mem_write(0x3c4501d0,struct.pack('<13I',ord('/'),0,0,
            0x0c7357d5,0x0c735789,0x0c735739,0x0c7356e9,0x0c73589d,0x0c735691,0,0,0,0))
        for a,d in self.sections:m.u.mem_write(a,d)
        return m

    def call(self,m,entry,args=()):
        for i,r in enumerate(m.args):m.u.reg_write(r,args[i] if i<len(args) else 0)
        for i,r in enumerate(m.saved):m.u.reg_write(r,0x34560000+i)
        m.u.reg_write(UC_ARM_REG_SP,m.STACK)
        m.u.reg_write(UC_ARM_REG_LR,m.STOP|1)
        m.u.emu_start(entry,m.STOP,count=20000)
        self.assertEqual(m.u.reg_read(UC_ARM_REG_PC),m.STOP)
        self.assertEqual(m.u.reg_read(UC_ARM_REG_SP),m.STACK)
        for i,r in enumerate(m.saved):self.assertEqual(m.u.reg_read(r),0x34560000+i)
        v=m.reg(0)
        return v if v<0x80000000 else v-0x100000000

    def test_probe_writes_only_pair_and_stack_and_is_removable(self):
        m=self.machine();pair=0x20006000;writes=[]
        before=bytes(m.u.mem_read(0x3c4501d0,52))
        m.u.hook_add(UC_HOOK_MEM_WRITE,lambda u,t,a,s,v,d:writes.append((a,s)))
        self.assertEqual(self.call(m,self.entry,(pair,)),0)
        callback=m.word(pair)
        self.assertTrue(callback&1)
        self.assertEqual(m.word(pair+4),0)
        self.assertEqual(self.call(m,callback,(0,)),0)
        self.assertEqual(bytes(m.u.mem_read(0x3c4501d0,52)),before)
        self.assertTrue(all(pair<=a<a+s<=pair+8 or m.STACK-256<=a<a+s<=m.STACK
                            for a,s in writes))
        self.assertEqual((m.gets,m.puts,m.writes),(0,0,[]))

    def test_wrong_firmware_rejects_before_driver_read(self):
        m=self.machine();m.u.mem_unmap(0x3c450000,0x10000)
        m.u.mem_write(0x0c3bf9fd,b'3.100.044')
        self.assertEqual(self.call(m,self.entry,(0x20006000,)),-211)
        self.assertEqual(m.word(0x20006000),0)

    def test_wrong_build_rejects(self):
        m=self.machine();m.u.mem_write(0x0cbff458,b'xxxxxxxx')
        self.assertEqual(self.call(m,self.entry,(0x20006000,)),-211)

    def test_each_driver_mismatch_rejects_without_publish(self):
        for off in (0,4,12,16,20,24,28,32):
            m=self.machine();m.word(0x3c4501d0+off,m.word(0x3c4501d0+off)^1)
            self.assertEqual(self.call(m,self.entry,(0x20006000,)),-212)
            self.assertEqual(m.word(0x20006000),0)

    def test_null_pair_rejects(self):
        self.assertEqual(self.call(self.machine(),self.entry,(0,)),-22)

    def insert(self,wrong_identity=False):
        m=self.machine();events=[];record=0x3c408000
        m.u.mem_write(record,bytes(160));m.u.mem_write(m.BUFFER,b'/test/probe.bin\0')
        m.u.mem_write(m.BUFFER+64,b'rw6_probe_v1\0')
        if wrong_identity:m.u.mem_write(0x0c3bf9fd,b'3.100.044')
        m.hook(0x0c4f9f70,lambda:events.append('lock') or 0)
        m.hook(0x0c4f9f80,lambda:events.append('unlock') or 0)
        m.hook(0x0c4f9ff8,lambda:0)
        def parse():
            info=m.reg(1);m.u.mem_write(info,bytes(144))
            m.word(info,0x20010000);m.word(info+12,4096)
            m.word(info+0x30,1);m.word(info+0x38,self.entry-0x20010000)
            return 0
        m.hook(0x0c4f9a70,parse)
        m.hook(0x0c50b320,lambda:record)
        m.hook(0x0c5048c0,lambda:m.reg(0)) # Module-name copying modeled.
        m.hook(0x0c4f9b58,lambda:0)
        m.hook(0x0c4f901c,lambda:0) # Section placement/binding modeled.
        m.hook(0x0c4f9f90,lambda:events.append('register') or 0)
        m.hook(0x0c4fa464,lambda:events.append('close') or 0)
        m.hook(0x0c4fa484,lambda:events.append('release_sections') or 0)
        m.hook(0x0c50b25c,lambda:events.append(('free',m.reg(0))) or 0)
        m.hook(0x0c4f793c,lambda:m.ERRNO)
        result=self.call(m,0x0c4c49ad,(m.BUFFER,m.BUFFER+64))
        return m,events,record,result

    def test_real_ap_insert_publishes_probe_unload_pair_then_remove_releases(self):
        m,events,record,result=self.insert()
        self.assertEqual(result,record)
        self.assertIn('register',events)
        self.assertTrue(m.word(record+104)&1)
        m.hook(0x0c4fa020,lambda:0)
        m.hook(0x0c4f9fb4,lambda:events.append('unregister') or 0)
        m.hook(0x0c4f9a14,lambda:events.append('cleanup') or 0)
        self.assertEqual(self.call(m,0x0c4c4ae5,(record,)),0)
        self.assertIn('unregister',events)
        self.assertIn(('free',record),events)
        self.assertEqual(m.word(record+104),0)

    def test_real_ap_insert_wrong_identity_never_registers(self):
        m,events,record,result=self.insert(True)
        self.assertEqual(result,0)
        self.assertNotIn('register',events)
        self.assertEqual(m.word(m.ERRNO),211)


if __name__ == '__main__':unittest.main()
