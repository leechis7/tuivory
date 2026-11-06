#!/usr/bin/env python3
"""Verify surface style binding and actual ANSI buffers in isolated native/JAR apps."""
import argparse,json,os,shutil,tempfile,subprocess
from pathlib import Path
from check_languages import ROOT,quote,run
from check_language_feedback import statements
from build_language import build
from ansi_cells import read_cells
F=json.loads((ROOT/'design/surface-cases.json').read_text())
def color(s):return str((int(s[1:],16)|0x1000000)if s.startswith('#')else int(s))
def validate_output(output):
    palettes=json.loads((ROOT/'design/tokens/candidate.json').read_text())['palettes'];frames=output.split('FRAME|')[1:];assert len(frames)==48
    for frame in frames:
        heading,ansi=frame.split('\n',1);theme,colors,surface=heading.split('|');ansi=ansi.split('\nEND',1)[0];cells=read_cells(ansi);p=palettes[theme+'-'+colors];background=p[surface]['background']
        for y in range(1,7):
            for x in range(1,21):assert cells[x,y][2]==background,(heading,x,y,cells[x,y],background)
        assert cells[1,7][2]==p['selection']['background'],heading
        for n,role in enumerate(F['explicit_roles']):
            assert cells[11+n,7][1:3]==(p[role]['foreground'],p[role]['background']),(heading,role,cells[11+n,7])
        assert cells[21,1][2]==background,heading
        assert cells[1,8][1:3]==(p['body']['foreground'],p['body']['background']),heading
        assert cells[0,0][0]=='O',heading
        assert cells[1,2][4],heading

def source(lang):
    c=lang=='c';java=lang=='java'
    out=['import static io.tuivory.Tuivory.*;import java.util.*;public class SurfaceCases{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]args){']if java else['#include "tuivory.h"'if c else'#include "tuivory.hpp"','#include <assert.h>','#include <stdio.h>','#include <string.h>']
    if c:out.append('''static TuiResult inner_paint(void*context,const char*id,TuiCanvas*c,int focused){(void)context;(void)id;(void)focused;return tui_canvas_write(c,0,0,"OK","body",0,2);}
static TuiResult paint(void*context,TuiCanvas*c){(void)context;TuiBadge b={.label="Text"};TuiChip chip={.id="off",.label="Disabled",.state={.disabled=1}};TuiShortcut hint={"x","Help",0,0};TuiHelp*h=tui_help_new(&hint,1);assert(h);assert(tui_badge_draw(&b,c,(TuiRect){0,0,20,1})==TUI_OK);assert(tui_chip_draw(&chip,c,(TuiRect){0,1,20,1})==TUI_OK);assert(tui_help_draw(h,c,(TuiRect){0,2,20,1})==TUI_OK);tui_help_free(h);tui_canvas_panel(c,(TuiRect){0,3,20,3},"Panel",1,0);assert(tui_canvas_write(c,0,6,"Selection","selection",0,20)==TUI_OK);TuiLayoutItem item={.id="body"};TuiContainer*container=tui_container_new(&item,1,NULL);assert(container);assert(tui_container_draw(container,c,(TuiRect){20,0,2,2},inner_paint,NULL)==TUI_OK);tui_container_free(container);const char*explicit_roles[]={"field","selection","edited","header","editor","button","button.focus"};for(int n=0;n<7;n++)assert(tui_canvas_write(c,10+n,6,"X",explicit_roles[n],0,1)==TUI_OK);return TUI_OK;}
int main(void){''')
    elif not java:out.append('int main(){using namespace tuivory;')
    def check(e):out.append(('check('if java else'assert(')+e+');')
    for f in F['text']:
        if c:
            out.append('{TuiStyle s;assert(tui_text_on_surface('+','.join(quote(f[k])for k in ['theme','colors','role','surface'])+',0,&s)==TUI_OK);')
            check('s.foreground=='+color(f['foreground']));check('s.background=='+color(f['background']));check('!!s.dim=='+str(int(f.get('dim',False))));out.append('}')
        elif java:
            out.append('{var p=new Palette('+quote(f['theme'])+','+quote(f['colors'])+');var s=p.textOnSurface('+quote(f['role'])+','+quote(f['surface'])+');')
            check('s.foreground()=='+color(f['foreground']));check('s.background()=='+color(f['background']));check('s.dim()=='+str(f.get('dim',False)).lower());out.append('}')
        else:
            out.append('{Palette p('+quote(f['theme'])+','+quote(f['colors'])+');auto s=p.text_on_surface('+quote(f['role'])+','+quote(f['surface'])+');')
            check('s.foreground=='+color(f['foreground']));check('s.background=='+color(f['background']));check('s.dim=='+str(f.get('dim',False)).lower());out.append('}')
    for theme in ['dark','light','blackwhite']:
        for colors in ['8','16','256','truecolor']:
            for surface in F['surfaces']:
                if c:
                    out.append('{TuiCanvas*c=tui_canvas_new(26,10,'+quote(theme)+','+quote(colors)+');assert(c);assert(tui_canvas_write(c,0,0,"Outside","body",0,26)==TUI_OK);TuiSurface surface={'+quote(surface)+'};assert(tui_surface_draw(&surface,c,(TuiRect){1,1,24,8},paint,NULL)==TUI_OK);TuiStyle raw,bound;assert(tui_style('+quote(theme)+','+quote(colors)+',"body",0,&raw)==TUI_OK);assert(tui_canvas_write_style(c,1,8,"Raw",&raw,3)==TUI_OK);TuiState state={.selected=1};assert(tui_control_on_surface('+quote(theme)+','+quote(colors)+',state,'+quote(surface)+',0,&bound)==TUI_OK);assert(tui_style('+quote(theme)+','+quote(colors)+',"selection",0,&raw)==TUI_OK);assert(bound.foreground==raw.foreground&&bound.background==raw.background);state.disabled=1;assert(tui_control_on_surface('+quote(theme)+','+quote(colors)+',state,'+quote(surface)+',1,&bound)==TUI_OK&&bound.dim&&!bound.underline);char*ansi=tui_canvas_ansi(c);assert(ansi);printf("FRAME|'+theme+'|'+colors+'|'+surface+'\\n%s\\nEND\\n",ansi);tui_string_free(ansi);tui_canvas_free(c);}')
                elif java:
                    out.append('{var p=new Palette('+quote(theme)+','+quote(colors)+');var c=new Canvas(26,10,p);c.write(0,0,"Outside","body");new Surface('+quote(surface)+').draw(c,new Rect(1,1,24,8),child->{var b=new Badge();b.label="Text";b.draw(child,new Rect(0,0,20,1));var chip=new Chip("off","Disabled");chip.state.disabled=true;chip.draw(child,new Rect(0,1,20,1));new Help(List.of(new Shortcut("x","Help"))).draw(child,new Rect(0,2,20,1));child.panel(new Rect(0,3,20,3),"Panel",true,false);child.write(0,6,"Selection","selection");new Container(List.of(new LayoutItem("body"))).draw(child,new Rect(20,0,2,2),(id,inner,focused)->inner.write(0,0,"OK","body"));String[]explicitRoles={"field","selection","edited","header","editor","button","button.focus"};for(int n=0;n<7;n++)child.write(10+n,6,"X",explicitRoles[n]);child.writeStyle(0,7,"Raw",p.style("body"));});var state=new State();state.selected=true;check(p.controlOnSurface(state,'+quote(surface)+',false).equals(p.style("selection")));state.disabled=true;check(!p.controlOnSurface(state,'+quote(surface)+',true).underline());System.out.print("FRAME|'+theme+'|'+colors+'|'+surface+'\\n"+c.ansi()+"\\nEND\\n");}')
                else:
                    out.append('{Palette p('+quote(theme)+','+quote(colors)+');Canvas c(26,10,p);c.write(0,0,"Outside");Surface{'+quote(surface)+'}.draw(c,{1,1,24,8},[&](Canvas&child){Badge b;b.label="Text";b.draw(child,{0,0,20,1});Chip chip;chip.id="off";chip.label="Disabled";chip.state.disabled=true;chip.draw(child,{0,1,20,1});Help({{"x","Help"}}).draw(child,{0,2,20,1});child.panel({0,3,20,3},"Panel",true);child.write(0,6,"Selection","selection");LayoutItem item;item.id="body";Container({item}).draw(child,{20,0,2,2},[](const std::string&,Canvas&inner,bool){inner.write(0,0,"OK");});const char*explicit_roles[]={"field","selection","edited","header","editor","button","button.focus"};for(int n=0;n<7;n++)child.write(10+n,6,"X",explicit_roles[n]);child.write_style(0,7,"Raw",p.style("body"));});State state;state.selected=true;assert(p.control_on_surface(state,'+quote(surface)+').sgr()==p.style("selection").sgr());state.disabled=true;assert(!p.control_on_surface(state,'+quote(surface)+',true).underline);printf("FRAME|'+theme+'|'+colors+'|'+surface+'\\n%s\\nEND\\n",c.ansi().c_str());}')
    out.append('{TuiStyle s;assert(tui_text_on_surface("dark","8","disabled","surface",1,&s)==TUI_OK&&!s.underline);}'if c else'check(!new Palette().textOnSurface("disabled","surface",true).underline());'if java else'assert(!Palette().text_on_surface("disabled","surface",true).underline);')
    out.append('}}'if java else'return 0;}');return statements('\n'.join(out))

def main():
    p=argparse.ArgumentParser();p.add_argument('--language',choices=['c','cpp','java'],required=True);lang=p.parse_args().language;artifact=build(lang)
    with tempfile.TemporaryDirectory(prefix='tuivory-surfaces-')as directory:
        base=Path(directory)
        if lang=='java':
            shutil.copy2(artifact,base/'tuivory.jar');src=base/'SurfaceCases.java';src.write_text(source(lang));run(['javac','--release','17','-encoding','UTF-8','-Xlint:all','-Werror','-cp',base/'tuivory.jar',src],base);output=subprocess.check_output(['java','-cp',str(base/'tuivory.jar')+os.pathsep+str(base),'SurfaceCases'],cwd=base,text=True);validate_output(output)
        else:
            src=base/('surfaces.c'if lang=='c'else'surfaces.cpp');src.write_text(source(lang));shutil.copytree(ROOT/lang/'include',base/'include');flags=['cc'if lang=='c'else'c++','-std=c11'if lang=='c'else'-std=c++17','-Wall','-Wextra','-Werror','-I',base/'include',src]
            run(flags+([ROOT/'c/src/tuivory.c']if lang=='c'else[])+['-fsanitize=address,undefined','-o',base/'checked'],base);validate_output(subprocess.check_output([base/'checked'],cwd=base,text=True,env=dict(os.environ,ASAN_OPTIONS=os.environ.get('ASAN_OPTIONS','detect_leaks=0'))))
            if lang=='c':shutil.copy2(ROOT/'.cache/native/c/libtuivory.a',base/'libtuivory.a');flags+=[base/'libtuivory.a']
            run(flags+['-static','-o',base/'isolated'],base);validate_output(subprocess.check_output([base/'isolated'],cwd=base,text=True))
    print(lang+': known contrast/state fixtures and48 actual ANSI surface/control/nested/raw-background frames passed')
if __name__=='__main__':main()
