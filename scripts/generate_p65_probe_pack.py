"""Verifier overlay for constants compared by the read-only loader probe.

This permits identity/driver reads and pointer equality only. It does not
promote the Supervisor, native Manager, or callable SDK capabilities.
"""
import argparse
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'xiaomi-p65-3.100.043'
ADDRESSES = (0x3c4501d0, 0x0c7357d5, 0x0c735789, 0x0c735739,
             0x0c7356e9, 0x0c73589d, 0x0c735691)


def generate(output):
    output = Path(output).resolve()
    original = ROOT / 'targets' / TARGET
    target = output / TARGET
    if target == original or original in target.parents:
        raise ValueError('Probe overlay must stay separate from the SDK pack')
    target.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(original / 'target.toml', target / 'target.toml')
    symbols = target / 'symbols'
    symbols.mkdir(exist_ok=True)
    for path in symbols.glob('*.json'):
        path.unlink()
    for path in (original / 'symbols').glob('*.json'):
        shutil.copyfile(path, symbols / path.name)
    for address in ADDRESSES:
        name = f'readonly_probe_{address:08x}'
        record = {
            'schema': 1, 'symbol_id': TARGET + '.' + name, 'target_id': TARGET,
            'name': name, 'kind': 'global', 'entry_address': hex(address),
            'callable_address': None, 'instruction_set': 'thumb',
            'prototype': 'read-only identity/driver comparison constant',
            'calling_convention': 'arm-aapcs',
            'contexts': {'allowed': ['readonly_loader_probe'], 'blocking': False},
            'ownership': {'return_value': 'none'}, 'side_effects': [],
            'proof': {'static': 'partial', 'device': 'not_probed', 'evidence_ids': []},
            'policy': 'restricted', 'status': 'CANDIDATE', 'approval_state': 'PENDING',
            'provenance': {
                'firmware_sha256': 'a19b601477569765103eaf468b937bd8026b4d68ffa5c896bde222a79e475858',
                'source': 'Exact AP initializer 0x0c7358f4; read-only comparisons',
            },
            'notes': 'Not permission to call; final probe must have no external calls.',
        }
        (symbols / (TARGET + '.' + name + '.json')).write_text(json.dumps(record, indent=2)+'\n')
    return target


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    print(generate(parser.parse_args().output))
