import json,unittest
from pathlib import Path
from tuivory import *
CASES=json.loads((Path(__file__).resolve().parents[2]/'design/document-cases.json').read_text())
class Documents(unittest.TestCase):
 def test_shared_layout_and_real_cursor(self):
  for case in CASES['layout']:
   with self.subTest(case=case['name']):
    d=TextDocument(case['source'],read_only=case['read_only']);d.buffer.secret=case.get('secret',False);d.buffer.select(case['cursor'],case['cursor']);d.wrap=case['wrap'];d.line_numbers=case['line_numbers'];d.scroll_x=case.get('scroll_x',0)
    c=Canvas(case['width'],case['height']);d.draw(c,Rect(0,0,c.width,c.height));self.assertEqual(c.lines()[:len(case['rows'])],[row+' '*(case['width']-cells(row))for row in case['rows']]);self.assertEqual(c.cursor,tuple(case['screen_cursor'])if'screen_cursor'in case else None)
 def test_markup_and_offsets_atomic(self):
  for f in CASES['markup']:
   source,spans=parse_markup(f['source']);self.assertEqual(source,f['plain']);self.assertEqual([vars(s)for s in spans],f['spans'])
  d=TextDocument.editor('unchanged');d.buffer.select(2,2)
  for bad in CASES['invalid_markup']:
   with self.assertRaises(ValueError):d.set_markup(bad)
   self.assertEqual(d.buffer.value,'unchanged');self.assertEqual(d.buffer.cursor,2)
  f=CASES['byte_spans'];d.set_text(f['source']);d.set_byte_syntax([DocumentSpan(**f['valid'])]);self.assertEqual(vars(d.syntax[0]),f['expected'])
  for start in f['invalid_starts']:
   with self.assertRaises(ValueError):d.set_byte_syntax([DocumentSpan(start,6,'error')])
   self.assertEqual(vars(d.syntax[0]),f['expected'])
 def test_highlight_priority_stale_and_copy(self):
  d=TextDocument.editor('abc');d.line_numbers=False;d.buffer.select(0,0);source=[DocumentSpan(0,3,'info')];d.set_syntax(source);source.clear();d.set_search_matches([DocumentRange(1,3)]);d.buffer.select(0,2)
  self.assertEqual([g.role for g in d.layout(8,2)[0].glyphs if g.index<3],['selection','selection','edited'])
  d.buffer.disabled=True;self.assertTrue(all(g.role=='disabled'for g in d.layout(8,2)[0].glyphs));self.assertEqual(d.click(0,0,8,2).kind,'');self.assertEqual(d.handle('insert','Z').kind,'')
  d.buffer.disabled=False;d.handle('insert','X');d.layout(8,2);self.assertEqual(d.syntax,[]);self.assertEqual(d.search_matches,[])
  d.buffer.secret=True;self.assertNotIn('X',repr(d));self.assertEqual(d.handle('copy').kind,'')
 def test_viewer_surface_cursor_wrap_and_pointer(self):
  for theme in ['dark','light','blackwhite']:
   for colors in ['8','16','256','truecolor']:
    c=Canvas(10,3,Palette(theme,colors),'button.focus');d=TextDocument.viewer('한글');d.draw(c,Rect(0,0,10,3));self.assertEqual(c.data[0][0].style.background,c.palette.style('button.focus').background);self.assertIsNone(c.cursor)
  d=TextDocument.editor('한글abcd');d.line_numbers=False;d.wrap=True;d.buffer.select(0,0);d.layout(4,6);d.click(1,0,4,6);self.assertEqual(d.buffer.cursor,0);d.click(0,1,4,6);self.assertEqual(d.buffer.cursor,2);d.draw(c,Rect(0,0,4,3));self.assertEqual(c.cursor,(0,1))
  old=d.buffer.value
  with self.assertRaises(ValueError):d.set_text('\ud800')
  self.assertEqual(d.buffer.value,old)

 def test_invalid_scroll_and_bounds_preserve_source_and_canvas(self):
  d=TextDocument.editor('safe');c=Canvas(8,2);c.write(0,0,'before');before=c.lines()
  with self.assertRaises(ValueError):d.draw(c,Rect(-1,0,8,2))
  self.assertEqual(c.lines(),before)
  for value in [-1,1_000_001,float('nan'),True]:
   d.scroll_x=value
   with self.assertRaises(ValueError):d.layout(8,2)
   self.assertEqual(d.buffer.value,'safe')
  d.scroll_x=0;d.scroll_y=1_000_000;d.handle('page_down');self.assertEqual(d.scroll_y,1_000_000)

 def test_source_limit_rejects_edit_without_changing_history(self):
  d=TextDocument.editor('safe');d.buffer.select(4,4)
  with self.assertRaises(ValueError):d.handle('insert','a'*999_997)
  self.assertEqual(d.buffer.value,'safe');self.assertEqual(d.buffer.cursor,4);self.assertEqual(d.handle('undo').kind,'')
  d.handle('insert','\r\n\t');self.assertEqual(d.buffer.value,'safe\n ')
