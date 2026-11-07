"""Inspect source highlighting, caching and failure recovery in actual example PTYs."""
import fcntl,json,os,struct,termios,time
from pathlib import Path
from ansi_cells import complete_frame,read_cells
ROOT=Path(__file__).resolve().parents[1]
def check_syntax_example(language,lang,theme,colors,ascii,master,slave,process,captured,screen,drain):
 palette=json.loads((ROOT/'design/tokens/candidate.json').read_text())['palettes'][theme+'-'+colors]
 def visible():return '\n'.join(''.join(row)for row in screen.rows[:24])
 def wait(predicate,message):
  deadline=time.monotonic()+5
  while time.monotonic()<deadline:
   drain(.02)
   if predicate():return
   if process.poll()is not None:break
  raise AssertionError((language,lang,theme,colors,ascii,message,visible()))
 def text(value):wait(lambda:value.replace(' ','')in visible().replace(' ',''),value)
 def status(mode,count):text(('Syntax 'if lang=='en'else'구문 ')+mode+' | '+('Calls 'if lang=='en'else'분석 ')+str(count))
 def frame():
  wait(lambda:complete_frame(captured)is not None,'complete syntax frame')
  return read_cells(complete_frame(captured).decode(),include_italic=True)
 def trailer():
  start=captured.rfind(b'\x1b[?25l');value=bytes(captured[start:])
  return value.split(b'\x1b[19;1H\x1b[K> ')[0]if language=='java'else value
 def token(value):
  for y,row in enumerate(screen.rows[1:18],1):
   x=''.join(row).find(value)
   if x>=0:return x,y
  raise AssertionError((language,value,visible()))
 def send(command,raw):
  count=captured.count(b'\x1b[0m');os.write(master,(command+'\n').encode()if language=='java'else raw)
  wait(lambda:captured.count(b'\x1b[0m')>count,'response '+command);frame()
 def key(value):send(value,value.encode())
 def keyword(active=True,surface='editor',disabled=False):
  x,y=token('SELECT');cell=frame()[x,y];assert cell[2]==palette[surface]['background'],(language,'syntax token background',cell)
  assert cell[4]==disabled,(language,'syntax disabled Dim',cell)
  if disabled:return
  if not active:assert not cell[3]and not cell[5]and not cell[6],(language,'stale syntax attributes',cell)
  elif theme=='dark'and colors=='8':assert cell[1]=='3'and cell[3]and cell[5]and not cell[6],(language,'dark8 accent',cell)
  elif theme=='blackwhite':assert cell[5]and not cell[3],(language,'monochrome keyword',cell)
 status('on',1);cells=frame();assert cells[1,2][0]=='2',(language,'SQL must retain source line breaks')
 keyword()
 if colors in ('8','16'):
  limit=int(colors);assert all(not c[1].startswith('#')and not c[2].startswith('#')and int(c[1])<limit and int(c[2])<limit for c in cells.values()),(language,'profile requested extra colors')
 if theme=='dark'and colors=='8'or theme=='blackwhite':
  for needle in (["'","--"]if theme=="dark"else["--"]):
   x,y=token(needle);assert cells[x,y][6],(language,'missing syntax italic',needle,cells[x,y])
 for value in ['w','n','n','w']:key(value);status('on',1)
 key('a');status('off',1);keyword(False)
 key('a');status('on',2);keyword()
 key('f');status('error',3);keyword(False);x,y=token('SELECT');assert x==4,(language,'failure example must add one blank to exercise analysis',x)
 send('undo',b'\x1a');status('error',4);x,y=token('SELECT');assert x==3,(language,'analysis failure damaged undo',x)
 key('f');status('on',5);keyword()
 key('s');wait(lambda:frame()[token('SELECT')][2]==palette['edited']['background'],'search overrides syntax')
 key('s');keyword()
 key('x');wait(lambda:frame()[token('SELECT')][4],'disabled syntax text');assert b'\x1b[?25h'not in trailer(),(language,'disabled cursor leak')
 send('click 3 2',b'\x1b[<0;4;3M');send('insert Z',b'Z');assert 'Z'not in visible(),(language,'disabled source edit accepted');status('on',5)
 key('x');wait(lambda:not frame()[token('SELECT')][4],'enabled syntax text');keyword()
 key('v');wait(lambda:frame()[token('SELECT')][2]==palette['surface']['background'],'viewer actual surface');assert b'\x1b[?25h'not in trailer(),(language,'viewer cursor leak')
 key('v');keyword()
 if language!='java':
  fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',18,40,0,0));key('w')
  wait(lambda:screen.rows[0][39]==('+'if ascii else'╗'),'syntax 40-column resize');status('on',5);key('w');status('on',5)
 x,y=token('SELECT');wait(lambda:f'\x1b[{y+1};{x+1}H\x1b[?25h'.encode()in trailer(),'actual syntax editor cursor')
