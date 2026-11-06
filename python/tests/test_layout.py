import json
import unittest
from pathlib import Path
import tuivory as ui

F=json.loads((Path(__file__).resolve().parents[2]/'design/layout-cases.json').read_text())


class Layout(unittest.TestCase):
    def test_shared_spacing_stacks_and_bounds(self):
        for s in F['spacing']:
            t=ui.SpacingTokens.for_width(s['density'],s['columns'])
            self.assertEqual((t.gap,t.padding,t.control_gap),(s['gap'],s['padding'],s['control_gap']))
        items=[ui.StackItem(**i)for i in F['items']]
        for s in F['stacks']:
            result=ui.stack_layout([ui.StackItem(**i)for i in s.get('items',F['items'])],s['total'],s['gap'])
            self.assertEqual([[i.id,i.start,i.size]for i in result.slots],s['slots'])
            self.assertEqual(result.gap,s['actual_gap']);self.assertEqual(result.hidden,s['hidden'])
        for width in range(241):
            r=ui.stack_layout(items,width,2);end=0
            for slot in r.slots:
                self.assertTrue(end<=slot.start<=slot.start+slot.size<=width)
                if slot.size:end=slot.start+slot.size
            for vertical in [False,True]:
                parent=ui.Rect(2,3,width,20);result=ui.stack_rects(parent,items,ui.SpacingTokens(2,1,2),vertical=vertical)
                for item in result.rects:
                    r=item.rect;self.assertTrue(2<=r.x<=r.x+r.width<=2+width);self.assertTrue(3<=r.y<=r.y+r.height<=23)
        self.assertEqual(items[0].preferred,40)
        self.assertTrue(ui.drawer_layout(ui.Rect(0,0,30,10),24,40).overlay)
        self.assertFalse(ui.drawer_layout(ui.Rect(0,0,100,10),24,40).overlay)
        for bad in [[ui.StackItem('a'),ui.StackItem('a')],[ui.StackItem('a',0)],[ui.StackItem('a',1,weight=-1)]]:
            with self.assertRaises(ValueError):ui.stack_layout(bad,20,1)

    def test_badges_chips_help_and_requests(self):
        for s in F['badges']:
            b=ui.Badge(**{k:v for k,v in s.items()if k not in ('text','role','state')},state=ui.ControlState(**s.get('state',{})))
            self.assertEqual((b.line(40).text,b.line(40).role),(s['text'],s['role']))
        for s in F['chips']:
            c=ui.Chip(s['id'],s['label'],ui.ControlState(**s['state']),s['removable'])
            self.assertEqual(c.request_remove().kind,s['request']);self.assertEqual(c.removable,s['removable'])
            for width in range(40):
                row=c.line(width);self.assertLessEqual(ui.cells(row.text),width)
                for span in row.spans:self.assertTrue(0<=span.start<span.start+span.width<=width)
        items=[ui.Shortcut(**i)for i in F['shortcuts']];h=ui.Help(items);items[1].text='changed'
        self.assertEqual(h.layout(40,1)[0].text,'[F1] Help');self.assertEqual(h.layout(40,2)[1].role,'disabled')
        for keys in F['duplicate_keys']:
            with self.assertRaises(ValueError):ui.Help([ui.Shortcut(k)for k in keys])
        with self.assertRaises(ValueError):ui.Help([ui.Shortcut(' 　')])
        for theme in ['dark','light','blackwhite']:
            for colors in ['8','16','256','truecolor']:
                for width in range(20):
                    c=ui.Canvas(width,6,ui.Palette(theme,colors));ui.Badge(label='Selected',count=123,state=ui.ControlState(selected=True)).draw(c,ui.Rect(0,0,width,1));ui.Chip('tag','한글',ui.ControlState(disabled=True),True).draw(c,ui.Rect(0,1,width,1));h.draw(c,ui.Rect(0,2,width,4));self.assertIsNone(c.cursor)
                    if width:self.assertEqual(c.data[0][0].style.background,c.palette.style('selection').background)

    def test_example_host_approves_removal_and_density(self):
        from tuivory._layout_example import LayoutDemo
        h=LayoutDemo(True);c=ui.Canvas(72,18);h.draw(c,ui.Rect(1,1,70,15))
        off=next(hit for hit in h.hits if hit[1].id=='off');h.pointer(off[0].x,off[0].y,0);self.assertTrue(h.active);self.assertEqual(h.status,'')
        fixed=next(hit for hit in h.hits if hit[1].id=='fixed');h.pointer(fixed[0].x,fixed[0].y,0);self.assertTrue(h.active)
        active=next(hit for hit in h.hits if hit[1].id=='filter');h.pointer(active[0].x,active[0].y,0);self.assertFalse(h.active);self.assertTrue(h.filter.removable);self.assertEqual(h.hits,[])
        h.handle('insert',text='d');self.assertEqual(h.density,'comfortable');h.draw(c,ui.Rect(1,1,70,15));self.assertIsNone(c.cursor)
