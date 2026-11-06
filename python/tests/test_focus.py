import json,unittest
from pathlib import Path
import tuivory as ui
F=json.loads((Path(__file__).resolve().parents[2]/'design/interaction-cases.json').read_text())
def targets(items):return [ui.FocusTarget(i['id'],ui.ControlState(**i.get('state',{})),i.get('hidden',False))for i in items]
class Focus(unittest.TestCase):
 def test_shared(self):
  f=ui.Focus('root',targets(F['root']))
  for s in F['steps']:
   try:
    if s['op']=='move':f.move(s.get('backwards',False))
    elif s['op']=='focus':self.assertEqual(f.focus(s['id']),s['accepted'])
    elif s['op']=='open':f.open(s['id'],targets(s['targets']),s.get('initial',''),s.get('dismissible',False))
    elif s['op']=='close':f.close(s['id'])
    elif s['op']=='update':f.update(s['id'],targets(s['targets']))
    elif s['op']=='route':self.assertEqual(f.route(s['target']).blocked,s['blocked']);self.assertEqual(f.route(s['target']).scope_id,s['expect_scope'])
    elif s['op']=='request':self.assertEqual(f.request_close().id if f.request_close()else'',s['request'])
   except ValueError:self.assertTrue(s.get('error'),s)
   else:self.assertFalse(s.get('error'),s)
   self.assertEqual((f.scope_id,f.focused,f.depth),(s['expect_scope'],s['expect_focus'],s['expect_depth']))
 def test_depth_and_ownership(self):
  t=ui.FocusTarget('original');f=ui.Focus('root',[t]);t.state.disabled=True;self.assertEqual(f.focused,'original')
  for i in range(64):f.open(str(i),[],dismissible=False)
  with self.assertRaises(ValueError):f.open('overflow',[])
  self.assertEqual(f.depth,64);self.assertTrue(f.route('root').blocked);self.assertFalse(f.route().blocked)
  self.assertIsNone(f.request_close());f.close('63');self.assertEqual(f.depth,63)
