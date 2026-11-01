#!/usr/bin/env python3
"""Package one unified executable per language, built only for this host."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile

from build_examples import ROOT, host_arch
from check_static_elf import inspect


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--crate', action='store_true', help='also verify and package the Rust crate')
    args = parser.parse_args()
    os.chdir(ROOT)
    assert not subprocess.check_output(['git', 'status', '--porcelain'], text=True).strip(), 'Release packaging requires a clean checkout'
    version = (ROOT / 'VERSION').read_text().strip()
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    arch = host_arch()
    out = ROOT / '.cache/releases' / ('v' + version)
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run(['make', 'build', 'build-rust'], check=True)
    result = {'version': version, 'source_commit': commit, 'source_uncommitted': False, 'architecture': arch, 'binaries': {}, 'assets': {}}
    for language in ['go', 'rust']:
        binary = ROOT / 'bin' / language / f'tuivory-linux-{arch}'
        inspect(binary, arch)
        if language == 'go':
            metadata = subprocess.check_output(['go', 'version', '-m', str(binary)], text=True)
            assert 'vcs.revision=' + commit in metadata and 'vcs.modified=false' in metadata
        result['binaries'][f'{language}/{binary.name}'] = {'sha256': sha(binary), 'architecture': arch, 'static_elf': True}
        name = f'tuivory-{language}-v{version}-linux-{arch}'
        with tempfile.TemporaryDirectory(dir=out) as temporary:
            stage = Path(temporary) / name
            destination = stage / 'bin' / language / binary.name
            destination.parent.mkdir(parents=True)
            shutil.copy2(binary, destination)
            for file in ['LICENSE', 'VERSION']:
                shutil.copy2(ROOT / file, stage / file)
            for file in ['NOTICE.md', 'NOTICE.en.md']:
                shutil.copy2(ROOT / language / file, stage / file)
            for english in [False, True]:
                suffix = '.en' if english else ''
                title = '[한국어 (default)](README.md) · **English**' if english else '**한국어 (기본)** · [English](README.en.md)'
                body = 'One static executable contains all demos. No separate runtime or shared libraries are needed.' if english else '정적 실행파일 하나에 모든 예제를 포함합니다. 별도 런타임·공유 라이브러리가 필요 없습니다.'
                commands = f'./bin/{language}/{binary.name}'
                (stage / f'README{suffix}.md').write_text(f'# Tuivory {version} — {language} / {arch}\n\n{title}\n\n{body}\n\n```sh\n{commands} --list\n{commands} --demo tree --lang {"en" if english else "ko"}\n{commands} --demo syntax --lang {"en" if english else "ko"}\n```\n\n[Guide](https://github.com/leechis7/tuivory/blob/go/v{version}/docs/examples{suffix}.md)\n')
            archive = out / (name + '.tar.gz')
            with tarfile.open(archive, 'w:gz') as tar:
                tar.add(stage, arcname=name)
        result['assets'][archive.name] = {'sha256': sha(archive), 'size': archive.stat().st_size}
    if args.crate:
        subprocess.run(['cargo', 'package', '--manifest-path', 'rust/Cargo.toml', '--locked'], check=True)
        metadata = json.loads(subprocess.check_output(['cargo', 'metadata', '--manifest-path', 'rust/Cargo.toml', '--no-deps', '--format-version', '1'], text=True))
        crate = Path(metadata['target_directory']) / 'package' / f'tuivory-{version}.crate'
        with tarfile.open(crate) as tar:
            vcs = json.load(tar.extractfile(f'tuivory-{version}/.cargo_vcs_info.json'))
            assert vcs['git']['sha1'] == commit and not vcs['git'].get('dirty', False)
        shutil.copy2(crate, out / crate.name)
        result['assets'][crate.name] = {'sha256': sha(crate), 'size': crate.stat().st_size}
    manifest = out / f'BUILD-MANIFEST-linux-{arch}.json'
    manifest.write_text(json.dumps(result, indent=2) + '\n')
    print(manifest)


if __name__ == '__main__':
    main()
