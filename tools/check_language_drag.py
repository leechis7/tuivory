#!/usr/bin/env python3
"""Verify independent immutable drop requests, revisions and captured previews."""
import argparse,json,os,shutil,subprocess,tempfile
from pathlib import Path
from check_languages import ROOT,quote,run
from build_language import build
F=json.loads((ROOT/'design/drag-cases.json').read_text())

def cpp_model(kind):
    if kind=='tabs':
        items=['{'+','.join([quote(t['id']),quote(t.get('title','')),str(t.get('edited',False)).lower(),str(t.get('closable',False)).lower(),str(t.get('disabled',False)).lower()])+'}'for t in F['tabs']]
        return 'Tabs m({'+','.join(items)+'});'
    nodes=[]
    for n in F['tree']:
        fields=[quote(n.get(k,''))for k in ['id','name','parent','secondary','icon','ascii_icon']]
        fields+=['std::optional<unsigned long long>('+str(n['count'])+'ull)'if'count'in n else'std::nullopt',str(n.get('branch',False)).lower()]
        nodes.append('{'+','.join(fields)+'}')
    return 'Tree m({'+','.join(nodes)+'});m.expanded={"root","a"};'

def cpp_source():
    out=['#include "tuivory.hpp"','#include <cassert>','#include <iostream>','using namespace tuivory;','int main(){']
    for case in F['cases']:
        out.append('{'+cpp_model(case['kind'])+'auto before=drag_revision(m);assert(before=='+quote(F['tab_revision_hex'if case['kind']=='tabs'else'tree_revision_hex'])+');DragOptions options;options.locked={'+','.join(quote(v)for v in case.get('locked',[]))+'};bool rejected=false;')
        args=','.join(quote(case[k])for k in ['source','target','position'])
        out.append('try{auto request=m.request_drop('+args+',options,'+('[](const DropRequest&){return false;}'if case.get('deny')else'DropPolicy{}')+');auto next=m.apply_drop(request);')
        if 'error'in case:out.append('assert(false);')
        else:
            collection='next.items()'if case['kind']=='tabs'else'next.nodes()'
            out.append('std::vector<std::string> ids;for(const auto&n:'+collection+')ids.push_back(n.id);assert(ids==std::vector<std::string>({'+','.join(quote(v)for v in case['order'])+'}));')
            if case['kind']=='tree':out.append('auto node=std::find_if(next.nodes().begin(),next.nodes().end(),[](const auto&n){return n.id=='+quote(case['source'])+';});assert(node!=next.nodes().end()&&node->parent=='+quote(case['parent'])+');')
        out.append('}catch(const DropError&e){rejected=true;assert(e.reason=='+quote(case.get('error','unexpected'))+');}assert(rejected=='+str('error'in case).lower()+');assert(drag_revision(m)==before);}')

    out.append(r"""
 {"""+cpp_model('tabs')+r"""DragState d;d.pointer(m,{"down",3,0,60,2});assert(!d.captured());d.enabled=true;auto before=drag_revision(m);auto active=m.active,focused=m.focused;int first=m.first;d.pointer(m,{"down",3,0,60,2});assert(d.captured());d.pointer(m,{"move",4,1,60,2});assert(d.phase=="armed");d.pointer(m,{"up",4,1,60,2});assert(d.result.empty()&&!d.captured());auto cells=m.layout(60);auto target=std::find_if(cells.begin(),cells.end(),[](auto c){return c.id=="c";});int x=target->start+target->width-1;d.pointer(m,{"down",3,0,60,2});d.pointer(m,{"move",x,0,60,2});assert(d.allowed);auto request=d.pointer(m,{"up",x,0,60,2});assert(request&&request->target_id=="c"&&d.result=="drop");assert(drag_revision(m)==before&&m.active==active&&m.focused==focused&&m.first==first);d.pointer(m,{"down",3,0,60,2});d.pointer(m,{"move",70,0,60,2});assert(!d.pointer(m,{"up",70,0,60,2})&&d.result=="reject");}
 {"""+cpp_model('tree')+r"""DragState d(true);DragOptions o;o.hover_expand=true;auto expanded=m.expanded;auto selected=m.selected;int scroll=m.scroll;d.pointer(m,{"down",6,3,24,6},o);d.pointer(m,{"move",10,4,24,6},o);assert(d.allowed&&!m.expanded.count("c"));auto preview=d.preview_layout(m,24,6);assert(preview.expanded.count("c")&&std::any_of(preview.rows.begin(),preview.rows.end(),[](auto n){return n.id=="c1";}));auto r=d.pointer(m,{"up",10,4,24,6},o);assert(r&&r->source_id=="b"&&r->target_id=="c"&&r->position=="inside");assert(m.expanded==expanded&&m.selected==selected&&m.scroll==scroll);bool allowed=true;auto policy=[&](const DropRequest&){return allowed;};d.pointer(m,{"down",6,3,24,6},o,policy);d.pointer(m,{"move",10,4,24,6},o,policy);allowed=false;assert(!d.pointer(m,{"up",10,4,24,6},o,policy)&&d.result=="reject");}
 for(int change=0;change<4;change++){"""+cpp_model('tabs')+r"""DragState d(true);Canvas initial(60,2);d.draw(m,initial,{0,0,60,2});d.pointer(m,{"down",3,0,60,2});if(change==0)m.focused="b";else if(change==1){auto items=m.items();items[0].title="changed";m=Tabs(items);}Canvas next(change==2?59:60,2,change==3?Palette("light","8"):Palette());d.draw(m,next,{0,0,next.width,2});assert(!d.captured()&&d.result=="stale");}
 {"""+cpp_model('tabs')+r"""auto r=m.request_drop("a","c","after");auto items=m.items();items[0].edited=false;Tabs changed(items);bool stale=false;try{changed.apply_drop(r);}catch(const DropError&e){stale=e.reason=="stale";}assert(stale);m.focused="c";auto key=m.keyboard_drop("previous");assert(key.source_id=="c"&&key.target_id=="b"&&key.position=="before");auto n=m.apply_drop(key);assert(n.focused=="c"&&n.items()[0].edited);}
 {"""+cpp_model('tree')+r"""m.selected="b";auto r=m.keyboard_drop("inside");assert(r.target_id=="a"&&r.position=="inside");auto n=m.apply_drop(r);assert(n.selected=="b");auto outside=n.keyboard_drop("outside");assert(outside.target_id=="a"&&outside.position=="after");}
 {"""+cpp_model('tabs')+r"""DragState d(true);d.pointer(m,{"down",3,0,60,1});bool failed=false;try{d.pointer(m,{"move",10,0,-1,1});}catch(const DropError&e){failed=e.reason=="pointer";}assert(failed&&d.phase=="armed");auto cells=m.layout(60);auto target=std::find_if(cells.begin(),cells.end(),[](auto c){return c.id=="c";});d.pointer(m,{"move",target->start+target->width-1,0,60,1},DragOptions{},[&](const DropRequest&){d.cancel();return true;});assert(!d.allowed&&d.reason=="policy");}
 {std::vector<Node> nodes;Node root;root.id="n0";nodes.push_back(root);for(int i=1;i<129;i++){Node n;n.id="n"+std::to_string(i);n.parent="n"+std::to_string(i-1);n.branch=i==128;nodes.push_back(n);}Node move;move.id="move";nodes.push_back(move);Tree m(nodes);bool deep=false;try{m.request_drop("move","n128","inside");}catch(const DropError&e){deep=e.reason=="depth";}assert(deep);}
 {"""+cpp_model('tabs')+r"""DragState d(true);Canvas c(60,2);d.draw(m,c,{0,0,60,2});d.pointer(m,{"down",3,0,60,2});bool invalid=false;try{d.draw(m,c,{0,0,65536,2});}catch(const DropError&e){invalid=e.reason=="bounds";}assert(invalid&&d.phase=="armed");d.draw(m,c,{0,0,60,2},false);assert(d.result=="cancel"&&!d.captured());}
""")
    for theme in ['dark','light','blackwhite']:
        for colors in ['8','16','256','truecolor']:
            for ascii in [False,True]:
                out.append('{'+cpp_model('tree')+'auto expanded=m.expanded;DragState d(true);Canvas c(28,8,Palette('+quote(theme)+','+quote(colors)+'),"button.focus");Rect area{1,1,24,6};d.draw(m,c,area,true,'+str(ascii).lower()+');d.pointer(m,{"down",6,3,24,6});d.pointer(m,{"move",10,4,24,6});d.draw(m,c,area,true,'+str(ascii).lower()+');const auto&marker=c.data[5][1];assert(marker.text=='+quote('+'if ascii else'↳')+'&&marker.style.bold&&marker.style.underline&&marker.style.background==c.palette.style("button.focus").background&&!c.cursor);assert(m.expanded==expanded&&m.scroll==0);std::cout<<"FEEDBACK|'+theme+'|'+colors+'|'+str(int(ascii))+'\\n"<<c.ansi()<<"\\nEND\\n";}')
    out.append('return 0;}');return '\n'.join(out)

def validate_output(output):
    from ansi_cells import read_cells
    palettes=json.loads((ROOT/'design/tokens/candidate.json').read_text())['palettes'];frames=0
    for block in output.split('\nEND\n'):
        if not block.strip():continue
        header,ansi=block.split('\n',1);kind,theme,colors,ascii=header.split('|');assert kind=='FEEDBACK'
        frame=read_cells(ansi);marker=frame[1,5]
        assert marker[0]==('+'if ascii=='1'else'↳') and marker[2]==palettes[theme+'-'+colors]['button.focus']['background'] and marker[3]and marker[5],header
        assert '\x1b[?25h'not in ansi,header;frames+=1
    assert frames==24,frames

def java_model(kind):
    out=[]
    if kind=='tabs':
        out.append('var items=new ArrayList<Tab>();')
        for t in F['tabs']:
            out.append('{var t=new Tab('+quote(t['id'])+','+quote(t.get('title',''))+');')
            for prop in ['edited','closable','disabled']:
                out.append('t.'+prop+'='+str(t.get(prop,False)).lower()+';')
            out.append('items.add(t);}')
        out.append('var m=new Tabs(items);')
    else:
        out.append('var nodes=new ArrayList<Node>();')
        for n in F['tree']:
            out.append('{var n=new Node('+quote(n['id'])+','+quote(n.get('name',''))+','+quote(n.get('parent',''))+');')
            for prop,field in [('secondary','secondary'),('icon','icon'),('ascii_icon','asciiIcon')]:
                out.append('n.'+field+'='+quote(n.get(prop,''))+';')
            out.append('n.branch='+str(n.get('branch',False)).lower()+';')
            if 'count' in n:out.append('n.count='+str(n['count'])+'L;')
            out.append('nodes.add(n);}')
        out.append('var m=new Tree(nodes);m.expanded.addAll(List.of("root","a"));')
    return ''.join(out)

def java_source():
    out=['import static io.tuivory.Tuivory.*;','import java.util.*;','public class DragCases {public static void main(String[] args){']
    for case in F['cases']:
        out.append('{'+java_model(case['kind'])+'var before=dragRevision(m);assert before.equals('+quote(F['tab_revision_hex'if case['kind']=='tabs'else'tree_revision_hex'])+');var options=new DragOptions();options.locked=List.of('+','.join(quote(v)for v in case.get('locked',[]))+');boolean rejected=false;')
        args=','.join(quote(case[k])for k in ['source','target','position'])
        out.append('try{var request=m.requestDrop('+args+',options,'+('r->false'if case.get('deny')else'null')+');var next=m.applyDrop(request);')
        if 'error'in case:out.append('throw new AssertionError("expected rejection");')
        else:
            collection='next.items()'if case['kind']=='tabs'else'next.nodes()'
            out.append('assert '+collection+'.stream().map(n->n.id).toList().equals(List.of('+','.join(quote(v)for v in case['order'])+'));')
            if case['kind']=='tree':out.append('assert next.nodes().stream().filter(n->n.id.equals('+quote(case['source'])+')).findFirst().orElseThrow().parent.equals('+quote(case['parent'])+');')
        out.append('}catch(DropError e){rejected=true;assert e.reason.equals('+quote(case.get('error','unexpected'))+'):e.reason;}assert rejected=='+str('error'in case).lower()+';assert dragRevision(m).equals(before);}')
    out.append('{'+java_model('tabs')+'var r=m.requestDrop("a","c","after");var items2=m.items();items2.get(0).title="changed";var changed=new Tabs(items2);boolean stale=false;try{changed.applyDrop(r);}catch(DropError e){stale=e.reason.equals("stale");}assert stale;assert dragRevision(m).equals('+quote(F['tab_revision_hex'])+');m.focused="c";var key=m.keyboardDrop("previous");assert key.sourceId().equals("c")&&key.targetId().equals("b")&&key.position().equals("before");var n=m.applyDrop(key);assert n.focused.equals("c")&&n.items().get(0).edited;}')
    out.append('{'+java_model('tree')+'m.selected="b";var r=m.keyboardDrop("inside");assert r.targetId().equals("a")&&r.position().equals("inside");var n=m.applyDrop(r);assert n.selected.equals("b");var outside=n.keyboardDrop("outside");assert outside.targetId().equals("a")&&outside.position().equals("after");}')
    out.append('{'+java_model('tabs')+'''var d=new DragState();d.pointer(m,new DragPointer("down",3,0,60,2));assert !d.captured();d.enabled=true;var before=dragRevision(m);var active=m.active;var focused=m.focused;int first=m.first;d.pointer(m,new DragPointer("down",3,0,60,2));assert d.captured();d.pointer(m,new DragPointer("move",4,1,60,2));assert d.phase.equals("armed");d.pointer(m,new DragPointer("up",4,1,60,2));assert d.result.isEmpty()&&!d.captured();var cells=m.layout(60);var target=cells.stream().filter(c->c.id().equals("c")).findFirst().orElseThrow();int x=target.start()+target.width()-1;d.pointer(m,new DragPointer("down",3,0,60,2));d.pointer(m,new DragPointer("move",x,0,60,2));assert d.allowed;var r=d.pointer(m,new DragPointer("up",x,0,60,2));assert r!=null&&r.targetId().equals("c")&&d.result.equals("drop");assert dragRevision(m).equals(before)&&m.active.equals(active)&&m.focused.equals(focused)&&m.first==first;d.pointer(m,new DragPointer("down",3,0,60,2));d.pointer(m,new DragPointer("move",70,0,60,2));assert d.pointer(m,new DragPointer("up",70,0,60,2))==null&&d.result.equals("reject");}''')
    out.append('{'+java_model('tree')+'''var d=new DragState(true);var o=new DragOptions();o.hoverExpand=true;var expanded=Set.copyOf(m.expanded);var selected=m.selected;int scroll=m.scroll;d.pointer(m,new DragPointer("down",6,3,24,6),o,null);d.pointer(m,new DragPointer("move",10,4,24,6),o,null);assert d.allowed&&!m.expanded.contains("c");var preview=d.previewLayout(m,24,6);assert preview.expanded().contains("c")&&preview.rows().stream().anyMatch(n->n.id.equals("c1"));var r=d.pointer(m,new DragPointer("up",10,4,24,6),o,null);assert r!=null&&r.sourceId().equals("b")&&r.targetId().equals("c")&&r.position().equals("inside");assert m.expanded.equals(expanded)&&m.selected.equals(selected)&&m.scroll==scroll;boolean[] allow={true};DropPolicy policy=request->allow[0];d.pointer(m,new DragPointer("down",6,3,24,6),o,policy);d.pointer(m,new DragPointer("move",10,4,24,6),o,policy);allow[0]=false;assert d.pointer(m,new DragPointer("up",10,4,24,6),o,policy)==null&&d.result.equals("reject");}''')
    out.append('for(int change=0;change<4;change++){'+java_model('tabs')+'''var d=new DragState(true);var initial=new Canvas(60,2);d.draw(m,initial,new Rect(0,0,60,2),true,false);d.pointer(m,new DragPointer("down",3,0,60,2));if(change==0)m.focused="b";else if(change==1){var values=m.items();values.get(0).title="changed";m=new Tabs(values);}var next=new Canvas(change==2?59:60,2,change==3?new Palette("light","8"):new Palette());d.draw(m,next,new Rect(0,0,next.width,2),true,false);assert !d.captured()&&d.result.equals("stale");}''')
    out.append('{'+java_model('tabs')+'''var d=new DragState(true);d.pointer(m,new DragPointer("down",3,0,60,1));boolean failed=false;try{d.pointer(m,new DragPointer("move",10,0,-1,1));}catch(DropError e){failed=e.reason.equals("pointer");}assert failed&&d.phase.equals("armed");var target=m.layout(60).stream().filter(c->c.id().equals("c")).findFirst().orElseThrow();d.pointer(m,new DragPointer("move",target.start()+target.width()-1,0,60,1),null,r->{d.cancel();return true;});assert !d.allowed&&d.reason.equals("policy");}''')
    out.append('''{var nodes=new ArrayList<Node>();nodes.add(new Node("n0","root"));for(int i=1;i<129;i++){var n=new Node("n"+i,"n","n"+(i-1));n.branch=i==128;nodes.add(n);}nodes.add(new Node("move","move"));var m=new Tree(nodes);boolean deep=false;try{m.requestDrop("move","n128","inside");}catch(DropError e){deep=e.reason.equals("depth");}assert deep;}''')
    out.append('{'+java_model('tabs')+'''var d=new DragState(true);var c=new Canvas(60,2);d.draw(m,c,new Rect(0,0,60,2),true,false);d.pointer(m,new DragPointer("down",3,0,60,2));boolean invalid=false;try{d.draw(m,c,new Rect(0,0,65536,2),true,false);}catch(DropError e){invalid=e.reason.equals("bounds");}assert invalid&&d.phase.equals("armed");d.draw(m,c,new Rect(0,0,60,2),false,false);assert d.result.equals("cancel")&&!d.captured();}''')
    for theme in ['dark','light','blackwhite']:
        for colors in ['8','16','256','truecolor']:
            for ascii in [False,True]:
                out.append('{'+java_model('tree')+'var expanded=Set.copyOf(m.expanded);var d=new DragState(true);var c=new Canvas(28,8,new Palette('+quote(theme)+','+quote(colors)+'),"button.focus");var area=new Rect(1,1,24,6);d.draw(m,c,area,true,'+str(ascii).lower()+');d.pointer(m,new DragPointer("down",6,3,24,6));d.pointer(m,new DragPointer("move",10,4,24,6));d.draw(m,c,area,true,'+str(ascii).lower()+');var marker=c.data[5][1];assert marker.text.equals('+quote('+'if ascii else'↳')+')&&marker.style.bold()&&marker.style.underline()&&marker.style.background()==c.palette.style("button.focus").background()&&c.cursorX<0;assert m.expanded.equals(expanded)&&m.scroll==0;System.out.print("FEEDBACK|'+theme+'|'+colors+'|'+str(int(ascii))+'\\n"+c.ansi()+"\\nEND\\n");}')
    out.append('}}')
    return chr(10).join(out)

def c_model(kind):
    if kind=='tabs':
        rows=['{'+','.join([quote(t['id']),quote(t.get('title','')),*[str(int(t.get(k,False)))for k in ['edited','closable','disabled']]])+'}'for t in F['tabs']]
        return 'TuiTab items[]={'+','.join(rows)+'};TuiTabs*m=tui_tabs_new(items,sizeof(items)/sizeof(items[0]));assert(m);'
    rows=[]
    for n in F['tree']:
        fields=[quote(n.get(k,''))for k in ['id','name','parent','secondary','icon','ascii_icon']]+[str(int(n.get('branch',False))),str(int('count'in n)),str(n.get('count',0))+'ull']
        rows.append('{'+','.join(fields)+'}')
    return 'TuiNode nodes[]={'+','.join(rows)+'};TuiTree*m=tui_tree_new(nodes,sizeof(nodes)/sizeof(nodes[0]));assert(m);tui_tree_handle(m,"toggle",6);tui_tree_handle(m,"down",6);tui_tree_handle(m,"toggle",6);'

def c_source():
    out=['#include "tuivory.h"','#include <assert.h>','#include <stdio.h>','#include <string.h>',
         'static int deny(void*c,const TuiDropRequest*r){(void)c;(void)r;return 0;}',
         'static int policy(void*c,const TuiDropRequest*r){(void)r;return *(int*)c;}',
         'static int reenter(void*c,const TuiDropRequest*r){(void)r;assert(tui_drag_cancel(c)==TUI_INVALID);return 0;}',
         'int main(void){']
    for case in F['cases']:
        kind=case['kind'];prefix='tui_tabs_'if kind=='tabs'else'tui_tree_'
        out.append('{'+c_model(kind)+'char before[17],after[17];assert('+prefix+'drag_revision(m,before)==TUI_OK);assert(!strcmp(before,'+quote(F['tab_revision_hex'if kind=='tabs'else'tree_revision_hex'])+'));const char*reason="";TuiDragOptions options={0};')
        if case.get('locked'):out.append('const char*locked[]={'+','.join(quote(v)for v in case['locked'])+'};options.locked=locked;options.locked_count=sizeof(locked)/sizeof(locked[0]);')
        args=','.join(quote(case[k])for k in ['source','target','position'])
        out.append('TuiDropRequest*r='+prefix+'request_drop(m,'+args+',&options,'+('deny'if case.get('deny')else'NULL')+',NULL,&reason);')
        if 'error'in case:out.append('assert(!r&&!strcmp(reason,'+quote(case['error'])+'));')
        else:
            out.append(('TuiTabs'if kind=='tabs'else'TuiTree')+'*next='+prefix+'apply_drop(m,r,&reason);assert(r&&next&&!*reason);assert('+prefix+'count(next)=='+str(len(case['order']))+');')
            getter='tui_tabs_item'if kind=='tabs'else'tui_tree_node'
            for i,id in enumerate(case['order']):out.append('assert(!strcmp('+getter+'(next,'+str(i)+')->id,'+quote(id)+'));')
            if kind=='tree':
                i=case['order'].index(case['source']);out.append('assert(!strcmp(tui_tree_node(next,'+str(i)+')->parent,'+quote(case['parent'])+'));')
            out.append(prefix+'free(next);')
        out.append('assert('+prefix+'drag_revision(m,after)==TUI_OK&&!strcmp(before,after));tui_drop_request_free(r);'+prefix+'free(m);}')
    out.append('{'+c_model('tabs')+'''TuiDragState*d=tui_drag_new(0);TuiDropRequest*r=NULL;TuiDragPointer down={"down",3,0,60,2};assert(tui_drag_tabs_pointer(d,m,down,NULL,NULL,NULL,&r)==TUI_OK&&!r&&!tui_drag_view(d).captured);tui_drag_enable(d,1);assert(tui_drag_tabs_pointer(d,m,down,NULL,NULL,NULL,&r)==TUI_OK&&tui_drag_view(d).captured);assert(tui_drag_tabs_pointer(d,m,(TuiDragPointer){"move",4,1,60,2},NULL,NULL,NULL,&r)==TUI_OK&&!strcmp(tui_drag_view(d).phase,"armed"));assert(tui_drag_tabs_pointer(d,m,(TuiDragPointer){"up",4,1,60,2},NULL,NULL,NULL,&r)==TUI_OK&&!r&&!tui_drag_view(d).captured&&!*tui_drag_view(d).result);TuiTabCell cells[10];size_t count;assert(tui_tabs_layout(m,60,cells,10,&count)==TUI_OK);int x=0;for(size_t i=0;i<count;i++)if(!strcmp(cells[i].id,"c"))x=cells[i].start+cells[i].width-1;char before[17],after[17];tui_tabs_drag_revision(m,before);assert(tui_drag_tabs_pointer(d,m,down,NULL,NULL,NULL,&r)==TUI_OK);assert(tui_drag_tabs_pointer(d,m,(TuiDragPointer){"move",x,0,60,2},NULL,NULL,NULL,&r)==TUI_OK&&tui_drag_view(d).allowed);assert(tui_drag_tabs_pointer(d,m,(TuiDragPointer){"up",x,0,60,2},NULL,NULL,NULL,&r)==TUI_OK&&r&&!strcmp(r->target_id,"c")&&!strcmp(tui_drag_view(d).result,"drop"));tui_tabs_drag_revision(m,after);assert(!strcmp(before,after));tui_drop_request_free(r);assert(tui_drag_tabs_pointer(d,m,down,NULL,NULL,NULL,&r)==TUI_OK);assert(tui_drag_tabs_pointer(d,m,(TuiDragPointer){"move",70,0,60,2},NULL,NULL,NULL,&r)==TUI_OK);assert(tui_drag_tabs_pointer(d,m,(TuiDragPointer){"up",70,0,60,2},NULL,NULL,NULL,&r)==TUI_OK&&!r&&!strcmp(tui_drag_view(d).result,"reject"));assert(tui_drag_tabs_pointer(d,m,down,NULL,NULL,NULL,&r)==TUI_OK);assert(tui_drag_tabs_pointer(d,m,(TuiDragPointer){"move",10,0,-1,1},NULL,NULL,NULL,&r)==TUI_INVALID&&!strcmp(tui_drag_view(d).phase,"armed"));assert(tui_drag_tabs_pointer(d,m,(TuiDragPointer){"move",x,0,60,2},NULL,reenter,d,&r)==TUI_OK&&!tui_drag_view(d).allowed&&!strcmp(tui_drag_view(d).reason,"policy"));tui_drag_free(d);tui_tabs_free(m);}''')
    out.append('{'+c_model('tree')+'''TuiDragState*d=tui_drag_new(1);TuiDropRequest*r=NULL;TuiDragOptions o={0};o.hover_expand=1;int scroll=tui_tree_scroll(m);char selected[100];snprintf(selected,sizeof(selected),"%s",tui_tree_selected(m));assert(tui_drag_tree_pointer(d,m,(TuiDragPointer){"down",6,3,24,6},&o,NULL,NULL,&r)==TUI_OK);assert(tui_drag_tree_pointer(d,m,(TuiDragPointer){"move",10,4,24,6},&o,NULL,NULL,&r)==TUI_OK&&tui_drag_view(d).allowed&&!tui_tree_expanded(m,"c"));TuiDragLayout*l=tui_drag_tree_preview(d,m,24,6);assert(l&&tui_tree_expanded(l->tree,"c"));const char*ids[20];size_t count=tui_tree_visible(l->tree,ids,20);int found=0;for(size_t i=0;i<count;i++)if(!strcmp(ids[i],"c1"))found=1;assert(found);tui_drag_layout_free(l);assert(tui_drag_tree_pointer(d,m,(TuiDragPointer){"up",10,4,24,6},&o,NULL,NULL,&r)==TUI_OK&&r&&!strcmp(r->source_id,"b")&&!strcmp(r->target_id,"c")&&!strcmp(r->position,"inside"));assert(!tui_tree_expanded(m,"c")&&tui_tree_scroll(m)==scroll&&!strcmp(tui_tree_selected(m),selected));tui_drop_request_free(r);int allow=1;assert(tui_drag_tree_pointer(d,m,(TuiDragPointer){"down",6,3,24,6},&o,policy,&allow,&r)==TUI_OK);assert(tui_drag_tree_pointer(d,m,(TuiDragPointer){"move",10,4,24,6},&o,policy,&allow,&r)==TUI_OK);allow=0;assert(tui_drag_tree_pointer(d,m,(TuiDragPointer){"up",10,4,24,6},&o,policy,&allow,&r)==TUI_OK&&!r&&!strcmp(tui_drag_view(d).result,"reject"));tui_drag_free(d);tui_tree_free(m);}''')
    out.append('for(int change=0;change<3;change++){'+c_model('tabs')+'''TuiDragState*d=tui_drag_new(1);TuiDropRequest*r=NULL;TuiCanvas*c=tui_canvas_new(60,2,"dark","256");assert(tui_drag_tabs_draw(d,m,c,(TuiRect){0,0,60,2},1,0)==TUI_OK);assert(tui_drag_tabs_pointer(d,m,(TuiDragPointer){"down",3,0,60,2},NULL,NULL,NULL,&r)==TUI_OK);if(change==0)tui_tabs_handle(m,"next");TuiCanvas*next=tui_canvas_new(change==1?59:60,2,change==2?"light":"dark",change==2?"8":"256");assert(tui_drag_tabs_draw(d,m,next,(TuiRect){0,0,change==1?59:60,2},1,0)==TUI_OK&&!tui_drag_view(d).captured&&!strcmp(tui_drag_view(d).result,"stale"));tui_canvas_free(c);tui_canvas_free(next);tui_drag_free(d);tui_tabs_free(m);}''')
    # Parent-only moves must not be classified as unchanged (Java regression).
    out.append('{'+c_model('tree')+'''const char*reason;TuiDropRequest*r=tui_tree_request_drop(m,"b","a","inside",NULL,NULL,NULL,&reason);assert(r);TuiTree*n=tui_tree_apply_drop(m,r,&reason);assert(n);for(size_t i=0;i<tui_tree_count(n);i++)if(!strcmp(tui_tree_node(n,i)->id,"b"))assert(!strcmp(tui_tree_node(n,i)->parent,"a"));tui_drop_request_free(r);tui_tree_free(n);tui_tree_free(m);}''')
    for theme in ['dark','light','blackwhite']:
        for colors in ['8','16','256','truecolor']:
            for ascii in [False,True]:
                out.append('{'+c_model('tree')+'TuiDragState*d=tui_drag_new(1);TuiDropRequest*r=NULL;TuiCanvas*c=tui_canvas_new(28,8,'+quote(theme)+','+quote(colors)+');assert(c);assert(tui_canvas_surface(c,"button.focus")==TUI_OK);assert(tui_drag_tree_draw(d,m,c,(TuiRect){1,1,24,6},1,'+str(int(ascii))+')==TUI_OK);assert(tui_drag_tree_pointer(d,m,(TuiDragPointer){"down",6,3,24,6},NULL,NULL,NULL,&r)==TUI_OK);assert(tui_drag_tree_pointer(d,m,(TuiDragPointer){"move",10,4,24,6},NULL,NULL,NULL,&r)==TUI_OK);assert(tui_drag_tree_draw(d,m,c,(TuiRect){1,1,24,6},1,'+str(int(ascii))+')==TUI_OK);assert(!tui_tree_expanded(m,"c"));char*ansi=tui_canvas_ansi(c);assert(ansi);printf("FEEDBACK|'+theme+'|'+colors+'|'+str(int(ascii))+'\\n%s\\nEND\\n",ansi);tui_string_free(ansi);tui_canvas_free(c);tui_drag_free(d);tui_tree_free(m);}')
    out.append('return 0;}');return chr(10).join(out)

def source(language):
    return {'c':c_source,'cpp':cpp_source,'java':java_source}[language]()

def main():
    p=argparse.ArgumentParser();p.add_argument('--language',choices=['c','cpp','java'],required=True);lang=p.parse_args().language
    artifact=build(lang)
    with tempfile.TemporaryDirectory(prefix='tuivory-drag-')as directory:
        base=Path(directory)
        if lang=='java':
            shutil.copy2(artifact,base/'tuivory.jar');src=base/'DragCases.java';src.write_text(java_source())
            run(['javac','--release','17','-encoding','UTF-8','-Xlint:all','-Werror','-cp',base/'tuivory.jar',src],base)
            validate_output(subprocess.check_output(['java','-ea','-cp',str(base/'tuivory.jar')+os.pathsep+str(base),'DragCases'],cwd=base,text=True))
            print('java:22 shared immutable cases/FNV64, captured previews and24 actual feedback frames passed')
            return
        shutil.copytree(ROOT/lang/'include',base/'include');src=base/('drag.c'if lang=='c'else'drag.cpp');src.write_text(c_source()if lang=='c'else cpp_source())
        flags=['cc'if lang=='c'else'c++','-std=c11'if lang=='c'else'-std=c++17','-Wall','-Wextra','-Werror','-I',base/'include',src]
        run(flags+([ROOT/'c/src/tuivory.c']if lang=='c'else[])+['-fsanitize=address,undefined','-o',base/'checked'],base)
        validate_output(subprocess.check_output([base/'checked'],cwd=base,text=True,env=dict(os.environ,ASAN_OPTIONS=os.environ.get('ASAN_OPTIONS','detect_leaks=0'))))
        if lang=='c':
            shutil.copy2(ROOT/'.cache/native/c/libtuivory.a',base/'libtuivory.a');flags+=[base/'libtuivory.a']
        run(flags+['-static','-o',base/'isolated'],base);validate_output(subprocess.check_output([base/'isolated'],cwd=base,text=True))
    print(lang+':22 shared immutable cases/FNV64, captured previews and24 actual feedback frames passed')
if __name__=='__main__':main()
