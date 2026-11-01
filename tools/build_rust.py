#!/usr/bin/env python3
"""Build static musl Rust playgrounds using rustup's bundled linker."""
import argparse
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


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
    parser = argparse.ArgumentParser(description='Build the single Rust showcase for the Linux host.')
    parser.parse_args()
    subprocess.run([__import__('sys').executable, str(ROOT / 'tools/build_examples.py'), 'rust'], check=True)


if __name__ == '__main__':
    main()
