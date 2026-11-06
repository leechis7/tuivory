#!/usr/bin/env python3
"""Install local wheel/npm archives into isolated external runtime consumers."""
from pathlib import Path
import argparse,json,os,shutil,subprocess,tempfile,sys
r=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--python',default=sys.executable)
parser.add_argument('--typescript-compiler',type=Path,default=r/'javascript/node_modules/typescript/bin/tsc')
args=parser.parse_args()
python=str(Path(args.python).resolve()) if "/" in args.python else (shutil.which(args.python) or args.python)
version=(r/'VERSION').read_text().strip()
def run(cmd,cwd,env=None):subprocess.run(list(map(str,cmd)),cwd=cwd,env=env,check=True)
with tempfile.TemporaryDirectory(prefix='tuivory-python-')as directory:
 b=Path(directory);run([python,'-m','venv',b/'venv'],b);p=b/'venv/bin/python'
 run([p,'-m','pip','install','--no-index','--find-links',r/'.cache/packages/python/deps',r/'.cache/packages/python'/f'tuivory-{version}-py3-none-any.whl'],b)
 (b/'consumer.py').write_text('''import tuivory as ui
p=ui.Palette("light","8")
t=ui.Tree([ui.Node("root","Workspace"),ui.Node("child","한글 👩‍💻",parent="root")])
assert t.handle("right",3).kind=="expand"
assert t.handle("down",3).id=="child"
c=ui.Canvas(30,4,p);t.draw(c,ui.Rect(0,0,30,4));assert "한글" in "".join(c.lines())
assert ui.cells("한글 👩‍💻")==7
tabs=ui.Tabs([ui.Tab("a","Overview"),ui.Tab("b","Draft",closable=True)])
assert tabs.handle("next").id=="b" and tabs.handle("close").kind=="close"
assert ui.path_runs([("r","root"),("f","folder"),("c","현재.sql")],15).text=="... / 현재.sql"
assert ui.status_line([ui.StatusItem("e","Failure","error",100),ui.StatusItem("h","F1 Help","hint",1)],10).omitted==1
assert ui.Split(3,4,7).layout(5).compact
''')
 run([p,'-I',b/'consumer.py'],b)
 run([p,'-I','-m','tuivory','--snapshot','--demo','tree','--lang','en'],b)
 print('Independent Python wheel: isolated external venv install/import/Tree/example passed')
with tempfile.TemporaryDirectory(prefix='tuivory-javascript-')as directory:
 b=Path(directory);(b/'package.json').write_text('{"type":"module"}\n')
 env=dict(os.environ,NPM_CONFIG_CACHE=str(r/'.cache/npm'))
 run(['npm','install','--offline','--ignore-scripts','--no-audit','--no-fund',r/'.cache/packages/javascript'/f'tuivory-{version}.tgz'],b,env)
 source='''import * as ui from "tuivory";
const p=new ui.Palette("light","8");const t=new ui.Tree([{id:"root",name:"Workspace"},{id:"child",parent:"root",name:"한글 👩‍💻"}]);
if(t.handle("right",3).kind!=="expand"||t.handle("down",3).id!=="child")throw new Error("tree");
const c=new ui.Canvas(30,4,p);t.draw(c,ui.rect(0,0,30,4));if(!c.lines().join("").includes("한글"))throw new Error("render");
if(ui.cells("한글 👩‍💻")!==7)throw new Error("width");
const tabs=new ui.Tabs([{id:"a",title:"Overview"},{id:"b",title:"Draft",closable:true}]);
if(tabs.handle("next").id!=="b"||tabs.handle("close").kind!=="close")throw new Error("tabs");
if(ui.pathRuns([{id:"r",label:"root"},{id:"f",label:"folder"},{id:"c",label:"현재.sql"}],15).text!=="... / 현재.sql")throw new Error("path");
if(!new ui.Split(3,4,7).layout(5).compact)throw new Error("split");
'''
 (b/'consumer.mjs').write_text(source);(b/'consumer.ts').write_text(source)
 run(['node','consumer.mjs'],b)
 run(['node',args.typescript_compiler.resolve(),'--strict','--module','NodeNext','--target','ES2022','--noEmit','consumer.ts'],b)
 run(['node',b/'node_modules/tuivory/examples/catalog.mjs','--snapshot','--lang','en'],b)
 print('Independent npm package: isolated external JS import/runtime, TS declarations and example passed')
