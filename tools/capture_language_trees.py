#!/usr/bin/env python3
"""Capture actual independent-language ANSI buffers as localized SVG references."""
from pathlib import Path
import argparse
import html
import os
import platform
import re
import subprocess
import sys
import regex
import cairosvg
from wcwidth import wcswidth

ROOT=Path(__file__).resolve().parents[1]
ANSI=['#000000','#800000','#008000','#808000','#000080','#800080','#008080','#c0c0c0','#808080','#ff0000','#00ff00','#ffff00','#0000ff','#ff00ff','#00ffff','#ffffff']
def indexed(n):
    if n<16:return ANSI[n]
    if n<232:
        n-=16;v=[0,95,135,175,215,255];return '#%02x%02x%02x'%(v[n//36],v[n//6%6],v[n%6])
    n=8+10*(n-232);return '#%02x%02x%02x'%(n,n,n)

def svg(data):
    rows=[[(' ',('#c0c0c0','#000000',False,False,False))for _ in range(72)]for _ in range(18)]
    cursor_visible=False
    x=y=pos=0;style=('#c0c0c0','#000000',False,False,False)
    while pos<len(data):
        if data.startswith('\x1b[',pos):
            match=re.match(r'\x1b\[([0-?]*)([ -/]*)([@-~])',data[pos:]);assert match
            params,_,command=match.groups();pos+=match.end()
            if params=='?25':cursor_visible=command=='h';continue
            if params.startswith('?'):continue
            args=[int(v or '0')for v in params.split(';')]
            if command=='H':y=(args[0]or 1)-1;x=(args[1]or 1)-1 if len(args)>1 else 0
            elif command=='m':
                fg,bg,bold,dim,underline=style;i=0
                while i<len(args):
                    c=args[i]
                    if c==0:fg,bg,bold,dim,underline='#c0c0c0','#000000',False,False,False
                    elif c==1:bold=True
                    elif c==2:dim=True
                    elif c==4:underline=True
                    elif 30<=c<=37:fg=ANSI[c-30]
                    elif 40<=c<=47:bg=ANSI[c-40]
                    elif 90<=c<=97:fg=ANSI[c-90+8]
                    elif 100<=c<=107:bg=ANSI[c-100+8]
                    elif c in (38,48):
                        if args[i+1]==5:color=indexed(args[i+2]);i+=2
                        else:assert args[i+1]==2;color='#%02x%02x%02x'%tuple(args[i+2:i+5]);i+=4
                        if c==38:fg=color
                        else:bg=color
                    i+=1
                style=fg,bg,bold,dim,underline
            continue
        end=data.find('\x1b',pos);end=len(data)if end<0 else end
        for g in regex.findall(r'\X',data[pos:end]):
            n=max(0,wcswidth(g))
            if n and 0<=y<18 and 0<=x and x+n<=72:
                rows[y][x]=(g,style)
                for cx in range(x+1,x+n):rows[y][cx]=('',style)
            x+=n
        pos=end
    cursor_x,cursor_y=x,y
    out=['<svg xmlns="http://www.w3.org/2000/svg" width="576" height="324" viewBox="0 0 576 324">','<style>text{font-family:D2Coding,monospace;font-size:16px;white-space:pre}</style>']
    for y,row in enumerate(rows):
        for x,(g,(fg,bg,bold,dim,underline))in enumerate(row):
            out.append(f'<rect x="{x*8}" y="{y*18}" width="8" height="18" fill="{bg}"/>')
    for y,row in enumerate(rows):
        for x,(g,(fg,bg,bold,dim,underline))in enumerate(row):
            if g and g!=' ':out.append(f'<text x="{x*8}" y="{y*18+14}" fill="{fg}" font-weight="{"bold"if bold else"normal"}" opacity="{0.6 if dim else 1}" text-decoration="{"underline"if underline else"none"}">{html.escape(g)}</text>')
    if cursor_visible and 0<=cursor_x<72 and 0<=cursor_y<18:out.append(f'<rect x="{cursor_x*8}" y="{cursor_y*18}" width="8" height="18" fill="none" stroke="#00a0ff"/>')
    out.append('</svg>');return '\n'.join(out)+'\n'

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--python',default=sys.executable);p.add_argument('--demo',choices=['tree','workspace','text','form','list','picker','menu','context-menu','feedback','layout','container','surface','shadow','dialog'],default='tree');args=p.parse_args()
    arch={'aarch64':'arm64','x86_64':'x86_64'}[platform.machine()]
    cmds={'python':[args.python,'-m','tuivory'],'javascript':['node','javascript/examples/catalog.mjs'],'c':[f'bin/c/tuivory-linux-{arch}'],'cpp':[f'bin/cpp/tuivory-linux-{arch}'],'java':['java','-jar',f'.cache/packages/java/tuivory-{(ROOT/"VERSION").read_text().strip()}.jar']}
    for language,cmd in cmds.items():
        for lang in ['ko','en']:
            env=dict(os.environ)
            if language=='python':env['PYTHONPATH']=str(ROOT/'python/src')
            output=subprocess.check_output([*cmd,'--demo',args.demo,'--lang',lang,'--theme','dark','--colors','truecolor','--snapshot-ansi'],cwd=ROOT,env=env,text=True)
            assert '\x1b['in output,(language,output[:200])
            literal=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', output)
            assert (('다시 연결'if lang=='ko'else'Reconnect')if args.demo=='dialog'else('문맥 메뉴'if lang=='ko'else'Context menu')if args.demo=='shadow'else('바탕 위 문구'if lang=='ko'else'Body on surface')if args.demo=='surface'else('탐색'if lang=='ko'else'Navigator')if args.demo=='container'else('배지'if lang=='ko'else'Badges')if args.demo=='layout'else('알림'if lang=='ko'else'Notices')if args.demo=='feedback'else(('문맥 메뉴'if lang=='ko'else'Context menu')if args.demo=='context-menu'else('새 문서'if lang=='ko'else'New document'))if args.demo in ('menu','context-menu')else('지원 언어'if lang=='ko'else'Languages')if args.demo in ('list','picker')else('이름'if lang=='ko'else'Name')if args.demo=='form'else('한글'if lang=='ko'else'Unicode')if args.demo=='text'else('작업 공간'if lang=='ko'else'Workspace'))in literal
            if lang=='en':assert '작업 공간'not in literal
            path=ROOT/'docs/images'/f'language-{language}-{args.demo}{"-en"if lang=="en"else""}.png'
            intermediate=ROOT/'.cache/validation/languages/snapshots'/path.with_suffix('.svg').name;intermediate.parent.mkdir(parents=True,exist_ok=True);intermediate.write_text(svg(output))
            cairosvg.svg2png(url=str(intermediate),write_to=str(path));print(path.relative_to(ROOT))

if __name__=='__main__':main()
