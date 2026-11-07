#!/usr/bin/env python3
"""Check independent wrapped dialogs, host requests and actual narrow ANSI output."""
import argparse,json,os,shutil,tempfile,subprocess
from pathlib import Path
from check_languages import ROOT,quote,run
from check_language_feedback import statements
from build_language import build
from ansi_cells import read_cells
F=json.loads((ROOT/'design/dialog-cases.json').read_text())
def validate_output(output):
    palettes=json.loads((ROOT/'design/tokens/candidate.json').read_text())['palettes'];count=0
    for block in output.split('\nEND\n'):
        if not block.strip():continue
        heading,ansi=block.split('\n',1);kind,theme,colors,glyph,x,y,width=heading.split('|');x,y,width=map(int,(x,y,width));ascii=glyph=='1';cells=read_cells(ansi);count+=1;p=palettes[theme+'-'+colors]
        assert 0<=x<x+width<=40 and 0<=y<12,heading
        for xx,yy,char in [(0,0,'╔'),(39,0,'╗'),(0,11,'╚'),(39,11,'╝')]:assert cells[xx,yy][0]==('+'if ascii else char),(heading,xx,yy,cells[xx,yy])
        line=''.join(cells[xx,y][0]for xx in range(40));assert 'Cancel'in line,(heading,line)
        for xx in range(x,x+width):
            cell=cells[xx,y]
            assert cell[2]==p['button.focus'if kind=='DIALOG'else'surface']['background'],(heading,xx,cell)
            assert cell[4]==(kind=='DISABLED'),(heading,xx,cell)
        assert '\x1b[?25h'not in ansi,heading
        if ascii:ansi.encode('ascii')
    assert count==48,count

def source(lang):
    c=lang=='c';java=lang=='java'
    out=['import static io.tuivory.Tuivory.*;import java.util.*;public class DialogCases{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]args){']if java else['#include "tuivory.h"'if c else'#include "tuivory.hpp"','#include <assert.h>','#include <stdio.h>','#include <string.h>','int main(void){'if c else'int main(){using namespace tuivory;']
    def check(e):out.append(('check('if java else'assert(')+e+');')
    def eq(e,v):check(e+'.equals('+quote(v)+')'if java else'!strcmp('+e+','+quote(v)+')'if c else e+'=='+quote(v))
    def create():
        if c:out.append('TuiDialogButton items[]={'+','.join('{'+quote(b['id'])+','+quote(b['label'])+',0}'for b in F['buttons'])+'};TuiDialog*d=tui_dialog_new("Confirm",'+quote(F['message'])+',items,3,"cancel");assert(d);')
        elif java:out.append('var items=List.of('+','.join('new DialogButton('+quote(b['id'])+','+quote(b['label'])+')'for b in F['buttons'])+');var d=new Dialog("Confirm",'+quote(F['message'])+',items,"cancel");')
        else:out.append('std::vector<DialogButton>items{'+','.join('{'+quote(b['id'])+','+quote(b['label'])+',false}'for b in F['buttons'])+'};Dialog d("Confirm",'+quote(F['message'])+',items,"cancel");')
    for f in F['layouts']:
        out.append('{');create()
        if c:out.append('TuiDialogLayout*l=NULL;assert(tui_dialog_layout(d,'+str(f['width'])+','+str(f['height'])+',&l)==TUI_OK);')
        elif java:out.append('var l=d.layout('+str(f['width'])+','+str(f['height'])+');')
        else:out.append('auto l=d.layout('+str(f['width'])+','+str(f['height'])+');')
        check(('tui_dialog_body_count(l)'if c else'l.body().size()'if java else'l.body.size()')+'=='+str(len(f['body'])))
        check(('tui_dialog_cell_count(l)'if c else'l.buttons().size()'if java else'l.buttons.size()')+'=='+str(len(f['buttons'])))
        for n,text in enumerate(f['body']):eq('tui_dialog_body_at(l,'+str(n)+')'if c else'l.body().get('+str(n)+')'if java else'l.body['+str(n)+']',text)
        for n,(id,x,y,w,h)in enumerate(f['buttons']):
            base='tui_dialog_cell_at(l,'+str(n)+')->'if c else'l.buttons().get('+str(n)+').'if java else'l.buttons['+str(n)+'].'
            eq(base+'id'+('()'if java else''),id)
            for k,v in [('x',x),('y',y),('width',w),('height',h)]:check(base+('rect().'+k+'()'if java else'rect.'+k)+'=='+str(v))
        check(('tui_dialog_hidden_buttons(l)'if c else'l.hiddenButtons()'if java else'l.hidden_buttons')+'=='+str(f['hidden']))
        check(('tui_dialog_body_truncated(l)'if c else'l.bodyTruncated()'if java else'l.body_truncated')+'=='+str(int(f['truncated'])if c else f['truncated']).lower())
        out.append('tui_dialog_layout_free(l);tui_dialog_free(d);}'if c else'}')
    for labels in (("확인", "다시 연결한 다음 계속", "설정 열기", "취소"),
                   ("OK", "Reconnect and continue", "Open settings", "Cancel")):
        for count in range(1, 5):
            entries = list(enumerate(labels[:count]))
            out.append("{")
            if c:
                entries_code = ",".join("{"+quote(str(i))+","+quote(label)+",0}" for i,label in entries)
                out.append("TuiDialogButton buttons[]={"+entries_code+"};TuiDialog *dialog=tui_dialog_new(\"Title\",\"\",buttons,"+str(count)+",\"0\");assert(dialog);")
            elif java:
                entries_code = ",".join("new DialogButton("+quote(str(i))+","+quote(label)+")" for i,label in entries)
                out.append("var dialog=new Dialog(\"Title\",\"\",List.of("+entries_code+"),\"0\");")
            else:
                entries_code = ",".join("{"+quote(str(i))+","+quote(label)+",false}" for i,label in entries)
                out.append("Dialog dialog(\"Title\",\"\",{"+entries_code+"},\"0\");")
            for width in (36,116):
                out.append("{")
                if c:
                    out.append(f"TuiDialogLayout *layout=NULL;assert(tui_dialog_layout(dialog,{width},12,&layout)==TUI_OK);assert(tui_dialog_cell_count(layout)=={count});")
                else:
                    out.append(("var" if java else "auto")+f" layout=dialog.layout({width},12);")
                    check(("layout.buttons().size()" if java else "layout.buttons.size()")+f"=={count}")
                out.append("int left=0,right=0,row=-1;")
                for i in range(count):
                    expr = (f"tui_dialog_cell_at(layout,{i})->rect" if c else
                            f"layout.buttons().get({i}).rect()" if java else f"layout.buttons[{i}].rect")
                    x,y,w = (f"box.{part}" + ("()" if java else "") for part in ("x","y","width"))
                    out.append("{"+("TuiRect" if c else "var" if java else "auto")+f" box={expr};")
                    out.append(f"if ({y}!=row){{")
                    check(f"row<0||left==({width}-(right-left))/2")
                    out.append(f"left={x};row={y};}}right={x}+{w};")
                    check(f"left>=0&&right<={width}")
                    out.append("}")
                check(f"left==({width}-(right-left))/2")
                if c:out.append("tui_dialog_layout_free(layout);")
                out.append("}")
            if c:out.append("tui_dialog_free(dialog);")
            out.append("}")
    out.append('{');create()
    if c:out.append('''assert(!strcmp(tui_dialog_focused(d),"cancel"));assert(!strcmp(tui_dialog_handle(d,"activate").id,"cancel"));assert(!strcmp(tui_dialog_handle(d,"cancel").kind,"cancel"));assert(!strcmp(tui_dialog_focused(d),"cancel"));items[2].disabled=1;assert(tui_dialog_set_buttons(d,items,3,NULL)==TUI_OK);assert(!strcmp(tui_dialog_focused(d),"retry"));assert(!*tui_dialog_handle(d,"cancel").kind);assert(!tui_dialog_focus(d,"cancel"));assert(!strcmp(tui_dialog_handle(d,"next").id,"details"));assert(!strcmp(tui_dialog_handle(d,"next").id,"retry"));TuiDialogButton invalid[]={{.id="same"},{.id="same"}};assert(tui_dialog_set_buttons(d,invalid,2,NULL)==TUI_INVALID);assert(tui_dialog_button_count(d)==3&&!strcmp(tui_dialog_focused(d),"retry"));const char*literal="한글\r\né [error]literal[/]";assert(tui_dialog_set_text(d,NULL,literal)==TUI_OK);assert(!strcmp(tui_dialog_message(d),literal));TuiDialogLayout*l=NULL;assert(tui_dialog_layout(d,40,12,&l)==TUI_OK);assert(tui_dialog_body_count(l)==2&&!strcmp(tui_dialog_body_at(l,1),"é [error]literal[/]"));tui_dialog_free(d);assert(!strcmp(tui_dialog_cell_at(l,0)->id,"retry"));tui_dialog_layout_free(l);}''')
    elif java:out.append('''check(d.focused().equals("cancel"));check(d.handle("activate").id().equals("cancel"));check(d.handle("cancel").kind().equals("cancel"));check(d.focused().equals("cancel"));d.setButtons(List.of(items.get(0),items.get(1),new DialogButton("cancel","Cancel",true)));check(d.focused().equals("retry"));check(d.handle("cancel").kind().isEmpty());check(!d.focus("cancel"));check(d.handle("next").id().equals("details"));check(d.handle("next").id().equals("retry"));boolean invalid=false;try{d.setButtons(List.of(new DialogButton("same"),new DialogButton("same")));}catch(IllegalArgumentException e){invalid=true;}check(invalid&&d.buttons().size()==3&&d.focused().equals("retry"));String literal="한글\r\né [error]literal[/]";d.setText(null,literal);check(d.message().equals(literal));var l=d.layout(40,12);check(l.body().size()==2&&l.body().get(1).equals("é [error]literal[/]"));}''')
    else:out.append('''assert(d.focused()=="cancel");assert(d.handle("activate").id=="cancel");assert(d.handle("cancel").kind=="cancel");assert(d.focused()=="cancel");items[2].disabled=true;d.set_buttons(items);assert(d.focused()=="retry");assert(d.handle("cancel").kind.empty());assert(!d.focus("cancel"));assert(d.handle("next").id=="details");assert(d.handle("next").id=="retry");bool invalid=false;try{d.set_buttons({{"same","",false},{"same","",false}});}catch(const std::invalid_argument&){invalid=true;}assert(invalid&&d.buttons().size()==3&&d.focused()=="retry");std::string literal="한글\r\né [error]literal[/]";d.set_text(std::nullopt,literal);assert(d.message()==literal);auto l=d.layout(40,12);assert(l.body.size()==2&&l.body[1]=="é [error]literal[/]");}''')
    if c:out.append('''{char title[]="Confirm",message[]="Confirm operation?",id[]="retry",label[]="Retry";TuiDialogButton button={id,label,0};TuiDialog*d=tui_dialog_new(title,message,&button,1,id);assert(d);title[0]=message[0]=id[0]=label[0]='X';assert(!strcmp(tui_dialog_title(d),"Confirm"));assert(!strcmp(tui_dialog_message(d),"Confirm operation?"));assert(!strcmp(tui_dialog_button_at(d,0)->id,"retry"));assert(!strcmp(tui_dialog_button_at(d,0)->label,"Retry"));TuiDialogLayout*l=NULL;assert(tui_dialog_layout(d,24,5,&l)==TUI_OK);tui_dialog_free(d);assert(!strcmp(tui_dialog_body_at(l,0),"Confirm operation?"));assert(!strcmp(tui_dialog_cell_at(l,0)->id,"retry"));tui_dialog_layout_free(l);}''')
    if c:out.append('''{const char*themes[]={"dark","light","blackwhite"},*profiles[]={"8","16","256","truecolor"};for(int t=0;t<3;t++)for(int p=0;p<4;p++)for(int ascii=0;ascii<2;ascii++){TuiDialogButton items[]={{"retry","Retry connection",0},{"settings","Open settings",0},{"cancel","Cancel",0}};TuiDialog*d=tui_dialog_new("Confirm","Confirm operation?",items,3,"cancel");assert(d);TuiCanvas*c=tui_canvas_new(40,12,themes[t],profiles[p]);assert(c);assert(!*tui_dialog_click(d,0,0).kind);TuiDialogLayout*l=NULL;assert(tui_dialog_draw(d,c,(TuiRect){0,0,40,12},1,ascii,&l)==TUI_OK);TuiRect cancel={0};for(size_t n=0;n<tui_dialog_cell_count(l);n++){const TuiDialogButtonCell*b=tui_dialog_cell_at(l,n);if(!strcmp(b->id,"cancel"))cancel=b->rect;}cancel.x+=2;cancel.y+=2;assert(cancel.width&&cancel.x+cancel.width<=40);char*ansi=tui_canvas_ansi(c);assert(ansi);printf("DIALOG|%s|%s|%d|%d|%d|%d\\n%s\\nEND\\n",themes[t],profiles[p],ascii,cancel.x,cancel.y,cancel.width,ansi);tui_string_free(ansi);assert(!strcmp(tui_dialog_click(d,cancel.x,cancel.y).id,"cancel"));tui_dialog_layout_free(l);items[2].disabled=1;assert(tui_dialog_set_buttons(d,items,3,NULL)==TUI_OK);assert(!*tui_dialog_click(d,cancel.x,cancel.y).kind);assert(tui_dialog_draw(d,c,(TuiRect){0,0,40,12},1,ascii,NULL)==TUI_OK);assert(!*tui_dialog_click(d,cancel.x,cancel.y).kind);assert(!strcmp(tui_dialog_focused(d),"retry"));assert(!*tui_dialog_handle(d,"cancel").kind);ansi=tui_canvas_ansi(c);assert(ansi);printf("DISABLED|%s|%s|%d|%d|%d|%d\\n%s\\nEND\\n",themes[t],profiles[p],ascii,cancel.x,cancel.y,cancel.width,ansi);tui_string_free(ansi);for(int width=0;width<12;width++){TuiCanvas*tiny=tui_canvas_new(width,5,themes[t],profiles[p]);assert(tiny);assert(tui_dialog_draw(d,tiny,(TuiRect){0,0,width,5},1,ascii,NULL)==TUI_OK);tui_canvas_free(tiny);}tui_dialog_free(d);tui_canvas_free(c);}}''')
    elif java:out.append('''for(String theme:List.of("dark","light","blackwhite"))for(String colors:List.of("8","16","256","truecolor"))for(boolean ascii:List.of(false,true)){var items=List.of(new DialogButton("retry","Retry connection"),new DialogButton("settings","Open settings"),new DialogButton("cancel","Cancel"));var d=new Dialog("Confirm","Confirm operation?",items,"cancel");var c=new Canvas(40,12,new Palette(theme,colors));check(d.click(0,0).kind().isEmpty());var l=d.draw(c,new Rect(0,0,40,12),true,ascii);var cancel=l.buttons().stream().filter(b->b.id().equals("cancel")).findFirst().orElseThrow().rect();int x=cancel.x()+2,y=cancel.y()+2;check(x+cancel.width()<=40);System.out.print("DIALOG|"+theme+"|"+colors+"|"+(ascii?1:0)+"|"+x+"|"+y+"|"+cancel.width()+"\\n"+c.ansi()+"\\nEND\\n");check(d.click(x,y).id().equals("cancel"));d.setButtons(List.of(items.get(0),items.get(1),new DialogButton("cancel","Cancel",true)));check(d.click(x,y).kind().isEmpty());d.draw(c,new Rect(0,0,40,12),true,ascii);check(d.click(x,y).kind().isEmpty()&&d.focused().equals("retry")&&d.handle("cancel").kind().isEmpty());System.out.print("DISABLED|"+theme+"|"+colors+"|"+(ascii?1:0)+"|"+x+"|"+y+"|"+cancel.width()+"\\n"+c.ansi()+"\\nEND\\n");for(int width=0;width<12;width++)d.draw(new Canvas(width,5,c.palette),new Rect(0,0,width,5),true,ascii);}''')
    else:out.append('''for(const auto&theme:{"dark","light","blackwhite"})for(const auto&colors:{"8","16","256","truecolor"})for(bool ascii:{false,true}){std::vector<DialogButton>items{{"retry","Retry connection",false},{"settings","Open settings",false},{"cancel","Cancel",false}};Dialog d("Confirm","Confirm operation?",items,"cancel");Canvas c(40,12,Palette(theme,colors));assert(d.click(0,0).kind.empty());auto l=d.draw(c,{0,0,40,12},true,ascii);Rect cancel;for(const auto&b:l.buttons)if(b.id=="cancel")cancel=b.rect;cancel.x+=2;cancel.y+=2;assert(cancel.width&&cancel.x+cancel.width<=40);printf("DIALOG|%s|%s|%d|%d|%d|%d\\n%s\\nEND\\n",theme,colors,(int)ascii,cancel.x,cancel.y,cancel.width,c.ansi().c_str());assert(d.click(cancel.x,cancel.y).id=="cancel");items[2].disabled=true;d.set_buttons(items);assert(d.click(cancel.x,cancel.y).kind.empty());d.draw(c,{0,0,40,12},true,ascii);assert(d.click(cancel.x,cancel.y).kind.empty()&&d.focused()=="retry"&&d.handle("cancel").kind.empty());printf("DISABLED|%s|%s|%d|%d|%d|%d\\n%s\\nEND\\n",theme,colors,(int)ascii,cancel.x,cancel.y,cancel.width,c.ansi().c_str());for(int width=0;width<12;width++){Canvas tiny(width,5,c.palette);d.draw(tiny,{0,0,width,5},true,ascii);}}''')
    out.append('}}'if java else'return 0;}');code='\n'.join(out);code=code.replace(chr(34)+'한글'+chr(13)+chr(10)+'é [error]literal[/]'+chr(34),quote('한글'+chr(13)+chr(10)+'é [error]literal[/]'));return statements(code)

def main():
    p=argparse.ArgumentParser();p.add_argument('--language',choices=['c','cpp','java'],required=True);lang=p.parse_args().language;artifact=build(lang)
    with tempfile.TemporaryDirectory(prefix='tuivory-dialogs-')as directory:
        base=Path(directory)
        if lang=='java':
            shutil.copy2(artifact,base/'tuivory.jar');src=base/'DialogCases.java';src.write_text(source(lang));run(['javac','--release','17','-encoding','UTF-8','-Xlint:all','-Werror','-cp',base/'tuivory.jar',src],base);validate_output(subprocess.check_output(['java','-cp',str(base/'tuivory.jar')+os.pathsep+str(base),'DialogCases'],cwd=base,text=True))
        else:
            src=base/('dialogs.c'if lang=='c'else'dialogs.cpp');src.write_text(source(lang));shutil.copytree(ROOT/lang/'include',base/'include');flags=['cc'if lang=='c'else'c++','-std=c11'if lang=='c'else'-std=c++17','-Wall','-Wextra','-Werror','-I',base/'include',src]
            run(flags+([ROOT/'c/src/tuivory.c']if lang=='c'else[])+['-fsanitize=address,undefined','-o',base/'checked'],base);validate_output(subprocess.check_output([base/'checked'],cwd=base,text=True,env=dict(os.environ,ASAN_OPTIONS=os.environ.get('ASAN_OPTIONS','detect_leaks=0'))))
            if lang=='c':shutil.copy2(ROOT/'.cache/native/c/libtuivory.a',base/'libtuivory.a');flags+=[base/'libtuivory.a']
            run(flags+['-static','-o',base/'isolated'],base);validate_output(subprocess.check_output([base/'isolated'],cwd=base,text=True))
    print(lang+':wrapped default cancel, host requests, atomic updates/ownership and48actual narrow dialog frames passed')
if __name__=='__main__':main()
