import json
from pathlib import Path
import unittest
from tuivory import Text, Canvas, Rect, Form, Field
ROOT=Path(__file__).resolve().parents[2]
class TextCases(unittest.TestCase):
    def test_shared(self):
        for case in json.loads((ROOT/'design/controls-cases.json').read_text())['text']:
            with self.subTest(case=case['name']):
                t=Text(case['text'],read_only=case.get('read_only',False),secret=case.get('secret',False),multiline=not case.get('single_line',False))
                for op in case['ops']:
                    e=t.handle(op['action'],op.get('text',''))
                    self.assertEqual(e.kind,op['kind'])
                    self.assertEqual(e.text,op.get('event_text',''))
                self.assertEqual(t.value,case['expected']);self.assertEqual(t.cursor,case['cursor'])
    def test_literal_offsets(self):
        t=Text('a\r\n한e\u0301😀');t.select_bytes(3,9)
        self.assertEqual(t.selection_bytes(),(3,9));before=(t.value,t.anchor,t.cursor)
        with self.assertRaises(ValueError):t.replace_bytes(4,9,'bad')
        self.assertEqual((t.value,t.anchor,t.cursor),before)
        self.assertEqual(t.replace_bytes(3,9,'[red]\r\n').kind,'change');self.assertEqual(t.value,'a\r\n[red]\r\n😀')
        t.handle('undo');self.assertEqual(t.value,before[0])
    def test_draw_bounds_and_password(self):
        t=Text('한😀x',multiline=False);t.select(0,2)
        for width in range(1,9):
            c=Canvas(12,4);c.write(0,0,'OUTSIDE');t.draw(c,Rect(3,1,width,1));self.assertEqual(c.lines()[0].strip(),'OUTSIDE')
            if c.cursor:self.assertTrue(3<=c.cursor[0]<3+width)
        t.scroll_x=0;t.click(1,0,8,1);self.assertEqual(t.cursor,0)
        f=Form([Field('p',kind='password',value='秘密😀')]);self.assertEqual(f.fields[0].value,'***');self.assertNotIn('秘密',repr(f.inputs['p']))
        self.assertEqual(f.value('p'),'秘密😀')
    def test_selection_and_noop(self):
        t=Text('ab\r\n한x');t.handle('home');self.assertEqual(t.cursor,3);t.handle('select_right');self.assertEqual(t.handle('copy').text,'한')
        t.disabled=True;self.assertEqual(t.handle('insert','bad').kind,'');t.disabled=False;t.read_only=True
        self.assertEqual(t.handle('cut').kind,'');self.assertEqual(t.handle('copy').text,'한')
