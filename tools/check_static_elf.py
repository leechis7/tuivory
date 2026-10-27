#!/usr/bin/env python3
"""Reject Linux artifacts requiring an interpreter or DT_NEEDED shared library."""
import argparse
from pathlib import Path
import struct

MACHINES = {'x86_64': 62, 'arm64': 183}


def inspect(path, arch=None):
    data = Path(path).read_bytes()
    if len(data) < 64 or data[:6] != b'\x7fELF\x02\x01':
        raise ValueError(f'{path}: expected little-endian ELF64')
    machine = struct.unpack_from('<H', data, 18)[0]
    if arch and machine != MACHINES[arch]:
        raise ValueError(f'{path}: wrong architecture, expected {arch}')
    phoff = struct.unpack_from('<Q', data, 32)[0]
    size, count = struct.unpack_from('<HH', data, 54)
    if size < 56 or not count or phoff + size * count > len(data):
        raise ValueError(f'{path}: invalid ELF program headers')
    for index in range(count):
        header = struct.unpack_from('<IIQQQQQQ', data, phoff + index * size)
        kind, offset, length = header[0], header[2], header[5]
        if offset + length > len(data):
            raise ValueError(f'{path}: invalid segment')
        if kind == 3:  # PT_INTERP
            raise ValueError(f'{path}: dynamic interpreter is forbidden')
        if kind == 2:  # Static PIE has PT_DYNAMIC for relocation; it is allowed.
            for position in range(offset, offset + length - 15, 16):
                tag, _ = struct.unpack_from('<qQ', data, position)
                if tag == 0:
                    break
                if tag == 1:  # DT_NEEDED
                    raise ValueError(f'{path}: shared-library dependency is forbidden')
    return machine


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--arch', choices=MACHINES)
    parser.add_argument('binaries', nargs='+', type=Path)
    args = parser.parse_args()
    for binary in args.binaries:
        machine = inspect(binary, args.arch)
        print(f'{binary}: static ELF verified (machine={machine}, no PT_INTERP/DT_NEEDED)')


if __name__ == '__main__':
    main()
