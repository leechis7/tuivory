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
e=ui.Text("a");e.handle("insert","́");assert e.cursor==1;e.handle("backspace");assert e.value=="";e.handle("undo");assert e.value=="á"
f=ui.Form([ui.Field("p",kind="password",value="secret")]);assert f.fields[0].value=="******"
s=ui.Form([ui.Field("s",kind="select",options=[ui.FormOption("a"),ui.FormOption("b")])]);s.handle("activate");s.handle("down");assert s.fields[0].choice=="";s.handle("activate");assert s.fields[0].choice=="b"
focus=ui.Focus("root",[ui.FocusTarget("open")]);focus.open("popup",[]);assert focus.route("root").blocked and not focus.route().blocked;assert focus.request_close().id=="popup";focus.close("popup");assert focus.focused=="open"
assert ui.fold("Straße Σςσ")=="strasse σσσ"
l=ui.List([ui.Item("de","Straße")]);assert l.set_query("STRASSE").kind=="query" and l.focused=="de"
picker=ui.SearchPicker([ui.Item("rust","Rust")]);picker.handle("open");picker.handle("insert","RUST");assert picker.value=="";assert picker.handle("activate").id=="rust" and picker.value=="rust"
m=ui.Menu([ui.MenuItem("file","File"),ui.MenuItem("run","Run",parent="file")]);m.open("file","editor");assert m.draw_popup(c,ui.Rect(0,0,30,4),"Menu").width==26;assert m.handle("activate").return_id=="editor"
q=ui.NoticeQueue(2);q.push(ui.Notice("error","Failure","error",actions=[ui.NoticeAction("off","Unavailable",True),ui.NoticeAction("retry","Retry")]));assert q.handle("activate").action=="retry" and q.handle("dismiss").kind=="dismiss" and len(q.items)==1;assert len(q.visible(100))==1
p=ui.Progress("job",current=40,total=100,cancellable=True);assert p.request_cancel().kind=="cancel" and "40%"in p.layout(40)[1].text;assert ui.DataState("ready","Ready").layout(10)[0].role=="body"
from importlib.metadata import distribution
assert any(str(p).endswith("CASEFOLD-LICENSE")for p in distribution("tuivory").files)
''')
 run([p,'-I',b/'consumer.py'],b)
 run([p,'-I','-m','tuivory','--snapshot','--demo','tree','--lang','en'],b)
 run([p,'-I','-m','tuivory','--snapshot','--demo','context-menu','--lang','en'],b)
 run([p,'-I','-m','tuivory','--snapshot','--demo','feedback','--lang','en'],b)
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
const e=new ui.Text("a");e.handle("insert","́");if(e.cursor!==1)throw new Error("grapheme cursor");e.handle("backspace");if(e.value!=="")throw new Error("grapheme erase");
const f=new ui.Form([{id:"p",kind:"password",value:"secret"}]);if(f.fields[0].value!=="******")throw new Error("password");
const s=new ui.Form([{id:"s",kind:"select",options:[{id:"a"},{id:"b"}]}]);s.handle("activate");s.handle("down");if(s.fields[0].choice)throw new Error("pending");s.handle("activate");if(s.fields[0].choice!=="b")throw new Error("choice");
const focus=new ui.Focus("root",[{id:"open"}]);focus.open("popup",[]);if(!focus.route("root").blocked||focus.route().blocked||focus.requestClose()?.id!=="popup")throw new Error("focus routing");focus.close("popup");if(focus.focused!=="open")throw new Error("focus restoration");
if(ui.fold("Straße Σςσ")!=="strasse σσσ")throw new Error("fold");const l=new ui.List([{id:"de",label:"Straße"}]);l.setQuery("STRASSE");if(l.focused!=="de")throw new Error("Unicode filter");
const menu=new ui.Menu([{id:"file",label:"File"},{id:"run",parent:"file",label:"Run"}]);menu.open("file","editor");if(menu.drawPopup(c,ui.rect(0,0,30,4),"Menu").width!==26||menu.handle("activate").returnId!=="editor")throw new Error("menu");
const notices=new ui.NoticeQueue(2);notices.push({id:"error",text:"Failure",severity:"error",actions:[{id:"off",disabled:true},{id:"retry",label:"Retry"}]});if(notices.handle("activate").action!=="retry"||notices.handle("dismiss").kind!=="dismiss"||notices.items.length!==1||notices.visible(100).length!==1)throw new Error("notice requests");
const progress=new ui.Progress({id:"job",current:40,total:100,cancellable:true});if(progress.requestCancel().kind!=="cancel"||!progress.layout(40)[1].text.includes("40%")||new ui.DataState("ready","Ready").layout(10)[0].role!=="body")throw new Error("progress/states");
const picker=new ui.SearchPicker([{id:"rust",label:"Rust"}]);picker.handle("open");picker.handle("insert","RUST");if(picker.value||picker.handle("activate").id!=="rust"||picker.value!=="rust")throw new Error("picker");
'''
 assert (b/'node_modules/tuivory/CASEFOLD-LICENSE').read_text().startswith('UNICODE LICENSE V3')
 (b/'consumer.mjs').write_text(source);(b/'consumer.ts').write_text(source)
 run(['node','consumer.mjs'],b)
 run(['node',args.typescript_compiler.resolve(),'--strict','--module','NodeNext','--target','ES2022','--noEmit','consumer.ts'],b)
 run(['node',b/'node_modules/tuivory/examples/catalog.mjs','--snapshot','--lang','en'],b)
 run(['node',b/'node_modules/tuivory/examples/catalog.mjs','--snapshot','--demo','context-menu','--lang','en'],b)
 run(['node',b/'node_modules/tuivory/examples/catalog.mjs','--snapshot','--demo','feedback','--lang','en'],b)
 print('Independent npm package: isolated external JS import/runtime, TS declarations and example passed')
