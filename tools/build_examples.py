#!/usr/bin/env python3
"""Build one static showcase executable for one language and the Linux host."""
import argparse
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile

from build_rust import linker_environment
from check_static_elf import inspect

ROOT = Path(__file__).resolve().parents[1]


def host_arch():
    if platform.system() != 'Linux':
        raise SystemExit('The static example builder currently supports Linux hosts only.')
    machine = platform.machine().lower()
    arch = {'aarch64': 'arm64', 'arm64': 'arm64', 'amd64': 'x86_64', 'x86_64': 'x86_64'}.get(machine)
    if arch is None:
        raise SystemExit(f'Unsupported host architecture: {machine}')
    return arch


def build(language):
    arch = host_arch()
    destination = ROOT / 'bin' / language
    destination.mkdir(parents=True, exist_ok=True)
    scratch = ROOT / '.cache/validation/build-host'
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch) as temporary:
        binary = Path(temporary) / f'tuivory-linux-{arch}'
        if language == 'go':
            env = dict(os.environ, CGO_ENABLED='0', GOOS='linux', GOARCH='arm64' if arch == 'arm64' else 'amd64')
            subprocess.run(['go', 'build', '-C', str(ROOT / 'go'), '-trimpath', '-o', str(binary), './cmd/tuivory'], env=env, check=True)
        else:
            target = {'arm64': 'aarch64-unknown-linux-musl', 'x86_64': 'x86_64-unknown-linux-musl'}[arch]
            directory = Path(os.environ.get('CARGO_TARGET_DIR', str(ROOT / '.cache/rust')))
            if not directory.is_absolute():
                directory = ROOT / 'rust' / directory
            subprocess.run(['cargo', 'build', '--manifest-path', str(ROOT / 'rust/Cargo.toml'), '--locked', '--release', '--target', target, '--target-dir', str(directory), '--features', 'playground,syntax-sql', '--example', 'showcase'], env=linker_environment(target), check=True)
            shutil.copy2(directory / target / 'release/examples/showcase', binary)
        inspect(binary, arch)
        final = destination / binary.name
        os.replace(binary, final)
    # Retire only known example outputs, after the replacement passes ELF checks.
    names = {'tuivory', 'catalog', 'controls', 'focus', 'menu', 'syntax', 'tree', 'workspace'}
    names |= {'tuivory-' + name for name in names if name != 'tuivory'}
    for old in destination.iterdir():
        if old != final and old.is_file() and any(old.name == f'{name}-linux-{suffix}' for name in names for suffix in ['arm64', 'x86_64']):
            old.unlink()
    print(f'Static {language} showcase ({arch}): {final}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('language', choices=['go', 'rust'])
    build(parser.parse_args().language)
