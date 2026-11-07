#!/usr/bin/env python3
"""Verify independent popup geometry, final shadow buffers and host boundaries."""
import argparse,json,os,shutil,tempfile,subprocess
from pathlib import Path
from check_languages import ROOT,quote,run
from check_language_feedback import statements
from build_language import build
from ansi_cells import read_cells
GEOMETRY=json.loads((ROOT/'design/popup-shadow-cases.json').read_text())['cases']
RENDER=json.loads((ROOT/'design/popup-shadow-render-cases.json').read_text())['cases']
def color(s):return str((int(s[1:],16)|0x1000000)if s.startswith('#')else int(s))
def validate_output(output):
    tokens=json.loads((ROOT/'design/tokens/candidate.json').read_text())['palettes'];known=wide=0
    for block in output.split('\nEND\n'):
        if not block.strip():continue
        heading,ansi=block.split('\n',1);parts=heading.split('|');cells=read_cells(ansi)
        if parts[0]=='KNOWN':
            f=RENDER[int(parts[1])];ascii=parts[2]=='1';known+=1
            for x,y,symbol in [(11,1,'▄'),(3,7,'▀')]:
                cell=cells[x,y];assert cell[0]==('.'if ascii else symbol),(heading,x,y,cell)
                assert cell[1:]==(f['shade'],f['backdrop'],False,False,False),(heading,cell,f)
            assert cells[11,2][0]==('.'if ascii else' '),heading
            assert cells[11,2][2]==(f['backdrop']if ascii else f['shade']),heading
        else:
            assert parts[0]=='WIDE',heading
            _,theme,colors,mode,glyph=parts;ascii=glyph=='1';wide+=1;p=tokens[theme+'-'+colors];w,h=(10,7)if mode=='off'else(9,6)
            for x,y,symbol in [(3,2,'┌'),(3+w-1,2,'┐'),(3,2+h-1,'└'),(3+w-1,2+h-1,'┘')]:assert cells[x,y][0]==('+'if ascii else symbol),(heading,x,y,cells[x,y])
            assert '\x1b[?25h'not in ansi,(heading,'covered cursor visible')
            for y in range(12):
                for x in range(22):
                    if 3<=x<13 and 2<=y<9:continue
                    c=cells[x,y];assert c[1:]==(p['body']['foreground'],p['body']['background'],p['body']['fontWeight']=='bold',False,False),(heading,x,y,c,p['body'])
            if mode=='dim':assert cells[6,8][0]=='界'and cells[6,8][4],heading
    assert known==len(RENDER)*2 and wide==96,(known,wide)

def source(lang):
    c=lang=='c';java=lang=='java'
    out=['import static io.tuivory.Tuivory.*;import java.util.*;public class PopupCases{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]args){']if java else['#include "tuivory.h"'if c else'#include "tuivory.hpp"','#include <assert.h>','#include <stdio.h>','#include <string.h>']
    if c:out.append('''static TuiResult paint(void*context,TuiCanvas*c){int ascii=*(int*)context;tui_canvas_panel(c,tui_canvas_bounds(c),"Popup",0,ascii);return TUI_OK;}static TuiResult fail(void*context,TuiCanvas*c){(void)context;tui_canvas_fill(c,tui_canvas_bounds(c),"surface");return TUI_INVALID;}int main(void){''')
    elif not java:out.append('int main(){using namespace tuivory;')
    def check(e):out.append(('check('if java else'assert(')+e+');')
    def rect(values):return ('new Rect('if java else'(TuiRect){'if c else'Rect{')+','.join(map(str,values))+(')'if java else'}')
    for f in GEOMETRY:
        o=f['options'];args=','.join([rect(f['anchor']),rect(f['viewport']),str(f['width']),str(f['height'])]);opts=','.join([quote(o['mode']),str(o['offsetX']),str(o['offsetY'])])
        if c:out.append('{TuiShadowOptions o={'+opts+'};TuiPopupLayout l;assert(tui_popup_placement('+args+',&o,&l)==TUI_OK);')
        elif java:out.append('{var l=popupPlacement('+args+',new ShadowOptions('+opts+'));')
        else:out.append('{auto l=popup_placement('+args+',ShadowOptions{'+opts+'});')
        for key,values in f['expected'].items():
            for field,value in zip(['x','y','width','height'],values):check('l.'+key+('().'+field+'()'if java else'.'+field)+'=='+str(value))
        if c:out.append('TuiRect regions[2];assert(tui_popup_shadow_regions(l,regions)==TUI_OK);for(int n=0;n<2;n++){TuiRect r=regions[n];for(int y=r.y;y<r.y+r.height;y++)for(int x=r.x;x<r.x+r.width;x++)assert(!tui_popup_hit(&l,x,y));}')
        elif java:out.append('for(var r:l.shadowRegions())for(int y=r.y();y<r.y()+r.height();y++)for(int x=r.x();x<r.x()+r.width();x++)check(!l.hit(x,y));')
        else:out.append('for(auto r:l.shadow_regions())for(int y=r.y;y<r.y+r.height;y++)for(int x=r.x;x<r.x+r.width;x++)assert(!l.hit(x,y));')
        out.append('}')
    for n,f in enumerate(RENDER):
        if c:out.append('{for(int ascii=0;ascii<2;ascii++){TuiCanvas*c=tui_canvas_new(20,10,'+quote(f['theme'])+','+quote(f['colors'])+');assert(c);TuiStyle style={.foreground=1,.background='+color(f['backdrop'])+',.bold=1,.underline=1};for(int y=0;y<10;y++)assert(tui_canvas_write_style(c,0,y,"AAAAAAAAAAAAAAAAAAAA",&style,20)==TUI_OK);TuiShadowOptions o={.mode='+quote(f['mode'])+'};TuiPopupLayout l;assert(tui_shadow_draw(&o,c,(TuiRect){2,1,10,7},paint,&ascii,ascii,&l)==TUI_OK);assert(!tui_popup_hit(&l,11,2));char*ansi=tui_canvas_ansi(c);assert(ansi);printf("KNOWN|'+str(n)+'|%d\\n%s\\nEND\\n",ascii,ansi);tui_string_free(ansi);tui_canvas_free(c);}}')
        elif java:out.append('{for(boolean ascii:List.of(false,true)){var c=new Canvas(20,10,new Palette('+quote(f['theme'])+','+quote(f['colors'])+'));var style=new Style(1,'+color(f['backdrop'])+',true,false,true);for(int y=0;y<10;y++)c.writeStyle(0,y,"AAAAAAAAAAAAAAAAAAAA",style);var l=new Shadow(new ShadowOptions('+quote(f['mode'])+')).draw(c,new Rect(2,1,10,7),child->child.panel(new Rect(0,0,child.width,child.height),"Popup",false,ascii),ascii);check(!l.hit(11,2));System.out.print("KNOWN|'+str(n)+'|"+(ascii?1:0)+"\\n"+c.ansi()+"\\nEND\\n");}}')
        else:out.append('{for(bool ascii:{false,true}){Canvas c(20,10,Palette('+quote(f['theme'])+','+quote(f['colors'])+'));Style style{1,'+color(f['backdrop'])+',true,false,true};for(int y=0;y<10;y++)c.write_style(0,y,"AAAAAAAAAAAAAAAAAAAA",style);auto l=Shadow(ShadowOptions{'+quote(f['mode'])+'}).draw(c,{2,1,10,7},[&](Canvas&child){child.panel({0,0,child.width,child.height},"Popup",false,ascii);},ascii);assert(!l.hit(11,2));printf("KNOWN|'+str(n)+'|%d\\n%s\\nEND\\n",(int)ascii,c.ansi().c_str());}}')
    if c:out.append('''{const char*themes[]={"dark","light","blackwhite"},*profiles[]={"8","16","256","truecolor"},*modes[]={"off","auto","solid","dim"};for(int t=0;t<3;t++)for(int p=0;p<4;p++)for(int m=0;m<4;m++)for(int ascii=0;ascii<2;ascii++){TuiCanvas*c=tui_canvas_new(22,12,themes[t],profiles[p]);assert(c);TuiStyle style;assert(tui_style(themes[t],profiles[p],"body",0,&style)==TUI_OK);for(int y=0;y<12;y++)assert(tui_canvas_write_style(c,0,y,"界界界界界界界界界界界",&style,22)==TUI_OK);tui_canvas_cursor(c,6,8,2);TuiShadowOptions o={.mode=modes[m]};assert(tui_shadow_draw(&o,c,(TuiRect){3,2,10,7},paint,&ascii,ascii,NULL)==TUI_OK);char*ansi=tui_canvas_ansi(c);assert(ansi);printf("WIDE|%s|%s|%s|%d\\n%s\\nEND\\n",themes[t],profiles[p],modes[m],ascii,ansi);tui_string_free(ansi);tui_canvas_cursor(c,0,0,2);assert(tui_shadow_draw(&o,c,(TuiRect){3,2,10,7},paint,&ascii,ascii,NULL)==TUI_OK);char*before=tui_canvas_ansi(c);assert(before&&strstr(before,"\\033[1;1H\\033[?25h"));assert(tui_shadow_draw(&o,c,(TuiRect){3,2,10,7},fail,NULL,ascii,NULL)==TUI_INVALID);ansi=tui_canvas_ansi(c);assert(ansi&&!strcmp(ansi,before));tui_string_free(ansi);tui_string_free(before);tui_canvas_free(c);}}TuiShadowOptions bad={.mode="invalid"};TuiPopupLayout result;assert(tui_shadow_layout(&bad,(TuiRect){0},&result)==TUI_INVALID);''')
    elif java:out.append('''for(String theme:List.of("dark","light","blackwhite"))for(String colors:List.of("8","16","256","truecolor"))for(String mode:List.of("off","auto","solid","dim"))for(boolean ascii:List.of(false,true)){var c=new Canvas(22,12,new Palette(theme,colors));var style=c.palette.style("body");for(int y=0;y<12;y++)c.writeStyle(0,y,"界界界界界界界界界界界",style);c.setCursor(6,8,2);var shadow=new Shadow(new ShadowOptions(mode));java.util.function.Consumer<Canvas>paint=child->child.panel(new Rect(0,0,child.width,child.height),"Popup",false,ascii);shadow.draw(c,new Rect(3,2,10,7),paint,ascii);System.out.print("WIDE|"+theme+"|"+colors+"|"+mode+"|"+(ascii?1:0)+"\\n"+c.ansi()+"\\nEND\\n");c.setCursor(0,0,2);shadow.draw(c,new Rect(3,2,10,7),paint,ascii);check(c.cursorX==0&&c.cursorY==0);String before=c.ansi();boolean failed=false;try{shadow.draw(c,new Rect(3,2,10,7),child->{throw new IllegalArgumentException("host");},ascii);}catch(IllegalArgumentException e){failed=true;}check(failed&&c.ansi().equals(before));}''')
    else:out.append('''for(const auto&theme:{"dark","light","blackwhite"})for(const auto&colors:{"8","16","256","truecolor"})for(const auto&mode:{"off","auto","solid","dim"})for(bool ascii:{false,true}){Canvas c(22,12,Palette(theme,colors));auto style=c.palette.style("body");for(int y=0;y<12;y++)c.write_style(0,y,"界界界界界界界界界界界",style);c.set_cursor(6,8,2);Shadow shadow(ShadowOptions{mode});auto paint=[&](Canvas&child){child.panel({0,0,child.width,child.height},"Popup",false,ascii);};shadow.draw(c,{3,2,10,7},paint,ascii);printf("WIDE|%s|%s|%s|%d\\n%s\\nEND\\n",theme,colors,mode,(int)ascii,c.ansi().c_str());c.set_cursor(0,0,2);shadow.draw(c,{3,2,10,7},paint,ascii);assert(c.cursor&&c.cursor->first==0&&c.cursor->second==0);auto before=c.ansi();bool failed=false;try{shadow.draw(c,{3,2,10,7},[](Canvas&){throw std::invalid_argument("host");},ascii);}catch(const std::invalid_argument&){failed=true;}assert(failed&&c.ansi()==before);}''')
    out.append('}}'if java else'return 0;}');return statements('\n'.join(out))

def main():
    p=argparse.ArgumentParser();p.add_argument('--language',choices=['c','cpp','java'],required=True);lang=p.parse_args().language;artifact=build(lang)
    with tempfile.TemporaryDirectory(prefix='tuivory-popups-')as directory:
        base=Path(directory)
        if lang=='java':
            shutil.copy2(artifact,base/'tuivory.jar');src=base/'PopupCases.java';src.write_text(source(lang));run(['javac','--release','17','-encoding','UTF-8','-Xlint:all','-Werror','-cp',base/'tuivory.jar',src],base);validate_output(subprocess.check_output(['java','-cp',str(base/'tuivory.jar')+os.pathsep+str(base),'PopupCases'],cwd=base,text=True))
        else:
            src=base/('popups.c'if lang=='c'else'popups.cpp');src.write_text(source(lang));shutil.copytree(ROOT/lang/'include',base/'include');flags=['cc'if lang=='c'else'c++','-std=c11'if lang=='c'else'-std=c++17','-Wall','-Wextra','-Werror','-I',base/'include',src]
            run(flags+([ROOT/'c/src/tuivory.c']if lang=='c'else[])+['-fsanitize=address,undefined','-o',base/'checked'],base);validate_output(subprocess.check_output([base/'checked'],cwd=base,text=True,env=dict(os.environ,ASAN_OPTIONS=os.environ.get('ASAN_OPTIONS','detect_leaks=0'))))
            if lang=='c':shutil.copy2(ROOT/'.cache/native/c/libtuivory.a',base/'libtuivory.a');flags+=[base/'libtuivory.a']
            run(flags+['-static','-o',base/'isolated'],base);validate_output(subprocess.check_output([base/'isolated'],cwd=base,text=True))
    print(lang+':32shared geometries,20known shades and96actual wide/Dim/cursor shadow buffers passed')
if __name__=='__main__':main()
