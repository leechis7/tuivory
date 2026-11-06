import json,unittest
from pathlib import Path
import tuivory as ui
ROOT=Path(__file__).resolve().parents[2]
F=json.loads((ROOT/'design/collections-cases.json').read_text())
class Collections(unittest.TestCase):
 def test_casefold(self):
  data=json.loads((ROOT/'design/casefold.json').read_text())
  for key,value in data['mappings'].items():self.assertEqual(ui.fold(chr(int(key))),value)
  for c in F['fold']:self.assertEqual(ui.fold(c['text']),c['expected'])
 def test_shared(self):
  items=[ui.Item(**i)for i in F['items']];m=ui.List(items)
  for s in F['list']:
   e=m.set_query(s['query'])if 'query'in s else m.click_id(s['click'])if 'click'in s else m.handle(s['action'],s.get('height',3))
   self.assertEqual(e.kind,s['kind']);self.assertEqual(e.id,s.get('id',''));self.assertEqual(e.text,s.get('text',''))
   for key in ['focused','selected']:
    if key in s:self.assertEqual(getattr(m,key),s[key])
  p=ui.SearchPicker(items)
  for s in F['picker']:
   e=p.click_id(s['click'])if 'click'in s else p.handle(s['action'],s.get('text',''),4)
   self.assertEqual(e.kind,s['kind']);self.assertEqual(e.id,s.get('id',''));self.assertEqual(e.text,s.get('event_text',''))
   for key in ['open','value']:
    if key in s:self.assertEqual(getattr(p,key),s[key])
   if 'focused'in s:self.assertEqual(p.list.focused,s['focused'])
 def test_update_hits_and_cursor(self):
  items=[ui.Item(**i)for i in F['items']];m=ui.List(items);m.handle('select');m.set_query('GO')
  with self.assertRaises(ValueError):m.set_items([ui.Item('bad'),ui.Item('bad')])
  self.assertEqual(m.focused,'go');self.assertEqual(m.selected,'go');m.set_items([ui.Item('replacement','Next')]);self.assertEqual(m.selected,'');self.assertEqual(m.focused,'');m.set_query('');self.assertEqual(m.focused,'replacement')
  p=ui.SearchPicker(items);p.handle('open');p.handle('insert','한'*40)
  for theme in ['dark','light','blackwhite']:
   for colors in ['8','16','256','truecolor']:
    for width in range(0,20):
     c=ui.Canvas(24,8,ui.Palette(theme,colors));p.draw(c,ui.Rect(2,1,width,6));self.assertTrue(all(ui.cells(r.text)<=width for r in p.layout(width,6)))
     if c.cursor:self.assertTrue(2<=c.cursor[0]<2+width)
  m=ui.List(items);rows=m.layout(40,20);self.assertEqual(m.click(-1,1,20).kind,'');self.assertEqual(m.click(40,1,20).kind,'');at=next(i for i,r in enumerate(rows)if r.id=='x');self.assertEqual(m.click(2,at,20).kind,'');at=next(i for i,r in enumerate(rows)if r.id=='go'and r.role=='hint');self.assertEqual(m.click(2,at,20).id,'go')
