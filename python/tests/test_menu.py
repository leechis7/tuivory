import json,unittest
from pathlib import Path
import tuivory as ui
F=json.loads((Path(__file__).resolve().parents[2]/'design/menu-cases.json').read_text())
class Menu(unittest.TestCase):
 def test_shared(self):
  for case in F['scenarios']:
   m=ui.Menu([ui.MenuItem(**i)for i in F['items']]);self.assertEqual(m.open(case['root'],case['caller']).kind,'open')
   for s in case['steps']:
    e=m.handle(s['action'],s.get('value',''),5);self.assertEqual((e.kind,e.id,e.return_id),(s['event'],s['id'],case['caller']))
    self.assertEqual(m.opened,not s.get('closed',False))
    if m.opened:self.assertEqual(m.focused,s.get('focus',''));self.assertEqual(m.path,s.get('path',[]))
 def test_atomic_updates_and_validation(self):
  items=[ui.MenuItem(**i)for i in F['items']];m=ui.Menu(items);m.open('file','origin');m.handle('next');m.handle('activate');m.handle('next');before=m.path
  with self.assertRaises(ValueError):m.set_items(items+[items[0]])
  self.assertEqual(m.path,before);m.set_items(items);self.assertEqual(m.focused,'deep');items[4].disabled=True;e=m.set_items(items);self.assertEqual((e.kind,e.return_id),('close','origin'));self.assertFalse(m.opened)
  bad=[[ui.MenuItem('@back')],[ui.MenuItem('a',parent='b'),ui.MenuItem('b',parent='a')],[ui.MenuItem('a',parent='missing')],[ui.MenuItem('a',mnemonic='f'),ui.MenuItem('b',mnemonic='F')],[ui.MenuItem('a',separator=True),ui.MenuItem('b',parent='a')]]
  for items in bad:
   with self.assertRaises(ValueError):ui.Menu(items)
 def test_spans_bar_geometry_and_scope(self):
  m=ui.Menu([ui.MenuItem(**i)for i in F['items']]);m.open('file','editor')
  for ascii in [False,True]:
   for width in range(0,90):
    for height in range(0,12):
     rows=m.layout(width,height,ascii);self.assertLessEqual(len(rows),height)
     for r in rows:
      self.assertLessEqual(ui.cells(r.text),width)
      for s in r.spans:self.assertLessEqual(s.start+s.width,width);self.assertLessEqual(ui.cells(s.text),s.width)
     for c in m.bar_layout(width).cells:self.assertLessEqual(c.start+c.width,width);self.assertLessEqual(ui.cells(c.text),c.width)
  for width in range(40):
   for height in range(20):
    v=ui.Rect(3,2,width,height);r=ui.menu_placement(ui.Rect(70,18,1,1),v,40,20);self.assertTrue(v.x<=r.x<=r.x+r.width<=v.x+v.width);self.assertTrue(v.y<=r.y<=r.y+r.height<=v.y+v.height)
  for theme in ['dark','light','blackwhite']:
   for colors in ['8','16','256','truecolor']:
    c=ui.Canvas(40,12,ui.Palette(theme,colors));m.draw(c,ui.Rect(1,1,38,10));self.assertIsNone(c.cursor);self.assertFalse(any(cell.style.underline for row in c.data for cell in row));self.assertEqual(m.click_id('off').kind,'')
  focus=ui.Focus('root',[ui.FocusTarget('editor')]);focus.open('popup',[ui.FocusTarget('menu')]);self.assertTrue(focus.route('root').blocked);m.open('file','editor');e=m.handle('activate');focus.close('popup');self.assertEqual(e.return_id,focus.focused)
 def test_popup_host_blocks_background_and_restores_cursor(self):
  from tuivory._menu_example import MenuDemo
  from tuivory.terminal import Terminal
  for theme in ['dark','light','blackwhite']:
   for colors in ['8','16','256','truecolor']:
    for ascii in [False,True]:
     h=MenuDemo(True,True);c=ui.Canvas(72,18,ui.Palette(theme,colors));h.draw(c,ui.Rect(1,1,70,15),ascii=ascii)
     self.assertIsNone(c.cursor);self.assertEqual(h.focus.depth,1)
     initial=h.editor.value;h.pointer(2,1,0);h.handle('insert',text='z');self.assertEqual(h.editor.value,initial)
     h.pointer(65,13,2);h.draw(c,ui.Rect(1,1,70,15),ascii=ascii);self.assertGreaterEqual(h.content.x,1);self.assertLessEqual(h.content.x+h.content.width,71)
     h.handle('cancel');self.assertEqual(h.focus.depth,0);self.assertEqual(h.focus.focused,'editor')
     h.handle('insert',text='z');self.assertNotEqual(h.editor.value,initial);h.draw(c,ui.Rect(1,1,70,15),ascii=ascii);self.assertIsNotNone(c.cursor)
  m=ui.Menu([ui.MenuItem('a',label='A')]);m.open('');c=ui.Canvas(12,8,ui.Palette())
  for w in range(12):
   for h in range(8):
    r=m.draw_popup(c,ui.Rect(0,0,w,h),'Popup',padding=99999)
    self.assertTrue(0<=r.width<=w and 0<=r.height<=h)
  row=ui.List([ui.Item("long","abcdefghijklmnop")]).layout(8,1)[0];self.assertEqual(ui.cells(row.text),8);self.assertTrue(row.text.endswith("~"))
  t=Terminal()
  for seq,key in [(b'\x1b[21~','f10'),(b'\x1b[21;2~','shift_f10')]:
   for split in range(1,len(seq)):
    t._buffer=seq[:split];self.assertIsNone(t._parse());t._buffer+=seq[split:];self.assertEqual(t._parse().key,key)
