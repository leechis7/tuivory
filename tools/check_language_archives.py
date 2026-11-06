#!/usr/bin/env python3
"""Check actual unreleased SDK/package archives outside the source tree."""
from pathlib import Path
import hashlib,json,os,subprocess,tarfile,tempfile,zipfile
from check_languages import ROOT,run
from check_language_collections import source

def main():
 out=ROOT/'.cache/packages/languages'
 manifest=json.loads((out/'UNRELEASED-MANIFEST.json').read_text())
 for name,entry in manifest['assets'].items():
  artifact=out/name
  assert hashlib.sha256(artifact.read_bytes()).hexdigest()==entry['sha256'],name
  assert artifact.stat().st_size==entry['size'],name
 for lang in ['c','cpp']:
  names=[name for name in manifest['assets']if name.startswith('tuivory-'+lang+'-')and name.endswith('.tar.gz')];assert len(names)==1
  with tempfile.TemporaryDirectory(prefix='tuivory-sdk-')as d:
   base=Path(d)
   with tarfile.open(out/names[0])as tar:tar.extractall(base,filter='data')
   sdk=next(base.iterdir());assert (sdk/'CASEFOLD-LICENSE').read_bytes()==(ROOT/'design/casefold.LICENSE').read_bytes()
   src=base/('consumer.c'if lang=='c'else'consumer.cpp');src.write_text(source(lang))
   args=['cc'if lang=='c'else'c++','-std=c11'if lang=='c'else'-std=c++17','-static','-Wall','-Wextra','-Werror','-I',sdk/'include',src]
   if lang=='c':args+=[sdk/'lib/libtuivory.a']
   args+=['-o',base/'consumer'];run(args,base);run([base/'consumer'],base)
 jar_name=next(name for name in manifest['assets']if name.endswith('.jar'))
 with zipfile.ZipFile(out/jar_name)as jar:
  names=jar.namelist();assert not any(n.endswith(('.so','.dll','.dylib'))for n in names)
  assert not any('ComponentsTest'in n or 'CollectionCases'in n for n in names)
  assert jar.read('CASEFOLD-LICENSE')==(ROOT/'design/casefold.LICENSE').read_bytes()
  assert 'io/tuivory/FoldData.class'in names
 with tempfile.TemporaryDirectory(prefix='tuivory-jar-')as d:
  base=Path(d);src=base/'CollectionCases.java';src.write_text(source('java'));jar=out/jar_name
  run(['javac','--release','17','-encoding','UTF-8','-Xlint:all','-Werror','-cp',jar,src],base);run(['java','-cp',str(jar)+os.pathsep+str(base),'CollectionCases'],base)
 wheel_name=next(name for name in manifest['assets']if name.endswith('.whl'))
 with zipfile.ZipFile(out/wheel_name)as wheel:
  assert any(n.endswith('/licenses/CASEFOLD-LICENSE')for n in wheel.namelist())
  assert 'tuivory/casefold.json'in wheel.namelist()
 npm_name=next(name for name in manifest['assets']if name.endswith('.tgz'))
 with tarfile.open(out/npm_name)as npm:
  assert 'package/CASEFOLD-LICENSE'in npm.getnames()
  assert 'package/dist/casefold.json'in npm.getnames()
 print('Six actual archive hashes/licenses, isolated static C/C++ SDK consumers, pure Java JAR and runtime package data passed')
if __name__=='__main__':main()
