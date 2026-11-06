#!/usr/bin/env python3
"""Assemble explicitly unreleased independent-language preview packages locally."""
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
    version=(ROOT/'VERSION').read_text().strip()
    arch={'aarch64':'arm64','x86_64':'x86_64'}[platform.machine()]
    out=ROOT/'.cache/packages/languages';out.mkdir(parents=True,exist_ok=True)
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
            (stage/'UNRELEASED.txt').write_text('Unreleased local preview only. Check manifest for source commit/worktree state; not part of the existing public release.\n')
            archive=out/(name+'.tar.gz')
            with tarfile.open(archive,'w:gz')as tar:tar.add(stage,arcname=name)
            assets[archive.name]={'sha256':sha(archive),'size':archive.stat().st_size}
    for directory,pattern in [('python',f'tuivory-{version}-py3-none-any.whl'),('python',f'tuivory-{version}.tar.gz'),('javascript',f'tuivory-{version}.tgz'),('java',f'tuivory-{version}.jar')]:
        source=ROOT/'.cache/packages'/directory/pattern
        shutil.copy2(source,out/source.name);assets[source.name]={'sha256':sha(source),'size':source.stat().st_size}
    manifest={'version':version,'status':'unreleased local preview','scope':'independent language catalog preview; verified milestones: Tree/workspace/Text/forms/focus/collections/menu/feedback/spacing-stacks-supporting/containers-cell-copy; remaining catalog in progress','source_base':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'source_uncommitted':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()),'architecture':arch,'assets':assets,'publication':'not performed','centos':'not run per user instruction'}
    (out/'UNRELEASED-MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (out/'SHA256SUMS').write_text(''.join(f'{sha(out/name)}  {name}\n'for name in sorted([*assets,'UNRELEASED-MANIFEST.json'])))
    print(out)

if __name__=='__main__':main()
