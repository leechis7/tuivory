#!/usr/bin/env python3
"""Check actual unreleased SDK/package archives outside the source tree."""
from pathlib import Path
import hashlib,json,os,subprocess,tarfile,tempfile,zipfile
from check_languages import ROOT,run
from check_language_collections import source
from check_language_menu import source as menu_source
from check_language_feedback import source as feedback_source
from check_language_layout import source as layout_source
from check_language_canvas_copy import source as copy_source
from check_language_containers import source as container_source
from check_language_surfaces import source as surface_source,validate_output as validate_surface_output

from check_language_popups import source as popup_source,validate_output as validate_popup_output
from check_language_dialogs import source as dialog_source,validate_output as validate_dialog_output

from check_language_documents import source as document_source,validate_output as validate_document_output

from check_language_syntax import source as syntax_source,validate_output as validate_syntax_output

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
   example=next((sdk/'bin'/lang).iterdir());snapshot=subprocess.check_output([example,'--demo','context-menu','--lang','en','--snapshot'],cwd=base);assert b'Context menu'in snapshot
   src=base/('consumer.c'if lang=='c'else'consumer.cpp');src.write_text(source(lang))
   args=['cc'if lang=='c'else'c++','-std=c11'if lang=='c'else'-std=c++17','-static','-Wall','-Wextra','-Werror','-I',sdk/'include',src]
   if lang=='c':args+=[sdk/'lib/libtuivory.a']
   args+=['-o',base/'consumer'];run(args,base);run([base/'consumer'],base)
   src.write_text(menu_source(lang));run(args,base);run([base/'consumer'],base)
   src.write_text(feedback_source(lang));run(args,base);run([base/'consumer'],base)
   src.write_text(layout_source(lang));run(args,base);run([base/'consumer'],base)
   src.write_text(copy_source(lang));run(args,base);run([base/'consumer'],base)
   src.write_text(container_source(lang));run(args,base);run([base/'consumer'],base)
   src.write_text(surface_source(lang));run(args,base);validate_surface_output(subprocess.check_output([base/'consumer'],cwd=base,text=True))
   for make,validate in [(popup_source,validate_popup_output),(dialog_source,validate_dialog_output),(document_source,validate_document_output),(syntax_source,validate_syntax_output)]:
    src.write_text(make(lang));run(args,base);validate(subprocess.check_output([base/'consumer'],cwd=base,text=True))
   for demo,label in [('shadow',b'Context menu'),('dialog',b'Reconnect'),('document',b'Document viewer/editor'),('syntax',b'SELECT COUNT')]:
    assert label in subprocess.check_output([example,'--demo',demo,'--lang','en','--snapshot'],cwd=base)
   snapshot=subprocess.check_output([example,'--demo','surface','--lang','en','--snapshot'],cwd=base);assert b'Body on surface'in snapshot
   snapshot=subprocess.check_output([example,'--demo','container','--lang','en','--snapshot'],cwd=base);assert b'Navigator'in snapshot
   snapshot=subprocess.check_output([example,'--demo','layout','--lang','en','--snapshot'],cwd=base);assert b'Items'in snapshot
   snapshot=subprocess.check_output([example,'--demo','feedback','--lang','en','--snapshot'],cwd=base);assert b'40%'in snapshot
 jar_name=next(name for name in manifest['assets']if name.endswith('.jar'))
 with zipfile.ZipFile(out/jar_name)as jar:
  names=jar.namelist();assert not any(n.endswith(('.so','.dll','.dylib'))for n in names)
  assert not any('ComponentsTest'in n or 'CollectionCases'in n or 'MenuCases'in n or 'FeedbackCases'in n or 'LayoutCases'in n or 'CanvasCopyCases'in n or 'ContainerCases'in n or 'SurfaceCases'in n or 'PopupCases'in n or 'DialogCases'in n or 'DocumentCases'in n or 'SyntaxCases'in n for n in names)
  assert jar.read('CASEFOLD-LICENSE')==(ROOT/'design/casefold.LICENSE').read_bytes()
  assert jar.read('NOTICE.md')==(ROOT/'java/NOTICE.md').read_bytes()and jar.read('NOTICE.en.md')==(ROOT/'java/NOTICE.en.md').read_bytes()
  assert 'io/tuivory/FoldData.class'in names
 with tempfile.TemporaryDirectory(prefix='tuivory-jar-')as d:
  base=Path(d);src=base/'CollectionCases.java';src.write_text(source('java'));jar=out/jar_name
  run(['javac','--release','17','-encoding','UTF-8','-Xlint:all','-Werror','-cp',jar,src],base);run(['java','-cp',str(jar)+os.pathsep+str(base),'CollectionCases'],base)
  src=base/'MenuCases.java';src.write_text(menu_source('java'))
  run(['javac','--release','17','-encoding','UTF-8','-Xlint:all','-Werror','-cp',jar,src],base);run(['java','-cp',str(jar)+os.pathsep+str(base),'MenuCases'],base)
  snapshot=subprocess.check_output(['java','-jar',jar,'--demo','context-menu','--lang','en','--snapshot'],cwd=base);assert b'Context menu'in snapshot
  src=base/'FeedbackCases.java';src.write_text(feedback_source('java'))
  run(['javac','--release','17','-encoding','UTF-8','-Xlint:all','-Werror','-cp',jar,src],base);run(['java','-cp',str(jar)+os.pathsep+str(base),'FeedbackCases'],base)
  snapshot=subprocess.check_output(['java','-jar',jar,'--demo','feedback','--lang','en','--snapshot'],cwd=base);assert b'40%'in snapshot
  src=base/'LayoutCases.java';src.write_text(layout_source('java'))
  run(['javac','--release','17','-encoding','UTF-8','-Xlint:all','-Werror','-cp',jar,src],base);run(['java','-cp',str(jar)+os.pathsep+str(base),'LayoutCases'],base)
  snapshot=subprocess.check_output(['java','-jar',jar,'--demo','layout','--lang','en','--snapshot'],cwd=base);assert b'Items'in snapshot
  for name,make in [('CanvasCopyCases',copy_source),('ContainerCases',container_source)]:
   src=base/(name+'.java');src.write_text(make('java'))
   run(['javac','--release','17','-encoding','UTF-8','-Xlint:all','-Werror','-cp',jar,src],base);run(['java','-cp',str(jar)+os.pathsep+str(base),name],base)
  snapshot=subprocess.check_output(['java','-jar',jar,'--demo','container','--lang','en','--snapshot'],cwd=base);assert b'Navigator'in snapshot
  src=base/'SurfaceCases.java';src.write_text(surface_source('java'))
  run(['javac','--release','17','-encoding','UTF-8','-Xlint:all','-Werror','-cp',jar,src],base);validate_surface_output(subprocess.check_output(['java','-cp',str(jar)+os.pathsep+str(base),'SurfaceCases'],cwd=base,text=True))
  for name,make,validate in [('PopupCases',popup_source,validate_popup_output),('DialogCases',dialog_source,validate_dialog_output),('DocumentCases',document_source,validate_document_output),('SyntaxCases',syntax_source,validate_syntax_output)]:
   src=base/(name+'.java');src.write_text(make('java'));run(['javac','--release','17','-encoding','UTF-8','-Xlint:all','-Werror','-cp',jar,src],base);validate(subprocess.check_output(['java','-cp',str(jar)+os.pathsep+str(base),name],cwd=base,text=True))
  for demo,label in [('shadow',b'Context menu'),('dialog',b'Reconnect'),('document',b'Document viewer/editor'),('syntax',b'SELECT COUNT')]:
   assert label in subprocess.check_output(['java','-jar',jar,'--demo',demo,'--lang','en','--snapshot'],cwd=base)
  snapshot=subprocess.check_output(['java','-jar',jar,'--demo','surface','--lang','en','--snapshot'],cwd=base);assert b'Body on surface'in snapshot
 wheel_name=next(name for name in manifest['assets']if name.endswith('.whl'))
 with zipfile.ZipFile(out/wheel_name)as wheel:
  assert any(n.endswith('/licenses/CASEFOLD-LICENSE')for n in wheel.namelist())
  assert 'tuivory/casefold.json'in wheel.namelist()
  assert 'tuivory/sql-syntax-words.json'in wheel.namelist()and'tuivory/syntax-unicode.json'in wheel.namelist()
 npm_name=next(name for name in manifest['assets']if name.endswith('.tgz'))
 with tarfile.open(out/npm_name)as npm:
  assert 'package/CASEFOLD-LICENSE'in npm.getnames()
  assert 'package/dist/casefold.json'in npm.getnames()
  assert 'package/dist/sql-syntax-words.json'in npm.getnames()and'package/dist/syntax-unicode.json'in npm.getnames()
 print('Six actual archive hashes/licenses, isolated static C/C++ SDK consumers, pure Java JAR and runtime package data passed')
if __name__=='__main__':main()
