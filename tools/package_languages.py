#!/usr/bin/env python3
"""Assemble independent-language preview or GitHub Release packages."""
import argparse
from pathlib import Path
import hashlib
import json
import platform
import shutil
import subprocess
import tarfile
import tempfile

ROOT=Path(__file__).resolve().parents[1]

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', action='store_true', help='package a clean release checkout')
    parser.add_argument('--native-only', action='store_true', help='include only C and C++ SDKs')
    args=parser.parse_args()
    dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    if args.release and dirty:
        parser.error('release packaging requires a clean checkout')
    version=(ROOT/'VERSION').read_text().strip()
    arch={'aarch64':'arm64','x86_64':'x86_64'}[platform.machine()]
    out=ROOT/('.cache/releases/v'+version if args.release else '.cache/packages/languages')
    out.mkdir(parents=True,exist_ok=True)
    assets={}
    # Binaries/libraries have already passed build and isolated-consumer checks.
    for language in ['c','cpp']:
        name=f'tuivory-{language}-{version}-linux-{arch}'
        with tempfile.TemporaryDirectory(dir=out)as directory:
            stage=Path(directory)/name;stage.mkdir()
            shutil.copytree(ROOT/language/'include',stage/'include')
            if language=='c':
                (stage/'lib').mkdir();shutil.copy2(ROOT/'.cache/native/c/libtuivory.a',stage/'lib/libtuivory.a')
            destination=stage/'bin'/language;destination.mkdir(parents=True)
            shutil.copy2(ROOT/'bin'/language/f'tuivory-linux-{arch}',destination)
            for file in ['README.md','README.en.md','NOTICE.md','NOTICE.en.md','LICENSE','UNICODE-LICENSE','CASEFOLD-LICENSE']:shutil.copy2(ROOT/language/file,stage/file)
            if not args.release:
                (stage/'UNRELEASED.txt').write_text('Unreleased local preview only. Check manifest for source commit/worktree state; not part of the existing public release.\n')
            archive=out/(name+'.tar.gz')
            with tarfile.open(archive,'w:gz')as tar:tar.add(stage,arcname=name)
            assets[archive.name]={'sha256':sha(archive),'size':archive.stat().st_size}
    if not args.native_only:
        for directory,pattern in [('python',f'tuivory-{version}-py3-none-any.whl'),('python',f'tuivory-{version}.tar.gz'),('javascript',f'tuivory-{version}.tgz'),('java',f'tuivory-{version}.jar')]:
            source=ROOT/'.cache/packages'/directory/pattern
            shutil.copy2(source,out/source.name);assets[source.name]={'sha256':sha(source),'size':source.stat().st_size}
    manifest={'version':version,'status':'unreleased local preview','scope':'independent language catalog preview; verified milestones: Tree/workspace/Text/forms/focus/collections/menu/feedback/spacing-stacks-supporting/containers-cell-copy/surfaces/popup-dialog/documents/syntax/grid/drag/terminal; remaining catalog in progress','source_base':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'source_uncommitted':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()),'architecture':arch,'assets':assets,'publication':'not performed','centos':'not run per user instruction'}
    if args.release:
        manifest.update(status='release build', scope='independent language packages', publication='build only')
        (out/f'LANGUAGE-BUILD-MANIFEST-linux-{arch}.json').write_text(json.dumps(manifest,indent=2)+'\n')
        print(out)
        return
    (out/'UNRELEASED-MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (out/'SHA256SUMS').write_text(''.join(f'{sha(out/name)}  {name}\n'for name in sorted([*assets,'UNRELEASED-MANIFEST.json'])))
    print(out)

if __name__=='__main__':main()
