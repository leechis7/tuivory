#!/usr/bin/env python3
"""Boot the CentOS 7.4 kernel/userspace and smoke-test static x86_64 binaries.

Requires Docker, qemu-system-x86_64 and the pinned official kernel. No KVM,
network in the guest, privileged containers, or host binfmt registration.
"""
import argparse
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import pty
import re
import select
import shlex
import struct
import subprocess
import tarfile
import tempfile
import termios
import time
import tty

from check_static_elf import inspect

IMAGE = 'centos@sha256:78b63c089c40a2ca0d85db9125fb3193c6ff74814bba5f894c803e5ae02a4035'
KERNEL_URL = 'https://vault.centos.org/7.4.1708/os/x86_64/isolinux/vmlinuz'
KERNEL_SHA256 = '8ede7f8d3c8f5e72f1a84713ad59b7b39211ea1af8887389cb50a189df937c6f'


def entry(output, name, mode, data=b'', device=(0, 0)):
    encoded = name.encode() + b'\0'
    fields = (0, mode, 0, 0, 1, 0, len(data), 0, 0, *device, len(encoded), 0)
    header = b'070701' + ''.join(f'{value:08x}' for value in fields).encode()
    output.write(header + encoded + b'\0' * (-(110 + len(encoded)) % 4))
    output.write(data + b'\0' * (-len(data) % 4))


def initramfs(rootfs, destination, binaries, consumers):
    commands = ['#!/bin/bash', 'set -eu',
                'trap \'echo TVR_FAILED; while :; do sleep 60; done\' ERR',
                'export TERM=xterm-256color LANG=en_US.UTF-8',
                'stty rows 36 cols 120',
                'test "$(uname -r)" = 3.10.0-693.el7.x86_64',
                'grep -q "7.4.1708" /etc/centos-release',
                'test "$(rpm -q glibc)" = glibc-2.17-196.el7.x86_64',
                'echo TVR_ENV; uname -r; cat /etc/centos-release; rpm -q glibc']
    for name in consumers:
        commands += [f'/work/{name}', f'echo TVR_CONSUMER_PASS:{name}']
    for name in binaries:
        for lang in ('ko', 'en'):
            commands += [f'echo TVR_START:{name}:{lang}',
                         f'/work/{name} --lang {lang}', f'echo TVR_PASS:{name}:{lang}']
    commands += ['echo TVR_ALL_PASSED', 'while :; do sleep 60; done']
    init = b'''#!/bin/bash
set -e
mount -t proc proc /proc
mount -t sysfs sysfs /sys
exec /usr/bin/setsid /bin/bash -c 'exec /bin/bash /work/run.sh </dev/ttyS0 >/dev/ttyS0 2>&1'
'''
    with gzip.open(destination, 'wb', compresslevel=1) as output, tarfile.open(rootfs) as archive:
        for member in archive:
            name = member.name
            while name.startswith('./'):
                name = name[2:]
            if name == '.':
                continue
            if not name or '..' in Path(name).parts or member.name.startswith('/'):
                if not name:
                    continue
                raise ValueError(f'Unsafe image member: {member.name}')
            if member.isdir():
                entry(output, name, 0o040000 | member.mode)
            elif member.issym():
                entry(output, name, 0o120000 | member.mode, member.linkname.encode())
            elif member.isfile() or member.islnk():
                with archive.extractfile(member) as source:
                    entry(output, name, 0o100000 | member.mode, source.read())
        for name, device in (('console', (5, 1)), ('null', (1, 3)), ('tty', (5, 0)), ('ttyS0', (4, 64))):
            entry(output, 'dev/' + name, 0o020600, device=device)
        entry(output, 'work', 0o040755)
        entry(output, 'work/run.sh', 0o100755, '\n'.join(commands).encode())
        entry(output, 'init', 0o100755, init)
        for name, path in {**binaries, **consumers}.items():
            entry(output, 'work/' + name, 0o100755, path.read_bytes())
        entry(output, 'TRAILER!!!', 0)


def boot(command, logfile, binaries, consumers, timeout):
    master, slave = pty.openpty()
    tty.setraw(slave)
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 36, 120, 0, 0))

    def terminal():
        os.setsid()
        fcntl.ioctl(0, termios.TIOCSCTTY, 0)

    process = subprocess.Popen(command, stdin=slave, stdout=slave, stderr=slave, preexec_fn=terminal)
    os.close(slave)
    captured = bytearray()
    reports, active, started, sent = 0, None, 0, False
    passes = set()
    deadline = time.monotonic() + timeout
    try:
        while time.monotonic() < deadline:
            if select.select([master], [], [], .1)[0]:
                try:
                    chunk = os.read(master, 65536)
                except OSError:
                    break
                if not chunk:
                    break
                captured.extend(chunk)
                logfile.write_bytes(captured)
                while reports < captured.count(b'\x1b[6n'):
                    os.write(master, b'\x1b[1;1R')
                    reports += 1
                for match in re.finditer(rb'TVR_START:([\w-]+):(ko|en)\r*\n', captured):
                    if active is None or match.end() > started:
                        active, started, sent = match.groups(), match.end(), False
                for match in re.finditer(rb'TVR_PASS:([\w-]+):(ko|en)\r*\n', captured):
                    key = match.groups()
                    if key in passes:
                        continue
                    begin = bytes(captured).rfind(b'TVR_START:' + key[0] + b':' + key[1], 0, match.start())
                    screen = bytes(captured[begin:match.start()])
                    korean = any('\uac00' <= char <= '\ud7a3' for char in screen.decode(errors='replace'))
                    if b'TUIVORY' not in screen or b'\x1b[?1049l' not in screen or korean != (key[1] == b'ko'):
                        raise RuntimeError(f'UI language/terminal restore failed: {key}')
                    passes.add(key)
                    print('PASS ' + ':'.join(part.decode() for part in key), flush=True)
                if re.search(rb'TVR_FAILED\r*\n', captured):
                    raise RuntimeError('Guest command failed')
                if re.search(rb'TVR_ALL_PASSED\r*\n', captured):
                    if len(passes) != 2 * len(binaries):
                        raise RuntimeError('Incomplete TUI checks')
                    for name in consumers:
                        if not re.search(f'TVR_CONSUMER_PASS:{name}'.encode() + rb'\r*\n', captured):
                            raise RuntimeError('Missing external consumer result: ' + name)
                    print('CentOS 7.4 / kernel 3.10.0-693 / glibc 2.17: all checks passed', flush=True)
                    return
            if active and not sent and b'TUIVORY' in captured[started:]:
                # Let the initial frame complete before quitting once.
                time.sleep(.3)
                os.write(master, b'\x11')
                sent = True
            if process.poll() is not None:
                break
        raise RuntimeError('Guest stopped or timed out; inspect ' + str(logfile))
    finally:
        logfile.write_bytes(captured)
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        os.close(master)


def named(items):
    result = {}
    for value in items:
        name, path = value.split('=', 1)
        if not re.fullmatch(r'[a-zA-Z0-9_-]+', name) or name in result:
            raise ValueError('Invalid or duplicate binary name: ' + name)
        result[name] = Path(path).resolve()
        inspect(result[name], 'x86_64')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kernel', type=Path, required=True, help=KERNEL_URL)
    parser.add_argument('--qemu', default='qemu-system-x86_64')
    parser.add_argument('--bios', type=Path)
    parser.add_argument('--qemu-data', type=Path)
    parser.add_argument('--binary', action='append', default=[], metavar='NAME=PATH')
    parser.add_argument('--consumer', action='append', default=[], metavar='NAME=PATH')
    parser.add_argument('--output', type=Path, default=Path('/tmp/tuivory-centos74.log'))
    parser.add_argument('--timeout', type=int, default=240)
    args = parser.parse_args()
    if hashlib.sha256(args.kernel.read_bytes()).hexdigest() != KERNEL_SHA256:
        raise SystemExit('Unexpected CentOS 7.4 kernel SHA256')
    binaries, consumers = named(args.binary), named(args.consumer)
    if not binaries or set(binaries) & set(consumers):
        raise SystemExit('Provide TUI binaries and distinct consumer names')
    with tempfile.TemporaryDirectory(prefix='tuivory-centos74-') as temporary:
        base = Path(temporary)
        container = subprocess.check_output(['docker', 'create', '--platform', 'linux/amd64', IMAGE,
                                             '/bin/bash'], text=True).strip()
        try:
            subprocess.run(['docker', 'export', '-o', str(base / 'rootfs.tar'), container], check=True)
        finally:
            subprocess.run(['docker', 'rm', container], check=True, stdout=subprocess.DEVNULL)
        print('Preparing pinned CentOS 7.4 initramfs', flush=True)
        initramfs(base / 'rootfs.tar', base / 'initrd.gz', binaries, consumers)
        command = [args.qemu, '-machine', 'pc,accel=tcg', '-cpu', 'qemu64', '-m', '1536',
                   '-nodefaults', '-display', 'none', '-serial', 'stdio', '-monitor', 'none',
                   '-nic', 'none', '-no-reboot', '-kernel', str(args.kernel.resolve()),
                   '-initrd', str(base / 'initrd.gz'), '-append',
                   'console=ttyS0 rdinit=/init panic=-1 loglevel=4']
        if args.bios:
            command += ['-bios', str(args.bios.resolve())]
        if args.qemu_data:
            command += ['-L', str(args.qemu_data.resolve())]
        print('Booting isolated legacy kernel: ' + shlex.join(command), flush=True)
        boot(command, args.output, binaries, consumers, args.timeout)
        result = {'image': IMAGE, 'kernel': '3.10.0-693.el7.x86_64',
                  'kernel_sha256': KERNEL_SHA256, 'glibc': '2.17-196.el7.x86_64',
                  'result': 'passed', 'languages': ['ko', 'en'],
                  'binaries_sha256': {name: hashlib.sha256(path.read_bytes()).hexdigest()
                                      for name, path in {**binaries, **consumers}.items()}}
        args.output.with_suffix('.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
