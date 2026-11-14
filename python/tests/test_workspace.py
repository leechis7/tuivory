import json
from pathlib import Path
import unittest
import tuivory as ui
ROOT=Path(__file__).resolve().parents[2]
class Workspace(unittest.TestCase):
    def test_common_workspace(self):
        f=json.loads((ROOT/'design/components-cases.json').read_text())
        for case in f['tabs']['layouts']:
            t=ui.Tabs([ui.Tab(**x)for x in f['tabs']['items']]);t.focused='c'
            views=t.layout(case['width']);self.assertEqual(t.first,case['first']);self.assertEqual([v.id for v in views],case['ids'])
            for v in views:self.assertLessEqual(v.start+v.width,case['width']);self.assertLessEqual(ui.cells(v.text),v.width)
        path=[('r','root'),('f','folder'),('c','현재.sql')]
        for case in f['paths']:
            layout=ui.path_runs(path,case['width']);self.assertEqual(layout.text,case['text'])
            for run in layout.runs:self.assertLessEqual(run.start+run.width,case['width'])
        items=[ui.StatusItem('help','F1 Help','hint',1),ui.StatusItem('err','Failure','error',100),ui.StatusItem('draft','Draft','edited',30)]
        for case in f['status']:
            layout=ui.status_line(items,case['width']);self.assertEqual((layout.text,layout.omitted),(case['text'],case['omitted']))
    def test_tab_close_and_disabled(self):
        t=ui.Tabs([ui.Tab('a','ax'),ui.Tab('d','Disabled',disabled=True),ui.Tab('b','Draft',closable=True)])
        first=t.layout(80)[0];self.assertEqual(t.click(first.start+ui.cells(first.text)-2,80).kind,'activate')
        disabled=t.layout(80)[1];self.assertEqual(t.click(disabled.start,80).kind,'')
        last=t.layout(80)[2];self.assertEqual(t.click(last.start+ui.cells(last.text)-2,80).kind,'close')
    def test_outline_keeps_close_hit_and_active_opening(self):
        t = ui.Tabs([ui.Tab('a', '조회', closable=True), ui.Tab('b', 'Draft', edited=True)])
        t.handle('next')
        active, candidate = t.layout(32)
        canvas = ui.Canvas(32, 3)
        t.draw(canvas, ui.Rect(0, 0, 32, 3))
        self.assertEqual(canvas.data[0][active.start].text, '┌')
        self.assertEqual(canvas.data[2][active.start + 1].text, ' ')
        self.assertEqual(canvas.data[2][candidate.start].text, '─')
        close = active.start + ui.cells(active.text) - 2
        self.assertEqual(canvas.data[1][close].text, 'x')
        self.assertEqual(t.click(close, 32).kind, 'close')

    def test_split(self):
        s=ui.Split(3,4,7)
        for total in range(30):
            l=s.layout(total);self.assertEqual(l.first+l.divider+l.second,total)
            if total<8:self.assertTrue(l.compact);self.assertEqual(l.first,0)
        self.assertTrue(s.resize(30,10));self.assertEqual(s.layout(30).first,10)
