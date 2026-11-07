#!/usr/bin/env python3
"""Exercise independent grid pointer APIs in copied SDKs and actual ANSI output."""
import argparse,json,os,re,shutil,subprocess,tempfile
from pathlib import Path
from check_languages import ROOT,quote,run
from ansi_cells import read_cells
F=json.loads((ROOT/'design/grid-pointer-cases.json').read_text())
PALETTES=json.loads((ROOT/'design/tokens/candidate.json').read_text())['palettes']

def c_prolog():
    out=['#include "tuivory.h"','#include <assert.h>','#include <stdio.h>','#include <string.h>']
    for i,r in enumerate(F['rows']):
        out.append('static const TuiGridCell cells'+str(i)+'[]={{.column_id="a",.text='+quote(r['a'])+'},{.column_id="b",.text="b"},{.column_id="c",.text="c"}};')
    out.append('static TuiGridRecord rows[]={'+','.join('{.id='+quote(r['id'])+',.cells=cells'+str(i)+',.cell_count=3,.state={.disabled='+str(int(r.get('disabled',False)))+',.read_only='+str(int(r.get('read_only',False)))+'}}'for i,r in enumerate(F['rows']))+'};')
    out.append('static const TuiGridColumn columns[]={'+','.join('{.id='+quote(c['id'])+',.label='+quote(c['id'].upper())+',.width='+str(c['width'])+',.editable=1}'for c in F['columns'])+'};')
    out.append(r'''
static TuiGrid*model(void){
 TuiGrid*g=tui_grid_new(columns,3,rows,4);assert(g);
 TuiGridOptions o;assert(tui_grid_preset("data",&o)==TUI_OK);assert(tui_grid_configure(g,&o)==TUI_OK);
 assert(tui_grid_set_column_options(g,"a",(TuiGridColumnOptions){.min_width=4,.max_width=14})==TUI_OK);
 assert(tui_grid_set_edit_options(g,(TuiGridEditOptions){.enabled=1})==TUI_OK);return g;
}
static TuiResult source_row(void*ctx,size_t index,TuiGridRecord*out){int*order=ctx;if(index>=4)return TUI_INVALID;*out=rows[order[index]];return TUI_OK;}
static TuiResult source_index(void*ctx,const char*id,size_t*out){int*order=ctx;for(size_t i=0;i<4;i++){if(!strcmp(rows[order[i]].id,id)){*out=i;return TUI_OK;}}return TUI_INVALID;}
typedef struct{int x,y;} Point;
static Point point(TuiGrid*g,int w,int h,int ox,int oy,const char*kind,int index,const char*id,int dx,int dy){
 if(!strcmp(kind,"outside"))return (Point){-3,h+3};
 if(!strcmp(kind,"delta"))return (Point){ox+dx,oy+dy};
 TuiGridGeometry*geo=NULL;assert(tui_grid_geometry(g,w,h,&geo)==TUI_OK);TuiGridGeometryInfo q=tui_grid_geometry_info(geo);
 Point p={0,q.header_rows+(index-(int)q.top)*q.stride};
 for(size_t i=0;i<tui_grid_span_count(geo);i++){const TuiGridSpan*s=tui_grid_span_at(geo,i);if(!strcmp(s->id,id))p.x=s->x+(!strcmp(kind,"divider")?s->width:!strcmp(kind,"editor")?tui_grid_options(g)->padding+dx:0);}
 if(!strcmp(kind,"header")||!strcmp(kind,"divider"))p.y=0;
 tui_grid_geometry_free(geo);return p;
}
static TuiCanvas*canvas(TuiGrid*g,int w,int h,const char*theme,const char*colors,int focused,int ascii){TuiCanvas*c=tui_canvas_new(w,h,theme,colors);assert(c);assert(tui_grid_draw(g,c,(TuiRect){0,0,w,h},focused,ascii)==TUI_OK);return c;}
static void paint(TuiGrid*g,int w,int h){tui_canvas_free(canvas(g,w,h,"dark","8",1,0));}
static void range(TuiGrid*g,const char*a,const char*b,const char*c,const char*d){const TuiGridRange*r=tui_grid_selection(g);assert(r&&!strcmp(r->anchor_row,a)&&!strcmp(r->anchor_column,b)&&!strcmp(r->end_row,c)&&!strcmp(r->end_column,d));}
static void width_is(TuiGrid*g,const char*id,int width){size_t n;const TuiGridColumn*c=tui_grid_columns(g,&n);for(size_t i=0;i<n;i++){if(!strcmp(c[i].id,id)){assert(c[i].width==width);return;}}assert(0);}
int main(void){
''')
    return out

def cpp_prolog():
    out=['#include "tuivory.hpp"','#include <cassert>','#include <iostream>','using namespace tuivory;']
    out.append('static std::vector<GridRecord> records(){std::vector<GridRecord> out;')
    for r in F['rows']:
        out.append('{GridRecord r;r.id='+quote(r['id'])+';r.cells={{"a",'+quote(r['a'])+'},{"b","b"},{"c","c"}};r.state.disabled='+str(r.get('disabled',False)).lower()+';r.state.read_only='+str(r.get('read_only',False)).lower()+';out.push_back(r);}')
    out.append('return out;}')
    out.append('static std::vector<GridColumn> cols(){return {'+','.join('{'+','.join([quote(c['id']),quote(c['id'].upper()),str(c['width']),'true','false','""'])+'}'for c in F['columns'])+'};}')
    out.append(r'''
struct Source:GridSource{std::vector<GridRecord> rows=records();std::size_t size()const override{return rows.size();}GridRecord row(std::size_t i)const override{return rows.at(i);}std::optional<std::size_t> index_of(const std::string&id)const override{for(std::size_t i=0;i<rows.size();i++){if(rows[i].id==id)return i;}return std::nullopt;}};
static Grid model(std::shared_ptr<const GridSource> source=nullptr){Grid g=source?Grid(cols(),source):Grid(cols(),records());g.set_options(grid_preset("data"));GridColumnOptions c;c.min_width=4;c.max_width=14;g.set_column_options("a",c);GridEditOptions e;e.enabled=true;g.set_edit_options(e);return g;}
struct Point{int x,y;};
static Point point(Grid&g,int w,int h,int ox,int oy,const std::string&kind,int index,const std::string&id,int dx,int dy){
 if(kind=="outside"){return {-3,h+3};}if(kind=="delta"){return {ox+dx,oy+dy};}
 auto geo=g.geometry(w,h);Point p{0,geo.header_rows+(index-int(geo.top))*geo.stride};
 for(const auto&s:geo.columns)if(s.id==id)p.x=s.x+(kind=="divider"?s.width:kind=="editor"?g.options().padding+dx:0);
 if(kind=="header"||kind=="divider"){p.y=0;}return p;
}
static Canvas canvas(Grid&g,int w,int h,const std::string&theme,const std::string&colors,bool focused,bool ascii){Canvas c(w,h,Palette(theme,colors));g.draw(c,{0,0,w,h},focused,ascii);return c;}
static void paint(Grid&g,int w,int h){canvas(g,w,h,"dark","8",true,false);}
static void range(Grid&g,const std::string&a,const std::string&b,const std::string&c,const std::string&d){assert(g.selected&&g.selected->anchor_row==a&&g.selected->anchor_column==b&&g.selected->end_row==c&&g.selected->end_column==d);}
static void width_is(Grid&g,const std::string&id,int width){auto c=std::find_if(g.columns.begin(),g.columns.end(),[&](auto&v){return v.id==id;});assert(c!=g.columns.end()&&c->width==width);}
int main(){
''')
    return out

def java_prolog():
    out=['import static io.tuivory.Tuivory.*;','import java.util.*;','public class GridPointerCases {','static List<GridRecord> records(){var out=new ArrayList<GridRecord>();']
    for r in F['rows']:
        out.append('{var r=new GridRecord('+quote(r['id'])+');r.cells.put("a",'+quote(r['a'])+');r.cells.put("b","b");r.cells.put("c","c");r.state.disabled='+str(r.get('disabled',False)).lower()+';r.state.readOnly='+str(r.get('read_only',False)).lower()+';out.add(r);}')
    out.append('return out;}')
    out.append('static List<GridColumn> cols(){return List.of('+','.join('new GridColumn('+','.join([quote(c['id']),quote(c['id'].upper()),str(c['width']),'true'])+')'for c in F['columns'])+');}')
    out.append(r'''
static final class Source implements GridSource{List<GridRecord> rows=records();public int size(){return rows.size();}public GridRecord row(int i){return rows.get(i);}public OptionalInt indexOf(String id){for(int i=0;i<rows.size();i++){if(rows.get(i).id.equals(id))return OptionalInt.of(i);}return OptionalInt.empty();}}
static Grid model(GridSource source){var g=source==null?new Grid(cols(),records()):new Grid(cols(),source);g.setOptions(gridPreset("data"));var c=new GridColumnOptions();c.minWidth=4;c.maxWidth=14;g.setColumnOptions("a",c);var e=new GridEditOptions();e.enabled=true;g.setEditOptions(e);return g;}
record Point(int x,int y){}
static Point point(Grid g,int w,int h,int ox,int oy,String kind,int index,String id,int dx,int dy){
 if(kind.equals("outside"))return new Point(-3,h+3);if(kind.equals("delta"))return new Point(ox+dx,oy+dy);
 var geo=g.geometry(w,h);int x=0,y=geo.headerRows()+(index-geo.top())*geo.stride();
 for(var s:geo.columns())if(s.id().equals(id))x=s.x()+(kind.equals("divider")?s.width():kind.equals("editor")?g.options().padding+dx:0);
 if(kind.equals("header")||kind.equals("divider"))y=0;return new Point(x,y);
}
static Canvas canvas(Grid g,int w,int h,String theme,String colors,boolean focused,boolean ascii){var c=new Canvas(w,h,new Palette(theme,colors));g.draw(c,new Rect(0,0,w,h),focused,ascii);return c;}
static void paint(Grid g,int w,int h){canvas(g,w,h,"dark","8",true,false);}
static void range(Grid g,String a,String b,String c,String d){assert new GridRange(a,b,c,d).equals(g.selected);}
static void width_is(Grid g,String id,int width){assert g.columns.stream().filter(v->v.id.equals(id)).findFirst().orElseThrow().width==width;}
public static void main(String[] args){
''')
    return out

def args_at(at):
    kind,*parts=at
    index=next((i for i,r in enumerate(F['rows'])if parts and r['id']==parts[0]),0)
    col=parts[0]if kind in ('header','divider')else parts[1]if kind in ('cell','editor')else ''
    dx=parts[0]if kind=='delta'else parts[2]if kind=='editor'else 0
    dy=parts[1]if kind=='delta'else 0
    return ','.join([quote(kind),str(index),quote(col),str(dx),str(dy)])

def source(lang):
    c=lang=='c';java=lang=='java'
    out=({'c':c_prolog,'cpp':cpp_prolog,'java':java_prolog}[lang])()
    boolean=lambda value:str(int(value))if c else str(bool(value)).lower()
    check=lambda expr:'assert '+expr+';'if java else'assert('+expr+');'
    equal=lambda value,text:(value+'.equals('+quote(text)+')')if java else('!strcmp('+value+','+quote(text)+')')if c else value+'=='+quote(text)
    create='TuiGrid*g=model();'if c else 'var g=model(null);'if java else'auto g=model();'
    x,y=('p.x()','p.y()')if java else('p.x','p.y')
    event='TuiGridEvent e;'if c else 'GridEvent e;'
    captured='tui_grid_pointer_captured(g)'if c else'g.pointerCaptured()'if java else'g.pointer_captured()'
    pointer=lambda act,extend=False:('tui_grid_pointer(g,'if c else'g.pointer(')+quote(act)+','+x+','+y+',w,h,'+boolean(extend)+')'
    clear='tui_grid_free(g);'if c else''
    for case in F['cases']:
        out.append('{'+create+'int w=64,h=10,ox=0,oy=0;'+event+'paint(g,w,h);')
        for step in case['steps']:
            if 'viewport'in step:out.append('w='+str(step['viewport'][0])+';h='+str(step['viewport'][1])+';')
            if 'key'in step:out.append('e='+('tui_grid_handle(g,'if c else'g.handle(')+quote(step['key'])+',h,"");')
            else:
                out.append('{'+('Point'if c else'var'if java else'auto')+' p=point(g,w,h,ox,oy,'+args_at(step['at'])+');')
                if step['action']=='down':out.append('ox='+x+';oy='+y+';')
                out.append('e='+pointer(step['action'],step.get('extend',False))+';}')
            out.append(check(('e.result==TUI_OK&&'if c else'')+equal('e.kind()'if java else'e.kind',step['event'])))
            for field,expr in [('row','tui_grid_row_id(g)'if c else'g.rowId()'if java else'g.row_id()'),('column','tui_grid_column_id(g)'if c else'g.columnId()'if java else'g.column_id()')]:
                if field in step:out.append(check(equal(expr,step[field])))
            if 'captured'in step:out.append(check(('!'if not step['captured']else'')+captured))
            if 'range'in step:
                if step['range'] is None:out.append(check('!tui_grid_selection(g)'if c else'g.selected==null'if java else'!g.selected'))
                else:out.append('range(g,'+','.join(quote(v)for v in step['range'])+');')
            if 'width'in step:out.append('width_is(g,'+quote(step['width'][0])+','+str(step['width'][1])+');')
            if 'order'in step:
                for i,id in enumerate(step['order']):out.append(check(equal('tui_grid_columns(g,NULL)['+str(i)+'].id'if c else'g.columns.get('+str(i)+').id'if java else'g.columns['+str(i)+'].id',id)))
            if 'caret'in step:
                a,b=step['caret'];out.append(check(('tui_text_anchor(tui_grid_edit_buffer(g))'if c else'g.edit.buffer.anchor'if java else'g.edit->buffer.anchor')+'=='+str(a)+'&&'+('tui_text_cursor(tui_grid_edit_buffer(g))'if c else'g.edit.buffer.cursor'if java else'g.edit->buffer.cursor')+'=='+str(b)))
            out.append('paint(g,w,h);')
        out.append(clear+'}')
    if c: virtual='int order[]={0,1,2,3};TuiGrid*g=model();assert(tui_grid_set_source(g,(TuiGridSource){order,4,source_row,source_index})==TUI_OK);'
    elif java:virtual='var src=new Source();var g=model(src);'
    else:virtual='auto src=std::make_shared<Source>();auto g=model(src);'
    swap='order[2]=3;order[3]=2;'if c else'Collections.swap(src.rows,2,3);'if java else'std::swap(src->rows[2],src->rows[3]);'
    pt='Point'if c else'var'if java else'auto'
    args1=args_at(['cell','r1','a']);args2=args_at(['cell','r3','b'])
    out.append('{'+virtual+'int w=64,h=10;paint(g,w,h);'+pt+' p=point(g,w,h,0,0,'+args1+');'+pointer('down')+';'+check(captured)+swap+'p=point(g,w,h,0,0,'+args2+');'+event+'e='+pointer('move')+';'+check(equal('e.kind()'if java else'e.kind','')+'&&!'+captured)+'paint(g,w,h);p=point(g,w,h,0,0,'+args1+');'+pointer('down')+';')
    light='canvas(g,w,h,"light","8",'+boolean(True)+','+boolean(False)+')'
    out.append(('tui_canvas_free('+light+');'if c else light+';')+check('!'+captured)+clear+'}')
    for theme in ['dark','light','blackwhite']:
        for colors in ['8','16','256','truecolor']:
            for ascii in [False,True]:
                out.append('{'+create+'int w=64,h=10;paint(g,w,h);'+pt+' p=point(g,w,h,0,0,'+args_at(['editor','r1','a',0])+');'+pointer('double')+';paint(g,w,h);')
                inc=lambda n:('p=new Point(p.x()+'+str(n)+',p.y());'if java else'p.x+='+str(n)+';')
                out.append(inc(1)+pointer('down')+';'+inc(2)+pointer('move')+';'+inc(-3))
                call='canvas(g,w,h,'+quote(theme)+','+quote(colors)+','+boolean(True)+','+boolean(ascii)+')'
                header='FRAME|'+theme+'|'+colors+'|'+str(int(ascii))+'|'
                if c:out.append('TuiCanvas*c='+call+';char*ansi=tui_canvas_ansi(c);assert(ansi);printf("'+header+'%d|%d\\n%s\\nEND\\n",p.x,p.y,ansi);tui_string_free(ansi);tui_canvas_free(c);')
                elif java:out.append('var c='+call+';System.out.print("'+header+'"+p.x()+"|"+p.y()+"\\n"+c.ansi()+"\\nEND\\n");')
                else:out.append('auto c='+call+';std::cout<<"'+header+'"<<p.x<<"|"<<p.y<<"\\n"<<c.ansi()<<"\\nEND\\n";')
                out.append(clear+'}')
    out.append('}}'if java else'return 0;}')
    return '\n'.join(out)

def validate(output):
    count=0
    for block in output.split('\nEND\n'):
        if not block.strip():continue
        header,frame=block.split('\n',1);kind,theme,colors,ascii,x,y=header.split('|');assert kind=='FRAME'
        x,y=int(x),int(y);cells=read_cells(frame)
        assert cells[x,y][0]=='한' and cells[x,y][2]==PALETTES[theme+'-'+colors]['selection']['background'],(header,cells[x,y])
        cursor=re.findall(r'\x1b\[(\d+);(\d+)H\x1b\[\?25h',frame)
        assert cursor and tuple(map(int,cursor[-1]))==(y+1,x+3),(header,cursor)
        count+=1
    assert count==24,count

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--language',choices=['c','cpp','java'],required=True)
    p.add_argument('--use-built',action='store_true',help='reuse artifacts built in the same checkout')
    args=p.parse_args()
    lang=args.language
    artifact=None
    if not args.use_built:
        from build_language import build
        artifact=build(lang)
    elif lang=='java':
        version=(ROOT/'VERSION').read_text().strip()
        artifact=ROOT/'.cache/packages/java'/f'tuivory-{version}.jar'
    with tempfile.TemporaryDirectory(prefix='tuivory-grid-pointer-')as directory:
        base=Path(directory)
        if lang=='java':
            shutil.copy2(artifact,base/'tuivory.jar');src=base/'GridPointerCases.java';src.write_text(source(lang))
            run(['javac','--release','17','-encoding','UTF-8','-Xlint:all','-Werror','-cp',base/'tuivory.jar',src],base)
            validate(subprocess.check_output(['java','-ea','-cp',str(base/'tuivory.jar')+os.pathsep+str(base),'GridPointerCases'],cwd=base,text=True))
        else:
            shutil.copytree(ROOT/lang/'include',base/'include');src=base/('pointer.c'if lang=='c'else'pointer.cpp');src.write_text(source(lang))
            flags=['cc'if lang=='c'else'c++','-std=c11'if lang=='c'else'-std=c++17','-Wall','-Wextra','-Werror','-I',base/'include',src]
            run(flags+([ROOT/'c/src/tuivory.c']if lang=='c'else[])+['-fsanitize=address,undefined','-o',base/'checked'],base)
            validate(subprocess.check_output([base/'checked'],cwd=base,text=True,env=dict(os.environ,ASAN_OPTIONS=os.environ.get('ASAN_OPTIONS','detect_leaks=0'))))
            if lang=='c':
                shutil.copy2(ROOT/'.cache/native/c/libtuivory.a',base/'libtuivory.a');flags+=[base/'libtuivory.a']
            run(flags+['-static','-o',base/'isolated'],base)
            validate(subprocess.check_output([base/'isolated'],cwd=base,text=True))
    print(lang+':7 shared grid pointer scenarios, stale/blur guards and 24 actual selected-grapheme frames passed')
if __name__=='__main__':main()
