#!/usr/bin/env python3
"""Build static musl Rust playgrounds using rustup's bundled linker."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
from check_static_elf import inspect

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {'arm64': 'aarch64-unknown-linux-musl', 'x86_64': 'x86_64-unknown-linux-musl'}


def linker_environment(target):
    sysroot = Path(subprocess.check_output(['rustc', '--print', 'sysroot'], text=True).strip())
    version = subprocess.check_output(['rustc', '-vV'], text=True)
    host = next(line.split(': ', 1)[1] for line in version.splitlines() if line.startswith('host: '))
    linker = sysroot / 'lib/rustlib' / host / 'bin/rust-lld'
    if not linker.is_file():
        raise SystemExit(f'Bundled rust-lld is required: {linker}')
    env = dict(os.environ)
    env['CARGO_TARGET_' + target.upper().replace('-', '_') + '_LINKER'] = str(linker)
    return env


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--arch', choices=TARGETS, default='arm64')
    parser.add_argument('--examples', action='store_true', help='also build component validation examples')
    args = parser.parse_args()
    target = TARGETS[args.arch]
    directory = Path(os.environ.get('CARGO_TARGET_DIR', 'target'))
    if not directory.is_absolute():
        directory = ROOT / 'rust' / directory
    env = linker_environment(target)
    command = ['cargo', 'build', '--manifest-path', str(ROOT / 'rust/Cargo.toml'), '--locked',
               '--release', '--target', target, '--target-dir', str(directory), '--features', 'playground']
    command += ['--examples'] if args.examples else ['--example', 'playground']
    subprocess.run(command, env=env, check=True)
    names = ('playground', 'tree', 'workspace', 'focus', 'catalog', 'tokens', 'menu', 'controls') if args.examples else ('playground',)
    for name in names:
        inspect(directory / target / 'release/examples' / name, args.arch)
    destination = ROOT / 'bin/rust' / f'tuivory-linux-{args.arch}'
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(directory / target / 'release/examples/playground', destination)
    print(f'Static {target}: {destination}')


if __name__ == '__main__':
    main()
