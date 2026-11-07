#!/usr/bin/env python3
"""Exercise independent native Grid SDKs against shared TSV/cursor and host-state cases."""
import argparse,json,os,shutil,subprocess,tempfile
from pathlib import Path
from check_languages import ROOT,quote,run
from build_language import build
from ansi_cells import read_cells


def cpp_source():
    out=['#include "tuivory.hpp"','#include <cassert>','#include <iostream>',
         'using namespace tuivory;',
         'GridColumn column(std::string id,int width=6){GridColumn c;c.id=id;c.label=id;c.width=width;c.editable=true;return c;}',
         'GridRecord row(std::string id,std::optional<std::string> a="한글",std::optional<std::string> b="two"){GridRecord r;r.id=id;r.cells={{"a",a},{"b",b}};return r;}',
         'Grid model(){return Grid({column("a"),column("b",8)},std::vector<GridRecord>{row("r1","한글",std::nullopt),row("r2","Straße")});}',
         'GridEditOptions editing(){GridEditOptions e;e.enabled=e.allow_null=true;return e;}',
         'template<class F> bool rejects(F f){try{f();return false;}catch(const std::invalid_argument&){return true;}}',
         'int main(){']
    for f in json.loads((ROOT/'design/grid-work-cases.json').read_text())['cases']:
        out.append('{')
        if f['accepted']:
            expected='{'+','.join(quote(s) for s in f['values'])+'}'
            out.append('auto rows=parse_grid_tsv('+quote(f['text'])+');std::vector<std::string> flat;for(auto r:rows)flat.insert(flat.end(),r.begin(),r.end());assert(flat==std::vector<std::string>('+expected+'));assert(parse_grid_tsv(format_grid_tsv(rows))==rows);')
        else:out.append('assert(rejects([]{parse_grid_tsv('+quote(f['text'])+');}));')
        out.append('}')
    for f in json.loads((ROOT/'design/grid-cursor-cases.json').read_text())['cases']:
        w=f['width'];out.append('{Grid g({column("a",'+str(w)+')},std::vector<GridRecord>{row("r",'+quote(f['text'])+')});g.set_edit_options(editing());assert(g.begin_edit());g.edit->buffer.select('+str(f['cursor'])+','+str(f['cursor'])+');Canvas c('+str(w)+',2);g.draw(c,{0,0,'+str(w)+',2});assert(c.lines()[1]==std::string('+quote(f['visible_text'])+')+std::string('+str(w)+'-cells('+quote(f['visible_text'])+'),32));assert(c.cursor==std::make_pair('+str(f['x'])+',1));std::cout<<"CURSOR|'+f['id']+'\\n"<<c.ansi()<<"\\nEND\\n";auto e=g.handle("submit");Canvas pending('+str(w)+',2);g.draw(pending,{0,0,'+str(w)+',2});assert(!pending.cursor);assert(g.resolve_edit(e.id,"retry"));}')
    out.append(r'''
 {auto g=model();g.set_edit_options(editing());assert(g.begin_edit());g.handle("insert",10,"!");auto first=g.handle("submit");assert(g.resolve_edit(first.id,"denied"));auto second=g.handle("submit");assert(first.id!=second.id&&!g.resolve_edit(first.id));g.columns[0].editable=false;assert(!g.resolve_edit(second.id)&&!g.edit);g.columns[0].editable=true;assert(g.begin_edit());auto third=g.handle("submit");g.set_rows({row("r1","replacement")});assert(!g.resolve_edit(third.id));}
 for(int flag=0;flag<3;flag++){auto r=row("r");r.state.disabled=flag==0;r.state.busy=flag==1;r.state.read_only=flag==2;r.cell_states["a"]={};Grid g({column("a"),column("b")},std::vector<GridRecord>{r});g.set_edit_options(editing());assert(!g.begin_edit());assert(!g.request_paste("new"));}
 {auto g=model();auto p=g.request_paste("one\ttwo\nthree\tfour");assert(p);p->changes[0].row_id="tamper";assert(g.pending_paste()->changes[0].row_id=="r1");g.columns[1].editable=false;assert(!g.resolve_paste(p->id)&&!g.pending_paste());g.columns[1].editable=true;p=g.request_paste("one\ttwo");assert(p&&g.resolve_paste(p->id)&&!g.resolve_paste(p->id));p=g.request_paste("NULL\t\"\"",10000,"NULL");assert(p&&p->changes[0].value.null&&!p->changes[1].value.null&&p->changes[1].value.text.empty());}
 {auto g=model();g.set_selection(GridRange{"r1","a","r2","b"});assert(parse_grid_tsv(g.copy_selection().text)==std::vector<std::vector<std::string>>({{"한글","NULL"},{"Straße","two"}}));auto o=g.options();o.max_copy_cells=3;g.set_options(o);assert(g.copy_selection().kind=="copy_rejected");assert(g.find("STRASSE")&&g.row_id()=="r2"&&g.column_id()=="a");g.case_sensitive=true;assert(!g.find("STRASSE"));g.set_cell_info([](auto,auto){GridCellInfo i;i.display="shown";i.has_display=true;return i;});g.use_display=true;assert(g.find("shown"));g.use_display=false;assert(!g.find("shown"));}
 {auto g=model();auto one=g.request("search","old"),two=g.request("search","new");assert(!g.apply_source(one.revision,std::make_shared<MemoryRows>(std::vector<GridRecord>{row("old")})));assert(g.apply_source(two.revision,std::make_shared<MemoryRows>(std::vector<GridRecord>{row("new","fresh")})));assert(!g.apply_source(two.revision,std::make_shared<MemoryRows>(std::vector<GridRecord>{})));assert(g.row_id()=="new");g.set_edit_options(editing());assert(g.begin_edit());auto e=g.handle("next");assert(g.column_id()=="a"&&g.resolve_edit(e.id)&&g.column_id()=="b"&&g.edit->column_id=="b");}
 {auto g=model();g.set_selection(GridRange{"r1","a","r2","b"});auto view=g.save_view();g.focus("r2","b");g.restore_view(view);assert(g.row_id()=="r1"&&g.column_id()=="a");auto bad=g.save_view();bad.columns[0].width=0;g.set_edit_options(editing());g.begin_edit();assert(rejects([&]{g.restore_view(bad);}));assert(g.edit&&g.row_id()=="r1");auto e=editing();e.prepare=[&](auto,auto)->std::optional<GridValue>{g.set_rows({});return GridValue{};};g.set_edit_options(e);assert(rejects([&]{g.begin_edit();}));assert(g.row_id()=="r1");}
 {struct Source:GridSource{mutable int calls=0;std::size_t size()const override{return 10000000;}GridRecord row(std::size_t i)const override{calls++;return ::row(std::to_string(i));}std::optional<std::size_t> index_of(const std::string&id)const override{if(id.empty())return std::nullopt;auto i=std::stoull(id);return i<size()?std::optional<std::size_t>(i):std::nullopt;}};auto source=std::make_shared<Source>();Grid g({column("a"),column("b")},source);assert(g.focus("9999999","a"));Canvas c(20,6);g.draw(c,{0,0,20,6});assert(source->calls<100&&g.row_id()=="9999999");}
 {auto a=column("a",3),b=column("b",5),c=column("c",3);a.pin="left";c.pin="right";auto r=row("r","A","a한bc");r.cells["c"]="C";Grid g({a,b,c},std::vector<GridRecord>{r});GridColumnOptions co;co.overflow="scroll";g.set_column_options("b",co);g.pan_cell("b",2);Canvas frame(11,3);g.draw(frame,{0,0,11,3});assert(frame.lines()[1]=="A   bc  C  ");g.set_selection(GridRange{"r","a","r","c"});g.set_rows({row("r","new")});assert(g.selected);}
 {auto g=model();auto e=editing();e.start_typing=true;e.prepare=[](auto,auto){return std::optional<GridValue>(GridValue{"prepared",false});};g.set_edit_options(e);assert(g.handle("insert",10,"typed").kind=="edit_begin"&&g.edit->buffer.value=="typed");g.handle("cancel");assert(g.begin_edit()&&g.edit->buffer.value=="prepared");g.handle("null");assert(g.handle("submit").value.null);}
''')
    out.append(r"""
 {struct Source:GridSource{mutable bool reversed=false,reenter=false;Grid*grid=nullptr;std::size_t size()const override{return 2;}GridRecord row(std::size_t i)const override{if(reenter)grid->focus("1","a");return ::row(std::to_string(reversed?1-i:i));}std::optional<std::size_t> index_of(const std::string&id)const override{if(id!="0"&&id!="1")return std::nullopt;auto i=std::size_t(id[0]-'0');return reversed?1-i:i;}};auto source=std::make_shared<Source>();Grid g({column("a",8)},source);source->grid=&g;Canvas c(10,4);g.draw(c,{0,0,10,4});source->reversed=true;assert(g.click(1,1,10,4).kind.empty());g.draw(c,{0,0,10,4});assert(g.click(1,1,10,4).row_id=="1");g.columns[0].width=4;assert(g.click(1,0,10,4).kind.empty());auto before=c.lines();source->reenter=true;assert(rejects([&]{g.draw(c,{0,0,10,4});}));assert(c.lines()==before);source->reenter=false;assert(g.row_id()=="1");}
""")
    out.append(r"""

 {struct Invalid:GridSource{std::size_t size()const override{return 1;}GridRecord row(std::size_t)const override{return ::row("wrong");}std::optional<std::size_t> index_of(const std::string&id)const override{return id=="r1"?std::optional<std::size_t>(0):std::nullopt;}};auto bad=std::make_shared<Invalid>();auto g=model();g.set_edit_options(editing());assert(g.begin_edit());auto e=g.handle("submit");assert(rejects([&]{g.resolve_edit(e.id,"",bad);}));assert(g.edit&&g.edit->pending&&g.edit->id==e.id);assert(g.resolve_edit(e.id));auto p=g.request_paste("new");assert(p);assert(rejects([&]{g.resolve_paste(p->id,bad);}));assert(g.pending_paste()&&g.pending_paste()->id==p->id);assert(g.resolve_paste(p->id));}

""")
    out.append(r"""

 {Grid g({column("a",2)},std::vector<GridRecord>{row("r",std::nullopt)});GridLabels labels;labels.null_text="한글";g.set_labels(labels);GridColumnOptions co;co.auto_fit=true;co.max_width=8;g.set_column_options("a",co);assert(g.geometry(20,4).columns[0].width==4&&g.columns[0].width==2);g.set_edit_options(editing());assert(g.begin_edit());Canvas c(20,4);g.draw(c,{0,0,20,4});assert(c.lines()[1].find("한글")!=std::string::npos&&!c.cursor&&g.edit);auto e=g.handle("submit");g.geometry(20,4);assert(g.edit->pending&&g.resolve_edit(e.id));auto external=g.labels();external.null_text="outside";assert(g.labels().null_text=="한글");labels.null_text="[x]";g.set_labels(labels);g.draw(c,{0,0,20,4});assert(c.lines()[1].find("[x]")!=std::string::npos);}

""")
    for theme in ('dark','light','blackwhite'):
        for colors in ('8','16','256','truecolor'):
            out.append('{auto g=model();auto o=grid_preset("data").with_density("comfortable");g.set_options(o);g.set_cell_info([](const GridRecord&r,auto){GridCellInfo i;i.state.disabled=r.id=="r2";return i;});for(int w:{0,1,4,12,30}){Canvas c(w,6,Palette('+quote(theme)+','+quote(colors)+'));g.draw(c,{0,0,w,6});assert(!c.cursor);for(auto line:c.data)for(auto cell:line)if(cell.owner>=0)assert(cells(line[cell.owner].text)>1);}Canvas c(30,6,Palette('+quote(theme)+','+quote(colors)+'));g.draw(c,{0,0,30,6});assert(c.data[3][2].style.dim);assert(g.click(4,3,30,6).kind.empty());assert(g.click(4,1,29,6).kind.empty());std::cout<<"PALETTE|'+theme+'|'+colors+'\\n"<<c.ansi()<<"\\nEND\\n";}')
    out.append('return 0;}')
    return '\n'.join(out)


def java_source():
    out=['import static io.tuivory.Tuivory.*;import java.util.*;public class GridCases{',
         'static void check(boolean b){if(!b)throw new AssertionError();}',
         'static boolean rejects(Runnable f){try{f.run();return false;}catch(IllegalArgumentException e){return true;}}',
         'static GridColumn column(String id,int width){return new GridColumn(id,id,width,true);}',
         'static GridRecord row(String id,String a,String b){var r=new GridRecord(id);r.cells.put("a",a);r.cells.put("b",b);return r;}',
         'static Grid model(){return new Grid(List.of(column("a",6),column("b",8)),List.of(row("r1","한글",null),row("r2","Straße","two")));}',
         'static GridEditOptions editing(){var e=new GridEditOptions();e.enabled=e.allowNull=true;return e;}',
         'public static void main(String[]args){']
    for f in json.loads((ROOT/'design/grid-work-cases.json').read_text())['cases']:
        if f['accepted']:
            out.append('{var rows=parseGridTSV('+quote(f['text'])+');check(rows.stream().flatMap(List::stream).toList().equals(List.of('+','.join(quote(v) for v in f['values'])+')));check(parseGridTSV(formatGridTSV(rows)).equals(rows));}')
        else:out.append('check(rejects(()->parseGridTSV('+quote(f['text'])+')));')
    for f in json.loads((ROOT/'design/grid-cursor-cases.json').read_text())['cases']:
        w=f['width'];out.append('{var g=new Grid(List.of(column("a",'+str(w)+')),List.of(row("r",'+quote(f['text'])+',"")));g.setEditOptions(editing());check(g.beginEdit());g.edit.buffer.select('+str(f['cursor'])+','+str(f['cursor'])+');var c=new Canvas('+str(w)+',2);g.draw(c,new Rect(0,0,'+str(w)+',2));check(c.lines().get(1).equals('+quote(f['visible_text'])+'+" ".repeat('+str(w)+'-cells('+quote(f['visible_text'])+'))));check(c.cursorX=='+str(f['x'])+'&&c.cursorY==1);System.out.print("CURSOR|'+f['id']+'\\n"+c.ansi()+"\\nEND\\n");var e=g.handle("submit");var pending=new Canvas('+str(w)+',2);g.draw(pending,new Rect(0,0,'+str(w)+',2));check(pending.cursorX<0);check(g.resolveEdit(e.id(),"retry"));}')
    out.append(r"""
 {var g=model();g.setEditOptions(editing());check(g.beginEdit());g.handle("insert",10,"!");var first=g.handle("submit");check(g.resolveEdit(first.id(),"denied"));var second=g.handle("submit");check(first.id()!=second.id()&&!g.resolveEdit(first.id()));g.columns.get(0).editable=false;check(!g.resolveEdit(second.id())&&g.edit==null);g.columns.get(0).editable=true;check(g.beginEdit());var third=g.handle("submit");g.setRows(List.of(row("r1","replacement","")));check(!g.resolveEdit(third.id()));}
 for(int flag=0;flag<3;flag++){var r=row("r","x","");r.state.disabled=flag==0;r.state.busy=flag==1;r.state.readOnly=flag==2;r.cellStates.put("a",new State());var g=new Grid(List.of(column("a",6),column("b",8)),List.of(r));g.setEditOptions(editing());check(!g.beginEdit()&&g.requestPaste("new").isEmpty());}
 {var g=model();var p=g.requestPaste("one\ttwo\nthree\tfour").orElseThrow();check(p.changes().get(0).rowId().equals("r1"));boolean immutable=false;try{p.changes().clear();}catch(UnsupportedOperationException expected){immutable=true;}check(immutable);g.columns.get(1).editable=false;check(!g.resolvePaste(p.id())&&g.pendingPaste()==null);g.columns.get(1).editable=true;var next=g.requestPaste("one\ttwo").orElseThrow();check(g.resolvePaste(next.id())&&!g.resolvePaste(next.id()));var nulls=g.requestPaste("NULL\t\"\"",10000,"NULL").orElseThrow();check(nulls.changes().get(0).value().isNull()&&!nulls.changes().get(1).value().isNull()&&nulls.changes().get(1).value().text().isEmpty());}
 {var g=model();g.setSelection(new GridRange("r1","a","r2","b"));check(parseGridTSV(g.copySelection().text()).equals(List.of(List.of("한글","NULL"),List.of("Straße","two"))));var o=g.options();o.maxCopyCells=3;g.setOptions(o);check(g.copySelection().kind().equals("copy_rejected"));check(g.find("STRASSE")&&g.rowId().equals("r2")&&g.columnId().equals("a"));g.caseSensitive=true;check(!g.find("STRASSE"));g.setCellInfo((r,c)->{var i=new GridCellInfo();i.display="shown";i.hasDisplay=true;return i;});g.useDisplay=true;check(g.find("shown"));g.useDisplay=false;check(!g.find("shown"));}
 {var g=model();var one=g.request("search","old");var two=g.request("search","new");check(!g.applySource(one.revision(),new MemoryRows(List.of(row("old","","")))));check(g.applySource(two.revision(),new MemoryRows(List.of(row("new","fresh","")))));check(!g.applySource(two.revision(),new MemoryRows(List.of())));check(g.rowId().equals("new"));g.setEditOptions(editing());check(g.beginEdit());var e=g.handle("next");check(g.columnId().equals("a")&&g.resolveEdit(e.id())&&g.columnId().equals("b")&&g.edit.columnId.equals("b"));}
 {var g=model();g.setSelection(new GridRange("r1","a","r2","b"));var view=g.saveView();g.focus("r2","b");g.restoreView(view);check(g.rowId().equals("r1")&&g.columnId().equals("a"));var bad=g.saveView();bad.columns.get(0).width=0;g.setEditOptions(editing());g.beginEdit();check(rejects(()->g.restoreView(bad)));check(g.edit!=null&&g.rowId().equals("r1"));var e=editing();e.prepare=(r,c)->{g.setRows(List.of());return new GridValue("",false);};g.setEditOptions(e);check(rejects(()->g.beginEdit()));check(g.rowId().equals("r1"));}
 {class Source implements GridSource{int calls;public int size(){return 10000000;}public GridRecord row(int i){calls++;return GridCases.row(String.valueOf(i),"한글","two");}public OptionalInt indexOf(String id){if(id.isEmpty())return OptionalInt.empty();int i=Integer.parseInt(id);return i>=0&&i<size()?OptionalInt.of(i):OptionalInt.empty();}}var source=new Source();var g=new Grid(List.of(column("a",6),column("b",8)),source);check(g.focus("9999999","a"));var c=new Canvas(20,6);g.draw(c,new Rect(0,0,20,6));check(source.calls<100&&g.rowId().equals("9999999"));}
 {var a=column("a",3);var b=column("b",5);var c=column("c",3);a.pin="left";c.pin="right";var r=row("r","A","a한bc");r.cells.put("c","C");var g=new Grid(List.of(a,b,c),List.of(r));var co=new GridColumnOptions();co.overflow="scroll";g.setColumnOptions("b",co);g.panCell("b",2);var frame=new Canvas(11,3);g.draw(frame,new Rect(0,0,11,3));check(frame.lines().get(1).equals("A   bc  C  "));g.setSelection(new GridRange("r","a","r","c"));g.setRows(List.of(row("r","new","")));check(g.selected!=null);}
 {var g=model();var e=editing();e.startTyping=true;e.prepare=(r,c)->new GridValue("prepared",false);g.setEditOptions(e);check(g.handle("insert",10,"typed").kind().equals("edit_begin")&&g.edit.buffer.value().equals("typed"));g.handle("cancel");check(g.beginEdit()&&g.edit.buffer.value().equals("prepared"));g.handle("null");check(g.handle("submit").value().isNull());}
""")
    out.append(r"""
 {class Source implements GridSource{boolean reversed,reenter;Grid grid;public int size(){return 2;}public GridRecord row(int i){if(reenter)grid.focus("1","a");return GridCases.row(String.valueOf(reversed?1-i:i),"first","");}public OptionalInt indexOf(String id){if(!id.equals("0")&&!id.equals("1"))return OptionalInt.empty();int i=Integer.parseInt(id);return OptionalInt.of(reversed?1-i:i);}}var source=new Source();var g=new Grid(List.of(column("a",8)),source);source.grid=g;var c=new Canvas(10,4);g.draw(c,new Rect(0,0,10,4));source.reversed=true;check(g.click(1,1,10,4).kind().isEmpty());g.draw(c,new Rect(0,0,10,4));check(g.click(1,1,10,4).rowId().equals("1"));g.columns.get(0).width=4;check(g.click(1,0,10,4).kind().isEmpty());var before=c.lines();source.reenter=true;check(rejects(()->g.draw(c,new Rect(0,0,10,4))));check(c.lines().equals(before));source.reenter=false;check(g.rowId().equals("1"));}
""")
    out.append(r"""

 {class Invalid implements GridSource{public int size(){return 1;}public GridRecord row(int i){return GridCases.row("wrong","","");}public OptionalInt indexOf(String id){return id.equals("r1")?OptionalInt.of(0):OptionalInt.empty();}}var bad=new Invalid();var g=model();g.setEditOptions(editing());check(g.beginEdit());var e=g.handle("submit");check(rejects(()->g.resolveEdit(e.id(),"",bad)));check(g.edit!=null&&g.edit.pending&&g.edit.id==e.id());check(g.resolveEdit(e.id()));var p=g.requestPaste("new").orElseThrow();check(rejects(()->g.resolvePaste(p.id(),bad)));check(g.pendingPaste()!=null&&g.pendingPaste().id()==p.id());check(g.resolvePaste(p.id()));}

""")
    out.append(r"""

 {var g=new Grid(List.of(column("a",2)),List.of(row("r",null,"")));var labels=new GridLabels();labels.nullText="한글";g.setLabels(labels);var co=new GridColumnOptions();co.autoFit=true;co.maxWidth=8;g.setColumnOptions("a",co);check(g.geometry(20,4).columns().get(0).width()==4&&g.columns.get(0).width==2);g.setEditOptions(editing());check(g.beginEdit());var c=new Canvas(20,4);g.draw(c,new Rect(0,0,20,4));check(c.lines().get(1).contains("한글")&&c.cursorX<0&&g.edit!=null);var e=g.handle("submit");g.geometry(20,4);check(g.edit.pending&&g.resolveEdit(e.id()));var external=g.labels();external.nullText="outside";check(g.labels().nullText.equals("한글"));labels.nullText="[x]";g.setLabels(labels);g.draw(c,new Rect(0,0,20,4));check(c.lines().get(1).contains("[x]"));}

""")
    for theme in ('dark','light','blackwhite'):
        for colors in ('8','16','256','truecolor'):
            out.append('{var g=model();var o=gridPreset("data").withDensity("comfortable");g.setOptions(o);g.setCellInfo((r,col)->{var i=new GridCellInfo();i.state.disabled=r.id.equals("r2");return i;});for(int w:new int[]{0,1,4,12,30}){var c=new Canvas(w,6,new Palette('+quote(theme)+','+quote(colors)+'));g.draw(c,new Rect(0,0,w,6));check(c.cursorX<0);for(var line:c.data)for(var cell:line)if(cell.owner>=0)check(cells(line[cell.owner].text)>1);}var c=new Canvas(30,6,new Palette('+quote(theme)+','+quote(colors)+'));g.draw(c,new Rect(0,0,30,6));check(c.data[3][2].style.dim());check(g.click(4,3,30,6).kind().isEmpty());check(g.click(4,1,29,6).kind().isEmpty());System.out.print("PALETTE|'+theme+'|'+colors+'\\n"+c.ansi()+"\\nEND\\n");}')
    out.append('}}')
    return '\n'.join(out)

def c_source():
    out=['#include "tuivory.h"','#include <assert.h>','#include <stdio.h>','#include <stdlib.h>','#include <string.h>',r"""
static TuiGridColumn column(const char*id,int w){return (TuiGridColumn){.id=id,.label=id,.width=w,.editable=1};}
static TuiGrid*model(void){TuiGridColumn cs[2]={column("a",6),column("b",8)};TuiGridCell cells[2][2]={{{.column_id="a",.text="한글"},{.column_id="b",.text="",.is_null=1}},{{.column_id="a",.text="Straße"},{.column_id="b",.text="two"}}};TuiGridRecord rows[2]={{.id="r1",.cells=cells[0],.cell_count=2},{.id="r2",.cells=cells[1],.cell_count=2}};TuiGrid*g=tui_grid_new(cs,2,rows,2);assert(g);return g;}
static void editing(TuiGrid*g){assert(tui_grid_set_edit_options(g,(TuiGridEditOptions){.enabled=1,.allow_null=1})==TUI_OK);}
static void frame(TuiCanvas*c,const char*name){char*a=tui_canvas_ansi(c);assert(a);printf("%s\n%s\nEND\n",name,a);free(a);}
static TuiResult info(void*context,const TuiGridRecord*r,const TuiGridColumn*c,TuiGridCellInfo*out){(void)context;(void)c;out->state.disabled=!strcmp(r->id,"r2");return TUI_OK;}
typedef struct {int calls,readonly,reversed,reenter;TuiGrid*grid;size_t count;char id[32];TuiGridCell cells[2];}Source;
static TuiResult source_row(void*context,size_t i,TuiGridRecord*out){Source*s=context;if(i>=s->count)return TUI_INVALID;s->calls++;if(s->reenter){assert(!tui_grid_focus(s->grid,"1","a"));return TUI_INVALID;}snprintf(s->id,sizeof(s->id),"%zu",s->reversed?s->count-1-i:i);s->cells[0]=(TuiGridCell){.column_id="a",.text="한글"};s->cells[1]=(TuiGridCell){.column_id="b",.text="two"};*out=(TuiGridRecord){.id=s->id,.cells=s->cells,.cell_count=2,.state={.read_only=s->readonly}};return TUI_OK;}
static TuiResult source_index(void*context,const char*id,size_t*out){Source*s=context;if(!id||!*id)return TUI_INVALID;char*end;unsigned long i=strtoul(id,&end,10);if(*end||i>=s->count)return TUI_INVALID;*out=s->reversed?s->count-1-i:i;strcpy(s->id,"changed");return TUI_OK;}
static TuiGridSource source(Source*s){return (TuiGridSource){s,s->count,source_row,source_index};}
static TuiResult prepared(void*ctx,const TuiGridRecord*r,const TuiGridColumn*c,TuiGridValue*out){(void)ctx;(void)r;(void)c;*out=(TuiGridValue){"prepared",0};return TUI_OK;}
static TuiResult recursive(void*ctx,const TuiGridRecord*r,const TuiGridColumn*c,TuiGridValue*out){(void)r;(void)c;(void)out;assert(tui_grid_set_rows(ctx,NULL,0)==TUI_INVALID);return TUI_INVALID;}
static TuiResult bad_row(void*ctx,size_t i,TuiGridRecord*out){(void)ctx;(void)i;*out=(TuiGridRecord){.id="wrong"};return TUI_OK;}
static TuiResult bad_index(void*ctx,const char*id,size_t*out){(void)ctx;if(strcmp(id,"r1"))return TUI_INVALID;*out=0;return TUI_OK;}
int main(void){
"""]
    for f in json.loads((ROOT/'design/grid-work-cases.json').read_text())['cases']:
        if f['accepted']:
            out.append('{TuiGridTSV*t=NULL;assert(tui_grid_parse_tsv('+quote(f['text'])+',10000,&t)==TUI_OK);size_t k=0;const char*values[]={'+','.join(quote(v)for v in f['values'])+'};for(size_t r=0;r<tui_grid_tsv_rows(t);r++)for(size_t c=0;c<tui_grid_tsv_columns(t);c++)assert(!strcmp(tui_grid_tsv_at(t,r,c),values[k++]));assert(k=='+str(len(f['values']))+');char*formatted=NULL;assert(tui_grid_format_tsv(t,&formatted)==TUI_OK);TuiGridTSV*again=NULL;assert(tui_grid_parse_tsv(formatted,10000,&again)==TUI_OK);assert(tui_grid_tsv_rows(again)==tui_grid_tsv_rows(t));free(formatted);tui_grid_tsv_free(again);tui_grid_tsv_free(t);}')
        else:out.append('{TuiGridTSV*t=NULL;assert(tui_grid_parse_tsv('+quote(f['text'])+',10000,&t)==TUI_INVALID&&!t);}')
    for f in json.loads((ROOT/'design/grid-cursor-cases.json').read_text())['cases']:
        w=f['width'];out.append('{TuiGridColumn col=column("a",'+str(w)+');TuiGridCell cell={.column_id="a",.text='+quote(f['text'])+'};TuiGridRecord r={.id="r",.cells=&cell,.cell_count=1};TuiGrid*g=tui_grid_new(&col,1,&r,1);assert(g);editing(g);assert(tui_grid_begin_edit(g,NULL));tui_text_select(tui_grid_edit_buffer(g),'+str(f['cursor'])+','+str(f['cursor'])+');TuiCanvas*c=tui_canvas_new('+str(w)+',2,"dark","256");assert(c&&tui_grid_draw(g,c,(TuiRect){0,0,'+str(w)+',2},1,0)==TUI_OK);char*line=tui_canvas_line(c,1);const char*expected='+quote(f['visible_text'])+';size_t bytes=strlen(expected);assert(!strncmp(line,expected,bytes));for(size_t i=bytes;i<strlen(line);i++)assert(line[i]==32);free(line);int x=-1,y=-1,glyph=0;assert(tui_grid_edit_cursor(g,'+str(w)+',2,&x,&y,&glyph)==TUI_OK&&x=='+str(f['x'])+'&&y==1);frame(c,"CURSOR|'+f['id']+'");TuiGridEvent e=tui_grid_handle(g,"submit",10,"");assert(!strcmp(e.kind,"edit_submit"));assert(tui_grid_draw(g,c,(TuiRect){0,0,'+str(w)+',2},1,0)==TUI_OK);char*a=tui_canvas_ansi(c);assert(a&&!strstr(a,"\\033[?25h"));free(a);assert(tui_grid_resolve_edit(g,e.id,"retry",NULL));tui_canvas_free(c);tui_grid_free(g);}')
    out.append(r"""
 {TuiGrid*g=model();editing(g);assert(tui_grid_begin_edit(g,NULL));tui_grid_handle(g,"insert",10,"!");TuiGridEvent e=tui_grid_handle(g,"submit",10,"");unsigned long long first=e.id;assert(tui_grid_resolve_edit(g,first,"denied",NULL));e=tui_grid_handle(g,"submit",10,"");assert(e.id!=first&&!tui_grid_resolve_edit(g,first,"",NULL));TuiGridRecord r={.id="r1"};assert(tui_grid_set_rows(g,&r,1)==TUI_OK);assert(!tui_grid_resolve_edit(g,e.id,"",NULL));tui_grid_free(g);}
 for(int flag=0;flag<3;flag++){TuiGridColumn col=column("a",6);TuiGridCell cell={.column_id="a",.text="x"};TuiGridRecord r={.id="r",.cells=&cell,.cell_count=1};r.state.disabled=flag==0;r.state.busy=flag==1;r.state.read_only=flag==2;TuiGrid*g=tui_grid_new(&col,1,&r,1);assert(g);editing(g);assert(!tui_grid_begin_edit(g,NULL));assert(tui_grid_request_paste(g,"new",10000,NULL)==TUI_INVALID);tui_grid_free(g);}
 {TuiGrid*g=model();assert(tui_grid_request_paste(g,"one\ttwo\nthree\tfour",10000,NULL)==TUI_OK);const TuiGridPasteRequest*p=tui_grid_pending_paste(g);assert(p&&p->change_count==4&&!strcmp(p->changes[0].row_id,"r1"));unsigned long long id=p->id;assert(tui_grid_resolve_paste(g,id,NULL)&&!tui_grid_resolve_paste(g,id,NULL));char*text=NULL;assert(tui_grid_copy(g,0,"NULL",&text)==TUI_OK&&!strcmp(text,"한글"));free(text);assert(tui_grid_request_paste(g,"NULL\t\"\"",10000,"NULL")==TUI_OK);p=tui_grid_pending_paste(g);assert(p->changes[0].value.is_null&&!p->changes[1].value.is_null&&!strcmp(p->changes[1].value.text,""));tui_grid_free(g);}
 {TuiGrid*g=model();assert(tui_grid_set_selection(g,&(TuiGridRange){"r1","a","r2","b"})==TUI_OK);char*text=NULL;assert(tui_grid_copy(g,0,"NULL",&text)==TUI_OK&&!strcmp(text,"한글\tNULL\nStraße\ttwo"));free(text);TuiGridOptions o;assert(tui_grid_preset("simple",&o)==TUI_OK);o.max_copy_cells=3;assert(tui_grid_configure(g,&o)==TUI_OK);assert(tui_grid_copy(g,0,"NULL",&text)==TUI_INVALID);assert(tui_grid_find(g,"STRASSE",0,0,0,100000)&&!strcmp(tui_grid_row_id(g),"r2")&&!strcmp(tui_grid_column_id(g),"a"));assert(!tui_grid_find(g,"STRASSE",0,1,0,100000));tui_grid_free(g);}
 {TuiGrid*g=model();TuiGridEvent e=tui_grid_request(g,"search","old");unsigned long long old=e.revision;e=tui_grid_request(g,"search","new");unsigned long long current=e.revision;Source data={.count=1};assert(!tui_grid_apply_source(g,old,source(&data)));assert(tui_grid_apply_source(g,current,source(&data)));assert(!tui_grid_apply_source(g,current,source(&data)));assert(!strcmp(tui_grid_row_id(g),"0"));editing(g);assert(tui_grid_begin_edit(g,NULL));e=tui_grid_handle(g,"next",10,"");assert(tui_grid_resolve_edit(g,e.id,"",NULL));assert(!strcmp(tui_grid_column_id(g),"b"));tui_grid_free(g);}
 {TuiGrid*g=model();assert(tui_grid_set_selection(g,&(TuiGridRange){"r1","a","r2","b"})==TUI_OK);TuiGridViewState*view=tui_grid_save_view(g);assert(view&&tui_grid_focus(g,"r2","b"));assert(tui_grid_restore_view(g,view)==TUI_OK);assert(!strcmp(tui_grid_row_id(g),"r1")&&!strcmp(tui_grid_column_id(g),"a"));tui_grid_view_free(view);TuiGridEditOptions o={.enabled=1,.prepare=recursive,.context=g};assert(tui_grid_set_edit_options(g,o)==TUI_OK&&!tui_grid_begin_edit(g,NULL));assert(!strcmp(tui_grid_row_id(g),"r1"));tui_grid_free(g);}
 {Source data={.count=10000000};TuiGrid*g=model();assert(tui_grid_set_source(g,source(&data))==TUI_OK);assert(tui_grid_focus(g,"9999999","a"));TuiCanvas*c=tui_canvas_new(20,6,"dark","256");assert(c&&tui_grid_draw(g,c,(TuiRect){0,0,20,6},1,0)==TUI_OK);assert(data.calls<100&&!strcmp(tui_grid_row_id(g),"9999999"));editing(g);assert(tui_grid_begin_edit(g,NULL));TuiGridEvent e=tui_grid_handle(g,"submit",10,"");data.readonly=1;assert(!tui_grid_resolve_edit(g,e.id,"",NULL)&&!tui_grid_edit_session(g));data.readonly=0;assert(tui_grid_request_paste(g,"new",10000,NULL)==TUI_OK);unsigned long long id=tui_grid_pending_paste(g)->id;data.readonly=1;assert(!tui_grid_resolve_paste(g,id,NULL)&&!tui_grid_pending_paste(g));tui_canvas_free(c);tui_grid_free(g);}
 {TuiGridColumn cols[3]={column("a",3),column("b",5),column("c",3)};cols[0].pin="left";cols[2].pin="right";TuiGridCell cells[3]={{.column_id="a",.text="A"},{.column_id="b",.text="a한bc"},{.column_id="c",.text="C"}};TuiGridRecord r={.id="r",.cells=cells,.cell_count=3};TuiGrid*g=tui_grid_new(cols,3,&r,1);assert(g&&tui_grid_set_column_options(g,"b",(TuiGridColumnOptions){.overflow="scroll"})==TUI_OK&&tui_grid_pan_cell(g,"b",2)==TUI_OK);TuiCanvas*c=tui_canvas_new(11,3,"dark","256");assert(c&&tui_grid_draw(g,c,(TuiRect){0,0,11,3},1,0)==TUI_OK);char*line=tui_canvas_line(c,1);assert(line&&!strcmp(line,"A   bc  C  "));free(line);TuiGridGeometry*geo=NULL;assert(tui_grid_geometry(g,11,3,&geo)==TUI_OK);tui_grid_free(g);assert(tui_grid_span_count(geo)==3&&!strcmp(tui_grid_span_at(geo,1)->id,"b"));tui_grid_geometry_free(geo);tui_canvas_free(c);}
 {TuiGrid*g=model();TuiGridEditOptions o={.enabled=1,.start_typing=1,.allow_null=1,.prepare=prepared};assert(tui_grid_set_edit_options(g,o)==TUI_OK);assert(!strcmp(tui_grid_handle(g,"insert",10,"typed").kind,"edit_begin"));assert(!strcmp(tui_text_value(tui_grid_edit_buffer(g)),"typed"));tui_grid_handle(g,"cancel",10,"");assert(tui_grid_begin_edit(g,NULL)&&!strcmp(tui_text_value(tui_grid_edit_buffer(g)),"prepared"));tui_grid_handle(g,"null",10,"");assert(tui_grid_handle(g,"submit",10,"").value.is_null);tui_grid_free(g);}
""")
    out.append(r"""
 {Source data={.count=2};TuiGrid*g=model();data.grid=g;assert(tui_grid_set_source(g,source(&data))==TUI_OK&&tui_grid_focus(g,"0","a"));TuiCanvas*c=tui_canvas_new(10,4,"dark","256");assert(c&&tui_grid_draw(g,c,(TuiRect){0,0,10,4},1,0)==TUI_OK);data.reversed=1;assert(!*tui_grid_click(g,1,1,10,4).kind);assert(tui_grid_draw(g,c,(TuiRect){0,0,10,4},1,0)==TUI_OK);assert(!strcmp(tui_grid_click(g,1,1,10,4).row_id,"1"));char*before=tui_canvas_line(c,1);data.reenter=1;assert(tui_grid_draw(g,c,(TuiRect){0,0,10,4},1,0)==TUI_INVALID);char*after=tui_canvas_line(c,1);assert(before&&after&&!strcmp(before,after));free(before);free(after);data.reenter=0;tui_canvas_free(c);tui_grid_free(g);}
""")
    out.append(r"""
 {TuiGridSource bad={NULL,1,bad_row,bad_index};TuiGrid*g=model();editing(g);assert(tui_grid_begin_edit(g,NULL));TuiGridEvent e=tui_grid_handle(g,"submit",10,"");assert(!tui_grid_resolve_edit(g,e.id,"",&bad));assert(tui_grid_edit_session(g)&&tui_grid_edit_session(g)->pending&&tui_grid_edit_session(g)->id==e.id);assert(tui_grid_resolve_edit(g,e.id,"",NULL));assert(tui_grid_request_paste(g,"new",10000,NULL)==TUI_OK);unsigned long long id=tui_grid_pending_paste(g)->id;assert(!tui_grid_resolve_paste(g,id,&bad));assert(tui_grid_pending_paste(g)&&tui_grid_pending_paste(g)->id==id);assert(tui_grid_resolve_paste(g,id,NULL));tui_grid_free(g);}
""")
    out.append(r"""

 {TuiGridColumn col=column("a",2);TuiGridCell cell={.column_id="a",.text="",.is_null=1};TuiGridRecord row={.id="r",.cells=&cell,.cell_count=1};TuiGrid*g=tui_grid_new(&col,1,&row,1);assert(g);TuiGridLabels labels={"한글","loading","empty","range","more"};assert(tui_grid_set_labels(g,labels)==TUI_OK);assert(tui_grid_set_column_options(g,"a",(TuiGridColumnOptions){.auto_fit=1,.max_width=8})==TUI_OK);TuiGridGeometry*geo=NULL;assert(tui_grid_geometry(g,20,4,&geo)==TUI_OK&&tui_grid_span_at(geo,0)->width==4);tui_grid_geometry_free(geo);editing(g);assert(tui_grid_begin_edit(g,NULL));TuiCanvas*c=tui_canvas_new(20,4,"dark","256");assert(c&&tui_grid_draw(g,c,(TuiRect){0,0,20,4},1,0)==TUI_OK);char*line=tui_canvas_line(c,1);assert(line&&strstr(line,"한글"));free(line);int x,y,w;assert(tui_grid_edit_cursor(g,20,4,&x,&y,&w)==TUI_INVALID);TuiGridEvent e=tui_grid_handle(g,"submit",10,"");assert(tui_grid_geometry(g,20,4,&geo)==TUI_OK);tui_grid_geometry_free(geo);assert(tui_grid_edit_session(g)->pending&&tui_grid_resolve_edit(g,e.id,"",NULL));labels.null_text="[x]";assert(tui_grid_set_labels(g,labels)==TUI_OK&&tui_grid_draw(g,c,(TuiRect){0,0,20,4},1,0)==TUI_OK);line=tui_canvas_line(c,1);assert(line&&strstr(line,"[x]"));free(line);assert(tui_grid_set_column_options(g,"a",(TuiGridColumnOptions){0})==TUI_OK&&tui_grid_geometry(g,20,4,&geo)==TUI_OK&&tui_grid_span_at(geo,0)->width==2);tui_grid_geometry_free(geo);tui_canvas_free(c);tui_grid_free(g);}

""")
    for theme in ('dark','light','blackwhite'):
        for colors in ('8','16','256','truecolor'):
            out.append('{TuiGrid*g=model();TuiGridOptions o;assert(tui_grid_preset("data",&o)==TUI_OK&&tui_grid_density(&o,"comfortable")==TUI_OK&&tui_grid_configure(g,&o)==TUI_OK&&tui_grid_set_cell_info(g,info,NULL)==TUI_OK);int widths[]={0,1,4,12,30};for(size_t i=0;i<5;i++){int w=widths[i];TuiCanvas*c=tui_canvas_new(w,6,'+quote(theme)+','+quote(colors)+');assert(c&&tui_grid_draw(g,c,(TuiRect){0,0,w,6},1,0)==TUI_OK);tui_canvas_free(c);}TuiCanvas*c=tui_canvas_new(30,6,'+quote(theme)+','+quote(colors)+');assert(c&&tui_grid_draw(g,c,(TuiRect){0,0,30,6},1,0)==TUI_OK);assert(!*tui_grid_click(g,4,3,30,6).kind&&!*tui_grid_click(g,4,1,29,6).kind);frame(c,"PALETTE|'+theme+'|'+colors+'");tui_canvas_free(c);tui_grid_free(g);}')
    out.append('return 0;}')
    return '\n'.join(out)

def validate_output(output):
    frames=0
    for block in output.split('\nEND\n'):
        if not block.strip():continue
        name,ansi=block.split('\n',1);frame=read_cells(ansi);frames+=1
        if name.startswith('CURSOR|'):assert '\x1b[?25h' in ansi,name
        else:
            assert name.startswith('PALETTE|') and '\x1b[?25h' not in ansi,name
            assert frame[2,3][4],name
    assert frames==23,frames


def source(language):
    if language=='c':return c_source()
    if language=='cpp':return cpp_source()
    if language=='java':return java_source()
    raise ValueError('unsupported grid SDK language')

def main():
    p=argparse.ArgumentParser();p.add_argument('--language',choices=['c','cpp','java'],required=True);lang=p.parse_args().language
    artifact=build(lang)
    with tempfile.TemporaryDirectory(prefix='tuivory-grid-') as directory:
        base=Path(directory)
        if lang=='java':
            shutil.copy2(artifact,base/'tuivory.jar');src=base/'GridCases.java';src.write_text(java_source())
            run(['javac','--release','17','-encoding','UTF-8','-Xlint:all','-Werror','-cp',base/'tuivory.jar',src],base)
            validate_output(subprocess.check_output(['java','-cp',str(base/'tuivory.jar')+os.pathsep+str(base),'GridCases'],cwd=base,text=True))
        else:
            shutil.copytree(ROOT/lang/'include',base/'include');src=base/('grid.c'if lang=='c'else'grid.cpp');src.write_text(c_source()if lang=='c'else cpp_source())
            flags=['cc'if lang=='c'else'c++','-std=c11'if lang=='c'else'-std=c++17','-Wall','-Wextra','-Werror','-I',base/'include',src]
            run(flags+([ROOT/'c/src/tuivory.c']if lang=='c'else[])+['-fsanitize=address,undefined','-o',base/'checked'],base)
            validate_output(subprocess.check_output([base/'checked'],cwd=base,text=True,env=dict(os.environ,ASAN_OPTIONS=os.environ.get('ASAN_OPTIONS','detect_leaks=0'))))
            if lang=='c':
                shutil.copy2(ROOT/'.cache/native/c/libtuivory.a',base/'libtuivory.a');flags+=[base/'libtuivory.a']
            run(flags+['-static','-o',base/'isolated'],base)
            validate_output(subprocess.check_output([base/'isolated'],cwd=base,text=True))
    print(lang+': shared TSV/cursor, host approvals, virtual source, stable view and 23 actual ANSI frames passed')
if __name__=='__main__':main()
