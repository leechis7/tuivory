import json,unittest
from pathlib import Path
import tuivory as ui
F=json.loads((Path(__file__).resolve().parents[2]/'design/forms-cases.json').read_text())
class Forms(unittest.TestCase):
 def test_shared(self):
  for case in F['scenarios']:
   with self.subTest(case=case['name']):
    fields=[]
    for data in case['fields']:
     data=dict(data);data['state']=ui.ControlState(**data.get('state',{}));data['options']=[ui.FormOption(**o)for o in data.get('options',[])];fields.append(ui.Field(**data))
    form=ui.Form(fields)
    for step in case['steps']:
     if 'focus'in step:self.assertTrue(form.focus(step['focus']));continue
     if 'feedback'in step:form.set_feedback(step['feedback'],error=step['error']);continue
     if 'state'in step:form.set_state(step['state'],ui.ControlState(**step['value']));continue
     e=form.click_field(step['click'],step.get('option',''))if 'click'in step else form.handle(step['action'],step.get('text',''))
     self.assertEqual(e.kind,step['kind'],step);self.assertEqual(e.text,step.get('event_text',''))
     if 'missing'in step:self.assertEqual(e.data,step['missing'])
     if 'focused'in step:self.assertEqual(form.focused,step['focused'])
     for key,attr in [('choices','choice'),('pending','pending'),('open','open'),('checked','checked'),('display','value')]:
      for id,value in step.get(key,{}).items():self.assertEqual(getattr(next(f for f in form.fields if f.id==id),attr),value)
     for id,value in step.get('values',{}).items():self.assertEqual(form.value(id),value)
 def test_validation_and_rendering(self):
  for fields in [[ui.Field('a'),ui.Field('a')],[ui.Field('')],[ui.Field('a',kind='bad')],[ui.Field('a',kind='select',open=True)],[ui.Field('a',options=[ui.FormOption('a'),ui.FormOption('a')])],[ui.Field('a',options=[ui.FormOption('')])],[ui.Field('a',choice='missing')]]:
   with self.assertRaises(ValueError):ui.Form(fields)
  for theme in ['dark','light','blackwhite']:
   for colors in ['8','16','256','truecolor']:
    f=ui.Form([ui.Field('p',kind='password',label='Password',value='秘密😀'),ui.Field('off',kind='checkbox',state=ui.ControlState(disabled=True)),ui.Field('b',kind='button',label='Run')])
    for width in range(0,20):
     c=ui.Canvas(24,8,ui.Palette(theme,colors));f.draw(c,ui.Rect(2,1,width,6));self.assertNotIn('秘密',''.join(c.lines()));self.assertEqual(f.click_field('off').kind,'');self.assertFalse(f.fields[1].checked)
     if c.cursor:self.assertTrue(2<=c.cursor[0]<2+width)
  original=ui.Field('p',kind='password',value='secret');form=ui.Form([original]);self.assertEqual(original.value,'secret');self.assertEqual(form.fields[0].value,'******')

 def test_pointer_grapheme_and_outside(self):
  f=ui.Control(ui.Field('a',value='한'));c=ui.Canvas(10,6);f.draw(c,ui.Rect(1,1,8,4));self.assertEqual(f.click(-1,1,4).kind,'');self.assertEqual(f.click(8,1,4).kind,'');self.assertEqual(f.click(3,1,4).kind,'select');f.handle('insert','X');self.assertEqual(f.value('a'),'X한')
