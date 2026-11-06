#!/usr/bin/env python3
"""Build one independent native-host C/C++ example or a pure-Java JAR."""
from pathlib import Path
import argparse
import platform
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]

def run(cmd):subprocess.run(list(map(str,cmd)),cwd=ROOT,check=True)

def build(language):
    cache=ROOT/'.cache/native'/language
    cache.mkdir(parents=True,exist_ok=True)
    if language=='java':
        classes=cache/'classes'
        if classes.exists():shutil.rmtree(classes)
        classes.mkdir()
        sources=sorted((ROOT/'java/src/main/java').rglob('*.java'))+sorted((ROOT/'java/examples').rglob('*.java'))
        run(['javac','--release','17','-encoding','UTF-8','-Xlint:all','-Werror','-d',classes,*sources])
        out=ROOT/'.cache/packages/java'/f'tuivory-{(ROOT/"VERSION").read_text().strip()}.jar'
        out.parent.mkdir(parents=True,exist_ok=True)
        run(['jar','--create','--file',out,'--main-class','io.tuivory.examples.Catalog','-C',classes,'.','-C',ROOT/'java','CASEFOLD-LICENSE','-C',ROOT/'java','UNICODE-LICENSE','-C',ROOT,'LICENSE','-C',ROOT/'java','NOTICE.md','-C',ROOT/'java','NOTICE.en.md'])
        return out
    if platform.system()!='Linux':raise SystemExit('Default native example builds require a Linux host')
    arch={'aarch64':'arm64','arm64':'arm64','x86_64':'x86_64','amd64':'x86_64'}.get(platform.machine().lower())
    if arch is None:raise SystemExit('Unsupported native host architecture')
    out=ROOT/'bin'/language/f'tuivory-linux-{arch}'
    out.parent.mkdir(parents=True,exist_ok=True)
    if language=='c':
        run(['cc','-O2','-std=c11','-Wall','-Wextra','-Werror','-I',ROOT/'c/include','-c',ROOT/'c/src/tuivory.c','-o',cache/'tuivory.o'])
        run(['ar','rcs',cache/'libtuivory.a',cache/'tuivory.o'])
        run(['cc','-static','-O2','-std=c11','-Wall','-Wextra','-Werror','-I',ROOT/'c/include',ROOT/'c/examples/catalog.c',cache/'libtuivory.a','-o',out])
    else:
        run(['c++','-static','-O2','-std=c++17','-Wall','-Wextra','-Werror','-Wno-missing-field-initializers','-I',ROOT/'cpp/include',ROOT/'cpp/examples/catalog.cpp','-o',out])
    run([sys.executable,ROOT/'tools/check_static_elf.py','--arch',arch,out])
    return out

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('language',choices=['c','cpp','java'])
    print(build(parser.parse_args().language))
