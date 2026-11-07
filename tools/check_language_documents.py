#!/usr/bin/env python3
"""Verify original document ranges, wrapped drawing, markup and real ANSI cursors."""
import argparse,json,os,re,shutil,subprocess,tempfile
from pathlib import Path
from check_languages import ROOT,quote,run
from check_language_feedback import statements
from build_language import build
from ansi_cells import read_cells
CASES=json.loads((ROOT/'design/document-cases.json').read_text())
def validate_output(output):
    frames=0
    for block in output.split('\nEND\n'):
        if not block.strip():continue
        heading,ansi=block.split('\n',1);parts=heading.split('|');frame=read_cells(ansi);frames+=1
        if parts[0]=='LAYOUT':
            f=next(f for f in CASES['layout']if f['name']==parts[1]);cursor=f.get('screen_cursor')
            if cursor:assert f'\x1b[{cursor[1]+1};{cursor[0]+1}H\x1b[?25h'in ansi,heading
            else:assert '\x1b[?25h'not in ansi,heading
        else:
            assert parts[0]=='PALETTE';theme,colors,disabled=parts[1:];p=json.loads((ROOT/'design/tokens/candidate.json').read_text())['palettes'][theme+'-'+colors]
            assert frame[0,0][2]==p['button.focus']['background'],heading
            assert frame[0,0][4]==(disabled=='1'),heading
            assert '\x1b[?25h'not in ansi,heading
    assert frames==len(CASES['layout'])+24,frames

def source(language):
    c=language=='c';java=language=='java'
    out=['import static io.tuivory.Tuivory.*;import java.util.*;public class DocumentCases{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]args){']if java else['#include "tuivory.h"'if c else'#include "tuivory.hpp"','#include <assert.h>','#include <stdio.h>','#include <stdlib.h>','#include <string.h>','int main(void){'if c else'int main(){using namespace tuivory;']
    for f in CASES['layout']:
        w,h=f['width'],f['height'];ro=str(f['read_only']).lower();wrap=str(f['wrap']).lower();ln=str(f['line_numbers']).lower();secret=str(f.get('secret',False)).lower();cursor=f['cursor'];sx=f.get('scroll_x',0);out.append('{')
        if c:
            out.append(f'TuiDocument*d=tui_document_new({quote(f["source"])},{int(f["read_only"])});assert(d);TuiText*t=tui_document_buffer(d);tui_text_options(t,(TuiState){{.read_only={int(f["read_only"])}}},{int(f.get("secret",False))},1);tui_text_select(t,{cursor},{cursor});assert(tui_document_configure(d,(TuiDocumentOptions){{{int(f["wrap"])},{int(f["line_numbers"])},{sx},0}})==TUI_OK);TuiCanvas*c=tui_canvas_new({w},{h},"dark","256");assert(c);assert(tui_document_draw(d,c,(TuiRect){{0,0,{w},{h}}},1,0)==TUI_OK);')
        elif java:out.append(f'var d=new TextDocument({quote(f["source"])},{ro});d.buffer.secret={secret};d.buffer.select({cursor},{cursor});d.wrap={wrap};d.lineNumbers={ln};d.scrollX={sx};var c=new Canvas({w},{h});d.draw(c,new Rect(0,0,{w},{h}));')
        else:out.append(f'TextDocument d({quote(f["source"])},{ro});d.buffer.secret={secret};d.buffer.select({cursor},{cursor});d.wrap={wrap};d.line_numbers={ln};d.scroll_x={sx};Canvas c({w},{h});d.draw(c,{{0,0,{w},{h}}});')
        for y,row in enumerate(f['rows']):
            if c:out.append(f'{{const char*raw={quote(row)};char*actual=tui_canvas_line(c,{y});assert(actual);size_t bytes=strlen(raw);int pad={w}-tui_cells(raw);char*expected=malloc(bytes+(size_t)pad+1);assert(expected);memcpy(expected,raw,bytes);memset(expected+bytes,32,(size_t)pad);expected[bytes+(size_t)pad]=0;assert(!strcmp(actual,expected));free(actual);free(expected);}}')
            elif java:out.append(f'check(c.lines().get({y}).equals({quote(row)}+" ".repeat({w}-cells({quote(row)}))));')
            else:out.append(f'assert(c.lines()[{y}]==std::string({quote(row)})+std::string({w}-cells({quote(row)}),32));')
        if c:out.append(f'char*ansi=tui_canvas_ansi(c);assert(ansi);printf("LAYOUT|{f["name"]}\\n%s\\nEND\\n",ansi);tui_string_free(ansi);TuiDocumentLayout*l=NULL;assert(tui_document_layout(d,{w},{h},&l)==TUI_OK);tui_document_free(d);assert(tui_document_line_count(l)>0);assert(tui_document_line_at(l,0)->prefix);tui_document_layout_free(l);tui_canvas_free(c);}}')
        elif java:out.append(f'System.out.print("LAYOUT|{f["name"]}\\n"+c.ansi()+"\\nEND\\n");}}')
        else:out.append(f'printf("LAYOUT|{f["name"]}\\n%s\\nEND\\n",c.ansi().c_str());}}')
    for f in CASES['markup']:
        if c:
            out.append('{char*source=NULL;TuiDocumentSpan*spans=NULL;size_t count=0;assert(tui_parse_markup('+quote(f['source'])+',&source,&spans,&count)==TUI_OK);assert(!strcmp(source,'+quote(f['plain'])+'));assert(count=='+str(len(f['spans']))+');')
            for i,s in enumerate(f['spans']):out.append(f'assert(spans[{i}].start=={s["start"]}&&spans[{i}].end=={s["end"]}&&!strcmp(spans[{i}].role,{quote(s["role"])}));')
            out.append('free(source);tui_document_spans_free(spans,count);}')
        elif java:
            out.append('{var parsed=parseMarkup('+quote(f['source'])+');check(parsed.source().equals('+quote(f['plain'])+'));check(parsed.spans().size()=='+str(len(f['spans']))+');')
            for i,s in enumerate(f['spans']):out.append(f'check(parsed.spans().get({i}).equals(new DocumentSpan({s["start"]},{s["end"]},{quote(s["role"])})));')
            out.append('}')
        else:
            out.append('{auto parsed=parse_markup('+quote(f['source'])+');assert(parsed.first=='+quote(f['plain'])+');assert(parsed.second.size()=='+str(len(f['spans']))+');')
            for i,s in enumerate(f['spans']):out.append(f'assert(parsed.second[{i}].start=={s["start"]}&&parsed.second[{i}].end=={s["end"]}&&parsed.second[{i}].role=={quote(s["role"])});')
            out.append('}')
    for bad in CASES['invalid_markup']:
        if c:out.append('{TuiDocument*d=tui_document_new("unchanged",0);assert(d);tui_text_select(tui_document_buffer(d),2,2);assert(tui_document_set_markup(d,'+quote(bad)+')==TUI_INVALID);assert(!strcmp(tui_text_value(tui_document_buffer(d)),"unchanged")&&tui_text_cursor(tui_document_buffer(d))==2);tui_document_free(d);}')
        elif java:out.append('{var d=TextDocument.editor("unchanged");d.buffer.select(2,2);boolean invalid=false;try{d.setMarkup('+quote(bad)+');}catch(IllegalArgumentException e){invalid=true;}check(invalid&&d.buffer.value().equals("unchanged")&&d.buffer.cursor==2);}')
        else:out.append('{auto d=TextDocument::editor("unchanged");d.buffer.select(2,2);bool invalid=false;try{d.set_markup('+quote(bad)+');}catch(const std::invalid_argument&){invalid=true;}assert(invalid&&d.buffer.value=="unchanged"&&d.buffer.cursor==2);}')
    if c:out.append('''{TuiDocument*d=tui_document_new("한é界",0);assert(d);TuiDocumentSpan span={3,6,"warning"};assert(tui_document_set_byte_syntax(d,&span,1)==TUI_OK);size_t bad[]={1,4,5,10};for(size_t i=0;i<4;i++){span.start=bad[i];assert(tui_document_set_byte_syntax(d,&span,1)==TUI_INVALID);}assert(tui_document_set_text(d,"abc")==TUI_OK);TuiDocumentSpan style={0,3,"info"};TuiDocumentRange match={1,3};assert(tui_document_set_syntax(d,&style,1)==TUI_OK);assert(tui_document_set_search_matches(d,&match,1)==TUI_OK);TuiText*t=tui_document_buffer(d);tui_text_select(t,0,2);TuiDocumentLayout*l=NULL;assert(tui_document_layout(d,8,2,&l)==TUI_OK);const TuiDocumentLine*r=tui_document_line_at(l,0);assert(!strcmp(r->glyphs[0].role,"selection")&&!strcmp(r->glyphs[1].role,"selection")&&!strcmp(r->glyphs[2].role,"edited"));tui_document_layout_free(l);tui_text_options(t,(TuiState){.disabled=1},0,1);assert(!*tui_document_click(d,0,0,8,2,0).kind);assert(!*tui_document_handle(d,"insert","Z").kind);tui_text_options(t,(TuiState){0},0,1);assert(!strcmp(tui_document_handle(d,"insert","X").kind,"change"));assert(tui_document_layout(d,8,2,&l)==TUI_OK);r=tui_document_line_at(l,0);for(size_t i=0;i<r->glyph_count;i++)assert(!strcmp(r->glyphs[i].role,"body"));tui_document_layout_free(l);tui_document_free(d);}''')
    elif java:out.append('''{var d=TextDocument.editor("한é界");d.setByteSyntax(List.of(new DocumentSpan(3,6,"warning")));check(d.syntax().equals(List.of(new DocumentSpan(1,2,"warning"))));for(int start:new int[]{1,4,5,10}){boolean bad=false;try{d.setByteSyntax(List.of(new DocumentSpan(start,6,"error")));}catch(IllegalArgumentException e){bad=true;}check(bad&&d.syntax().get(0).role().equals("warning"));}d.setText("abc");d.lineNumbers=false;var spans=new ArrayList<DocumentSpan>();spans.add(new DocumentSpan(0,3,"info"));d.setSyntax(spans);spans.clear();d.setSearchMatches(List.of(new DocumentRange(1,3)));d.buffer.select(0,2);var g=d.layout(8,2).get(0).glyphs();check(g.get(0).role().equals("selection")&&g.get(1).role().equals("selection")&&g.get(2).role().equals("edited"));d.buffer.state.disabled=true;check(d.click(0,0,8,2).kind().isEmpty()&&d.handle("insert","Z").kind().isEmpty());d.buffer.state.disabled=false;d.handle("insert","X");d.layout(8,2);check(d.syntax().isEmpty()&&d.searchMatches().isEmpty());}''')
    else:out.append('''{auto d=TextDocument::editor("한é界");d.set_byte_syntax({{3,6,"warning"}});assert(d.syntax()[0].start==1&&d.syntax()[0].end==2);for(std::size_t start:{1,4,5,10}){bool bad=false;try{d.set_byte_syntax({{start,6,"error"}});}catch(const std::invalid_argument&){bad=true;}assert(bad&&d.syntax()[0].role=="warning");}d.set_text("abc");d.line_numbers=false;std::vector<DocumentSpan>spans{{0,3,"info"}};d.set_syntax(spans);spans.clear();d.set_search_matches({{1,3}});d.buffer.select(0,2);auto g=d.layout(8,2)[0].glyphs;assert(g[0].role=="selection"&&g[1].role=="selection"&&g[2].role=="edited");d.buffer.state.disabled=true;assert(d.click(0,0,8,2).kind.empty()&&d.handle("insert","Z").kind.empty());d.buffer.state.disabled=false;d.handle("insert","X");d.layout(8,2);assert(d.syntax().empty()&&d.search_matches().empty());}''')
    if c:out.append('{TuiDocument*d=tui_document_new("safe",0);assert(d);TuiDocumentOptions options=tui_document_options(d);options.scroll_x=-1;assert(tui_document_configure(d,options)==TUI_INVALID);assert(tui_document_options(d).scroll_x==0);options.scroll_x=1000001;assert(tui_document_configure(d,options)==TUI_INVALID);TuiDocumentLayout*l=NULL;assert(tui_document_layout(d,-1,2,&l)==TUI_INVALID);assert(!l&&!strcmp(tui_text_value(tui_document_buffer(d)),"safe"));tui_document_free(d);}')
    elif java:out.append('{var d=TextDocument.editor("safe");for(int bad:new int[]{-1,1000001}){d.scrollX=bad;boolean rejected=false;try{d.layout(8,2);}catch(IllegalArgumentException e){rejected=true;}check(rejected&&d.buffer.value().equals("safe"));}d.scrollX=0;d.scrollY=1000000;d.handle("page_down");check(d.scrollY==1000000);}')
    else:out.append('{auto d=TextDocument::editor("safe");for(int bad:{-1,1000001}){d.scroll_x=bad;bool rejected=false;try{d.layout(8,2);}catch(const std::invalid_argument&){rejected=true;}assert(rejected&&d.buffer.value=="safe");}d.scroll_x=0;d.scroll_y=1000000;d.handle("page_down");assert(d.scroll_y==1000000);}')
    if c:out.append('{TuiDocument*d=tui_document_new("safe",0);assert(d);char*large=malloc(999998);assert(large);memset(large,97,999997);large[999997]=0;assert(tui_document_handle(d,"insert",large).result==TUI_INVALID);assert(!strcmp(tui_text_value(tui_document_buffer(d)),"safe")&&tui_text_cursor(tui_document_buffer(d))==4);assert(!*tui_document_handle(d,"undo","").kind);free(large);tui_document_free(d);}')
    elif java:out.append('{var d=TextDocument.editor("safe");boolean rejected=false;try{d.handle("insert","a".repeat(999997));}catch(IllegalArgumentException e){rejected=true;}check(rejected&&d.buffer.value().equals("safe")&&d.buffer.cursor==4&&d.handle("undo").kind().isEmpty());}')
    else:out.append('{auto d=TextDocument::editor("safe");bool rejected=false;try{d.handle("insert",std::string(999997,97));}catch(const std::invalid_argument&){rejected=true;}assert(rejected&&d.buffer.value=="safe"&&d.buffer.cursor==4&&d.handle("undo").kind.empty());}')
    if c:out.append('''{const char*themes[]={"dark","light","blackwhite"},*colors[]={"8","16","256","truecolor"};for(int t=0;t<3;t++)for(int p=0;p<4;p++)for(int disabled=0;disabled<2;disabled++){TuiDocument*d=tui_document_new("한글",1);assert(d);tui_text_options(tui_document_buffer(d),(TuiState){.read_only=1,.disabled=disabled},0,1);TuiCanvas*c=tui_canvas_new(10,3,themes[t],colors[p]);assert(c);assert(tui_canvas_surface(c,"button.focus")==TUI_OK);assert(tui_document_draw(d,c,(TuiRect){0,0,10,3},1,0)==TUI_OK);char*ansi=tui_canvas_ansi(c);assert(ansi);printf("PALETTE|%s|%s|%d\\n%s\\nEND\\n",themes[t],colors[p],disabled,ansi);tui_string_free(ansi);tui_canvas_free(c);tui_document_free(d);}}''')
    elif java:out.append('''for(String theme:List.of("dark","light","blackwhite"))for(String colors:List.of("8","16","256","truecolor"))for(boolean disabled:List.of(false,true)){var d=TextDocument.viewer("한글");d.buffer.state.disabled=disabled;var c=new Canvas(10,3,new Palette(theme,colors),"button.focus");d.draw(c,new Rect(0,0,10,3));System.out.print("PALETTE|"+theme+"|"+colors+"|"+(disabled?1:0)+"\\n"+c.ansi()+"\\nEND\\n");}''')
    else:out.append('''for(const auto&theme:{"dark","light","blackwhite"})for(const auto&colors:{"8","16","256","truecolor"})for(bool disabled:{false,true}){auto d=TextDocument::viewer("한글");d.buffer.state.disabled=disabled;Canvas c(10,3,Palette(theme,colors),"button.focus");d.draw(c,{0,0,10,3});printf("PALETTE|%s|%s|%d\\n%s\\nEND\\n",theme,colors,(int)disabled,c.ansi().c_str());}''')
    out.append('}}'if java else'return 0;}');return statements('\n'.join(out))

def main():
    p=argparse.ArgumentParser();p.add_argument('--language',choices=['c','cpp','java'],required=True);lang=p.parse_args().language;artifact=build(lang)
    with tempfile.TemporaryDirectory(prefix='tuivory-documents-')as directory:
        base=Path(directory)
        if lang=='java':
            shutil.copy2(artifact,base/'tuivory.jar');src=base/'DocumentCases.java';src.write_text(source(lang));run(['javac','--release','17','-encoding','UTF-8','-Xlint:all','-Werror','-cp',base/'tuivory.jar',src],base);validate_output(subprocess.check_output(['java','-cp',str(base/'tuivory.jar')+os.pathsep+str(base),'DocumentCases'],cwd=base,text=True))
        else:
            src=base/('documents.c'if lang=='c'else'documents.cpp');src.write_text(source(lang));shutil.copytree(ROOT/lang/'include',base/'include');flags=['cc'if lang=='c'else'c++','-std=c11'if lang=='c'else'-std=c++17','-Wall','-Wextra','-Werror','-I',base/'include',src]
            run(flags+([ROOT/'c/src/tuivory.c']if lang=='c'else[])+['-fsanitize=address,undefined','-o',base/'checked'],base);validate_output(subprocess.check_output([base/'checked'],cwd=base,text=True,env=dict(os.environ,ASAN_OPTIONS=os.environ.get('ASAN_OPTIONS','detect_leaks=0'))))
            if lang=='c':shutil.copy2(ROOT/'.cache/native/c/libtuivory.a',base/'libtuivory.a');flags+=[base/'libtuivory.a']
            run(flags+['-static','-o',base/'isolated'],base);validate_output(subprocess.check_output([base/'isolated'],cwd=base,text=True))
    print(lang+': shared document layouts/markup/byte offsets, cursor and24 palette frames passed')
if __name__=='__main__':main()
