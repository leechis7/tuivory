#!/usr/bin/env python3
"""Verify independent SQL classification, source-tagged bindings and actual syntax cells."""
import argparse,json,os,shutil,subprocess,tempfile
from pathlib import Path
from check_languages import ROOT,run
from check_language_feedback import statements
from build_language import build
from ansi_cells import read_cells
CASES=sum([json.loads((ROOT/'design'/name).read_text())['cases']for name in ['syntax-cases.json','syntax-extra-cases.json']],[])
KINDS=['keyword','function','type','string','number','comment','parameter']
DOC="SELECT COUNT(1), CAST(:p AS VARCHAR2), 'x' -- c"
def q(text,java=False):
 if java:return json.dumps(text,ensure_ascii=True).replace('\\u001c','\\034').replace('\\u0085','\\205')
 out='"'
 for b in text.encode():
  out+=('\\"'if b==34 else'\\\\'if b==92 else chr(b)if 32<=b<127 else'\\%03o'%b)
 return out+'"'
def validate_output(output):
 styles={};docs=[];count=0
 palettes=json.loads((ROOT/'design/tokens/candidate.json').read_text())['palettes']
 for block in output.split('\nEND\n'):
  if not block.strip():continue
  heading,ansi=block.split('\n',1);parts=heading.split('|');cells=read_cells(ansi,include_italic=True);count+=1
  if parts[0]=='STYLE':
   _,theme,colors,surface=parts;p=palettes[theme+'-'+colors]
   styles[theme,colors,surface]=[cells[x,0][1:]for x in range(7)]
   for x,kind in enumerate(KINDS):
    cell=cells[x,0];assert cell[0]=='X'and cell[2]==p[surface]['background']and not cell[4],(heading,kind,cell)
    if theme=='dark'and colors=='8':
     assert cell[3]==(kind in ['keyword','number'])and cell[5]==(kind in ['keyword','type','parameter'])and cell[6]==(kind in ['string','comment']),(heading,kind,cell)
     assert int(cell[1])<8,(heading,cell)
     if surface=='editor':assert cell[1]==('3'if kind in ['keyword','function','string','parameter']else'7'),(heading,kind,cell)
    if theme=='blackwhite':assert not cell[3]and cell[5]==(kind in ['keyword','parameter'])and cell[6]==(kind=='comment'),(heading,kind,cell)
   assert cells[0,1][6]and not cells[1,1][6]and cells[0,2][6]and not cells[1,2][6],(heading,'italic blit/reset')
   assert cells[8,2][4]and cells[8,2][6]and cells[9,2][4]and not cells[9,2][6],(heading,'Dim preserves italic')
  else:
   assert parts[0]=='DOCUMENT',heading;docs.append((parts,cells))
 for parts,cells in docs:
  _,theme,colors=parts;expected=styles[theme,colors,'editor']
  for kind,literal in [('keyword','SELECT'),('function','COUNT'),('type','VARCHAR2'),('parameter',':p'),('number','1'),('string',"'x'"),('comment','-- c')]:
   x=DOC.index(literal)+2;assert cells[x,0][1:]==expected[KINDS.index(kind)],(parts,kind,cells[x,0],expected[KINDS.index(kind)])
 assert count==36 and len(docs)==12,(count,len(docs))
def source(language):
 c=language=='c';java=language=='java';out=['import static io.tuivory.Tuivory.*;import java.util.*;public class SyntaxCases{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]args){']if java else['#include "tuivory.h"'if c else'#include "tuivory.hpp"','#include <assert.h>','#include <stdio.h>','#include <stdlib.h>','#include <string.h>']
 def quote(text):return q(text,java)
 if c:out.append('''typedef struct {int calls,fail;} Context;static TuiResult analyze(void*ctx,const char*text,const TuiSyntaxRequest*request,TuiSyntaxAnalysis**out){Context*c=ctx;c->calls++;if(c->fail)return TUI_INVALID;return tui_sql_analyze(text,request,out);}static TuiResult paint(void*ctx,TuiCanvas*c){(void)ctx;(void)c;return TUI_OK;}int main(void){''')
 elif not java:out.append('int main(){using namespace tuivory;')
 for f in CASES:
  out.append('{')
  if c:out.append('TuiSyntaxRequest request={'+quote(f['language'])+','+quote(f['dialect'])+'};TuiSyntaxAnalysis*a=NULL;assert(tui_sql_analyze('+quote(f['source'])+',&request,&a)==TUI_OK);assert(a&&a->count=='+str(len(f['tokens']))+');assert(tui_syntax_validate(a,'+quote(f['source'])+')==TUI_OK);assert(!strcmp(a->source,'+quote(f['source'])+'));')
  elif java:out.append('var a=new SQLAnalyzer().analyzeSyntax('+quote(f['source'])+',new SyntaxRequest('+quote(f['language'])+','+quote(f['dialect'])+'));a.validate('+quote(f['source'])+');check(a.tokens().size()=='+str(len(f['tokens']))+');')
  else:out.append('auto a=SQLAnalyzer{}.analyze_syntax('+quote(f['source'])+',{'+quote(f['language'])+','+quote(f['dialect'])+'});a.validate('+quote(f['source'])+');assert(a.tokens.size()=='+str(len(f['tokens']))+');')
  for i,t in enumerate(f['tokens']):
   if c:out.append(f'assert(a->tokens[{i}].start=={t["start"]}&&a->tokens[{i}].end=={t["end"]}&&!strcmp(a->tokens[{i}].role,{quote(t["role"])}));')
   elif java:out.append(f'check(a.tokens().get({i}).equals(new SyntaxToken({t["start"]},{t["end"]},{quote(t["role"])})));')
   else:out.append(f'assert(a.tokens[{i}].start=={t["start"]}&&a.tokens[{i}].end=={t["end"]}&&a.tokens[{i}].role=={quote(t["role"])});')
  out.append('tui_syntax_analysis_free(a);}'if c else'}')
 if c:out.append('{TuiDocument*d=tui_document_new("SELECT 1",0);assert(d);assert(tui_document_set_syntax_analyzer(d,tui_sql_analyzer,NULL,NULL)==TUI_OK);tui_document_free(d);}')
 if c:out.append('''{Context ctx={0};TuiDocument*d=tui_document_new("SELECT 1",0);assert(d);assert(tui_document_set_syntax_analyzer(d,analyze,&ctx,NULL)==TUI_OK&&ctx.calls==1);TuiCanvas*c=tui_canvas_new(40,4,"dark","8");assert(c);for(int i=0;i<3;i++)assert(tui_document_draw(d,c,(TuiRect){0,0,40,4},1,0)==TUI_OK);tui_document_handle(d,"scroll_down","");TuiDocumentLayout*l=NULL;assert(tui_document_layout(d,12,2,&l)==TUI_OK);tui_document_layout_free(l);assert(ctx.calls==1);assert(!strcmp(tui_document_handle(d,"insert"," ").kind,"change")&&ctx.calls==2);char*before=malloc(strlen(tui_text_value(tui_document_buffer(d)))+1);assert(before);strcpy(before,tui_text_value(tui_document_buffer(d)));size_t cursor=tui_text_cursor(tui_document_buffer(d));ctx.fail=1;tui_document_handle(d,"insert","X");assert(ctx.calls==3&&*tui_document_syntax_error(d));assert(tui_document_draw(d,c,(TuiRect){0,0,40,4},1,0)==TUI_OK&&ctx.calls==3);assert(!strcmp(tui_document_handle(d,"undo","").kind,"change")&&ctx.calls==4);assert(!strcmp(tui_text_value(tui_document_buffer(d)),before)&&tui_text_cursor(tui_document_buffer(d))==cursor);ctx.fail=0;assert(tui_document_set_syntax_analyzer(d,analyze,&ctx,NULL)==TUI_OK&&ctx.calls==5&&!*tui_document_syntax_error(d));tui_text_options(tui_document_buffer(d),(TuiState){0},1,1);assert(tui_document_draw(d,c,(TuiRect){0,0,40,4},1,0)==TUI_OK&&ctx.calls==5);assert(tui_document_set_syntax_analyzer(d,analyze,&ctx,NULL)==TUI_INVALID&&ctx.calls==5);tui_text_options(tui_document_buffer(d),(TuiState){0},0,1);assert(tui_document_draw(d,c,(TuiRect){0,0,40,4},1,0)==TUI_OK&&ctx.calls==6);assert(tui_document_set_syntax_analyzer(d,NULL,NULL,NULL)==TUI_OK);tui_document_handle(d,"insert","Z");assert(ctx.calls==6);free(before);tui_canvas_free(c);tui_document_free(d);}''')
 elif java:out.append('''{int[]calls={0};boolean[]fail={false};SyntaxAnalyzer analyzer=(text,request)->{calls[0]++;if(fail[0])throw new IllegalArgumentException("sample failure");return new SQLAnalyzer().analyzeSyntax(text,request);};var d=TextDocument.editor("SELECT 1");d.setSyntaxAnalyzer(analyzer);check(calls[0]==1);for(String theme:List.of("dark","light","blackwhite"))d.draw(new Canvas(40,4,new Palette(theme,"8")),new Rect(0,0,40,4));d.handle("scroll_down");d.layout(12,2);check(calls[0]==1);d.handle("insert"," ");d.layout(40,4);check(calls[0]==2);String before=d.buffer.value();int cursor=d.buffer.cursor;fail[0]=true;d.handle("insert","X");check(calls[0]==3&&d.syntax().isEmpty()&&d.syntaxError()!=null);d.layout(40,4);check(calls[0]==3);check(d.handle("undo").kind().equals("change")&&calls[0]==4&&d.buffer.value().equals(before)&&d.buffer.cursor==cursor);fail[0]=false;d.setSyntaxAnalyzer(analyzer);check(calls[0]==5&&d.syntaxError()==null);d.buffer.secret=true;d.layout(40,4);check(d.syntax().isEmpty());boolean denied=false;try{d.setSyntaxAnalyzer(analyzer);}catch(IllegalArgumentException e){denied=true;}check(denied&&calls[0]==5);d.buffer.secret=false;d.layout(40,4);check(calls[0]==6);d.setSyntaxAnalyzer(null);d.handle("insert","Z");check(calls[0]==6&&d.syntax().isEmpty());}''')
 else:out.append('''{int calls=0;bool fail=false;SyntaxAnalyzer analyzer=[&](const std::string&text,const SyntaxRequest&request){calls++;if(fail)throw std::invalid_argument("sample failure");return SQLAnalyzer{}.analyze_syntax(text,request);};auto d=TextDocument::editor("SELECT 1");d.set_syntax_analyzer(analyzer);assert(calls==1);for(const auto&theme:{"dark","light","blackwhite"}){Canvas c(40,4,Palette(theme,"8"));d.draw(c,{0,0,40,4});}d.handle("scroll_down");d.layout(12,2);assert(calls==1);d.handle("insert"," ");d.layout(40,4);assert(calls==2);auto before=d.buffer.value;auto cursor=d.buffer.cursor;fail=true;d.handle("insert","X");assert(calls==3&&d.syntax().empty()&&d.syntax_error());d.layout(40,4);assert(calls==3);assert(d.handle("undo").kind=="change"&&calls==4&&d.buffer.value==before&&d.buffer.cursor==cursor);fail=false;d.set_syntax_analyzer(analyzer);assert(calls==5&&!d.syntax_error());d.buffer.secret=true;d.layout(40,4);assert(d.syntax().empty());bool denied=false;try{d.set_syntax_analyzer(analyzer);}catch(const std::invalid_argument&){denied=true;}assert(denied&&calls==5);d.buffer.secret=false;d.layout(40,4);assert(calls==6);d.set_syntax_analyzer({});d.handle("insert","Z");assert(calls==6&&d.syntax().empty());}''')
 # Applying a valid codepoint boundary inside a grapheme must still fail atomically.
 source_text=quote('한é界')
 if c:out.append('{TuiDocument*d=tui_document_new('+source_text+',0);assert(d);TuiDocumentSpan old={0,3,"warning"};assert(tui_document_set_syntax(d,&old,1)==TUI_OK);TuiSyntaxRequest bad_request={"unknown",""};assert(tui_document_set_syntax_analyzer(d,tui_sql_analyzer,NULL,&bad_request)==TUI_INVALID);TuiDocumentLayout*prior=NULL;assert(tui_document_layout(d,40,4,&prior)==TUI_OK);assert(!strcmp(tui_document_line_at(prior,0)->glyphs[0].role,"warning"));tui_document_layout_free(prior);TuiSyntaxToken token={3,4,"keyword"};TuiSyntaxAnalysis analysis={'+source_text+',"custom","",&token,1};assert(tui_syntax_validate(&analysis,analysis.source)==TUI_OK);assert(tui_document_set_syntax_analysis(d,&analysis)==TUI_INVALID);TuiSyntaxAnalysis stale={"wrong","","",NULL,0};assert(tui_document_set_syntax_analysis(d,&stale)==TUI_INVALID);token=(TuiSyntaxToken){1,3,"keyword"};assert(tui_syntax_validate(&analysis,analysis.source)==TUI_INVALID);token=(TuiSyntaxToken){0,3,"identifier"};assert(tui_document_set_syntax_analysis(d,&analysis)==TUI_OK);TuiDocumentLayout*l=NULL;assert(tui_document_layout(d,40,4,&l)==TUI_OK);assert(!strcmp(tui_document_line_at(l,0)->glyphs[0].role,"body"));tui_document_layout_free(l);tui_document_free(d);}')
 elif java:out.append('{var d=TextDocument.editor('+source_text+');d.setSyntax(List.of(new DocumentSpan(0,3,"warning")));boolean failed_attach=false;try{d.setSyntaxAnalyzer(new SQLAnalyzer(),new SyntaxRequest("unknown",""));}catch(IllegalArgumentException e){failed_attach=true;}check(failed_attach&&d.syntax().get(0).role().equals("warning"));var analysis=new SyntaxAnalysis('+source_text+',"custom","",List.of(new SyntaxToken(3,4,"keyword")));analysis.validate(d.buffer.value());boolean invalid=false;try{d.setSyntaxAnalysis(analysis);}catch(IllegalArgumentException e){invalid=true;}check(invalid&&d.syntax().get(0).role().equals("warning"));invalid=false;try{d.setSyntaxAnalysis(new SyntaxAnalysis("wrong","","",List.of()));}catch(IllegalArgumentException e){invalid=true;}check(invalid&&d.syntax().get(0).role().equals("warning"));d.setSyntaxAnalysis(new SyntaxAnalysis(d.buffer.value(),"custom","",List.of(new SyntaxToken(0,3,"identifier"))));check(d.syntax().get(0).role().equals("body"));}')
 else:out.append('{auto d=TextDocument::editor('+source_text+');d.set_syntax({{0,3,"warning"}});bool failed_attach=false;try{d.set_syntax_analyzer(SQLAnalyzer{},{"unknown",""});}catch(const std::invalid_argument&){failed_attach=true;}assert(failed_attach&&d.syntax()[0].role=="warning");SyntaxAnalysis analysis{'+source_text+',"custom","",{{3,4,"keyword"}}};analysis.validate(d.buffer.value);bool invalid=false;try{d.set_syntax_analysis(analysis);}catch(const std::invalid_argument&){invalid=true;}assert(invalid&&d.syntax()[0].role=="warning");invalid=false;try{d.set_syntax_analysis({"wrong","","",{}});}catch(const std::invalid_argument&){invalid=true;}assert(invalid&&d.syntax()[0].role=="warning");d.set_syntax_analysis({d.buffer.value,"custom","",{{0,3,"identifier"}}});assert(d.syntax()[0].role=="body");}')
 for theme in ['dark','light','blackwhite']:
  for colors in ['8','16','256','truecolor']:
   for surface in ['editor','button.focus']:
    out.append('{')
    if c:
     out.append('TuiCanvas*c=tui_canvas_new(12,4,'+quote(theme)+','+quote(colors)+');assert(c);assert(tui_canvas_surface(c,'+quote(surface)+')==TUI_OK);TuiStyle s;')
     for x,kind in enumerate(KINDS):out.append('assert(tui_syntax_style('+quote(theme)+','+quote(colors)+','+quote('syntax.'+kind)+','+quote(surface)+',&s)==TUI_OK);assert(tui_canvas_write_style(c,'+str(x)+',0,"X",&s,1)==TUI_OK);')
     out.append('assert(tui_style('+quote(theme)+','+quote(colors)+','+quote(surface)+',0,&s)==TUI_OK);s.foreground=7;s.bold=s.dim=s.underline=0;s.italic=1;assert(tui_canvas_write_style(c,0,1,"I",&s,1)==TUI_OK);s.italic=0;assert(tui_canvas_write_style(c,1,1,"N",&s,1)==TUI_OK);assert(tui_canvas_blit(c,c,(TuiRect){0,1,2,1},0,2)==TUI_OK);s.italic=1;assert(tui_canvas_write_style(c,8,2,"I",&s,1)==TUI_OK);s.italic=0;assert(tui_canvas_write_style(c,9,2,"N",&s,1)==TUI_OK);TuiShadowOptions options={"dim",0,0};assert(tui_shadow_draw(&options,c,(TuiRect){7,0,5,3},paint,NULL,0,NULL)==TUI_OK);char*ansi=tui_canvas_ansi(c);assert(ansi);printf("STYLE|'+theme+'|'+colors+'|'+surface+'\\n%s\\nEND\\n",ansi);tui_string_free(ansi);tui_canvas_free(c);}')
    elif java:
     out.append('var p=new Palette('+quote(theme)+','+quote(colors)+');var c=new Canvas(12,4,p,'+quote(surface)+');')
     for x,kind in enumerate(KINDS):out.append('c.writeStyle('+str(x)+',0,"X",syntaxStyle(p,'+quote('syntax.'+kind)+','+quote(surface)+'),1);')
     out.append('int bg=p.style('+quote(surface)+').background();var italic=new Style(7,bg,false,false,false,true);var normal=new Style(7,bg,false,false,false);c.writeStyle(0,1,"I",italic,1);c.writeStyle(1,1,"N",normal,1);c.blit(c,new Rect(0,1,2,1),0,2);c.writeStyle(8,2,"I",italic,1);c.writeStyle(9,2,"N",normal,1);new Shadow(new ShadowOptions("dim")).draw(c,new Rect(7,0,5,3),child->{},false);System.out.print("STYLE|'+theme+'|'+colors+'|'+surface+'\\n"+c.ansi()+"\\nEND\\n");}')
    else:
     out.append('Palette p('+quote(theme)+','+quote(colors)+');Canvas c(12,4,p,'+quote(surface)+');')
     for x,kind in enumerate(KINDS):out.append('c.write_style('+str(x)+',0,"X",syntax_style(p,'+quote('syntax.'+kind)+','+quote(surface)+'),1);')
     out.append('Style italic{7,p.style('+quote(surface)+').background,false,false,false,true},normal=italic;normal.italic=false;c.write_style(0,1,"I",italic,1);c.write_style(1,1,"N",normal,1);c.blit(c,{0,1,2,1},0,2);c.write_style(8,2,"I",italic,1);c.write_style(9,2,"N",normal,1);Shadow(ShadowOptions{"dim"}).draw(c,{7,0,5,3},[](Canvas&){},false);printf("STYLE|'+theme+'|'+colors+'|'+surface+'\\n%s\\nEND\\n",c.ansi().c_str());}')
   if c:out.append('{TuiDocument*d=tui_document_new('+quote(DOC)+',0);assert(d);Context ctx={0};assert(tui_document_set_syntax_analyzer(d,analyze,&ctx,NULL)==TUI_OK);tui_text_select(tui_document_buffer(d),0,0);TuiCanvas*c=tui_canvas_new(72,4,'+quote(theme)+','+quote(colors)+');assert(c);assert(tui_document_draw(d,c,(TuiRect){0,0,72,4},1,0)==TUI_OK);char*ansi=tui_canvas_ansi(c);assert(ansi);printf("DOCUMENT|'+theme+'|'+colors+'\\n%s\\nEND\\n",ansi);tui_string_free(ansi);tui_canvas_free(c);tui_document_free(d);}')
   elif java:out.append('{var d=TextDocument.editor('+quote(DOC)+');d.setSyntaxAnalyzer(new SQLAnalyzer());d.buffer.select(0,0);var c=new Canvas(72,4,new Palette('+quote(theme)+','+quote(colors)+'));d.draw(c,new Rect(0,0,72,4));System.out.print("DOCUMENT|'+theme+'|'+colors+'\\n"+c.ansi()+"\\nEND\\n");}')
   else:out.append('{auto d=TextDocument::editor('+quote(DOC)+');d.set_syntax_analyzer(SQLAnalyzer{});d.buffer.select(0,0);Canvas c(72,4,Palette('+quote(theme)+','+quote(colors)+'));d.draw(c,{0,0,72,4});printf("DOCUMENT|'+theme+'|'+colors+'\\n%s\\nEND\\n",c.ansi().c_str());}')
 out.append('}}'if java else'return 0;}');return statements('\n'.join(out))
def main():
 p=argparse.ArgumentParser();p.add_argument('--language',choices=['c','cpp','java'],required=True);lang=p.parse_args().language;artifact=build(lang)
 with tempfile.TemporaryDirectory(prefix='tuivory-syntax-')as directory:
  base=Path(directory)
  if lang=='java':
   shutil.copy2(artifact,base/'tuivory.jar');src=base/'SyntaxCases.java';src.write_text(source(lang));run(['javac','--release','17','-encoding','UTF-8','-Xlint:all','-Werror','-cp',base/'tuivory.jar',src],base);validate_output(subprocess.check_output(['java','-cp',str(base/'tuivory.jar')+os.pathsep+str(base),'SyntaxCases'],cwd=base,text=True))
  else:
   src=base/('syntax.c'if lang=='c'else'syntax.cpp');src.write_text(source(lang));shutil.copytree(ROOT/lang/'include',base/'include');flags=['cc'if lang=='c'else'c++','-std=c11'if lang=='c'else'-std=c++17','-Wall','-Wextra','-Werror','-I',base/'include',src]
   run(flags+([ROOT/'c/src/tuivory.c']if lang=='c'else[])+['-fsanitize=address,undefined','-o',base/'checked'],base);validate_output(subprocess.check_output([base/'checked'],cwd=base,text=True,env=dict(os.environ,ASAN_OPTIONS=os.environ.get('ASAN_OPTIONS','detect_leaks=0'))))
   if lang=='c':shutil.copy2(ROOT/'.cache/native/c/libtuivory.a',base/'libtuivory.a');flags+=[base/'libtuivory.a']
   run(flags+['-static','-o',base/'isolated'],base);validate_output(subprocess.check_output([base/'isolated'],cwd=base,text=True))
 print(lang+':31 syntax fixtures, cached/atomic/secret bindings and36 actual attribute/background/copy/Dim frames passed')
if __name__=='__main__':main()
