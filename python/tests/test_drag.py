import json,unittest
from copy import deepcopy
from pathlib import Path
from tuivory import *
F=json.loads((Path(__file__).resolve().parents[2]/'design/drag-cases.json').read_text())
def tabs():return Tabs([Tab(**x)for x in F['tabs']])
def tree():
    t=Tree([Node(**x)for x in F['tree']]);t.expanded={'root','a'};return t

class Drag(unittest.TestCase):
    def test_shared_immutable_requests_and_exact_revision(self):
        for case in F['cases']:
            with self.subTest(case=case):
                m=tabs()if case['kind']=='tabs'else tree();before=deepcopy(vars(m))
                rev=drag_revision(m);self.assertEqual(rev,F['tab_revision_hex'if isinstance(m,Tabs)else'tree_revision_hex'])
                o=DragOptions(locked=tuple(case.get('locked',[])))
                if 'error'in case:
                    with self.assertRaises(DropError)as raised:m.request_drop(case['source'],case['target'],case['position'],o,(lambda _:False)if case.get('deny')else None)
                    self.assertEqual(raised.exception.reason,case['error'])
                else:
                    r=m.request_drop(case['source'],case['target'],case['position'],o);n=m.apply_drop(r)
                    self.assertEqual([x.id for x in(n.items if isinstance(n,Tabs)else n.nodes)],case['order'])
                    if isinstance(n,Tree):self.assertEqual(n.by_id[case['source']].parent,case['parent'])
                    self.assertIsNot(n,m)
                self.assertEqual(vars(m),before)

    def test_tab_threshold_capture_policy_and_outside_release(self):
        m=tabs();d=DragState();self.assertIsNone(d.pointer(m,DragPointer('down',3,0,60,2)));self.assertFalse(d.captured)
        d.enabled=True;before=deepcopy(vars(m));d.pointer(m,DragPointer('down',3,0,60,2));self.assertTrue(d.captured)
        d.pointer(m,DragPointer('move',4,1,60,2));self.assertEqual(d.phase,'armed')
        d.pointer(m,DragPointer('up',4,1,60,2));self.assertEqual(d.result,'');self.assertFalse(d.captured)
        cells=m.layout(60);target=next(c for c in cells if c.id=='c');x=target.start+target.width-1
        d.pointer(m,DragPointer('down',3,0,60,2));d.pointer(m,DragPointer('move',x,0,60,2));self.assertTrue(d.allowed)
        request=d.pointer(m,DragPointer('up',x,0,60,2));self.assertEqual(request.target_id,'c');self.assertEqual(d.result,'drop')
        self.assertEqual(vars(m),before)
        d.pointer(m,DragPointer('down',3,0,60,2));d.pointer(m,DragPointer('move',70,0,60,2))
        self.assertIsNone(d.pointer(m,DragPointer('up',70,0,60,2)));self.assertEqual(d.result,'reject')
        d.pointer(m,DragPointer('down',3,0,60,2));d.cancel();self.assertEqual(d.result,'cancel')
        self.assertEqual(vars(m),before)

    def test_tree_preview_expand_and_policy_recheck(self):
        m=tree();before=deepcopy(vars(m));d=DragState(True);o=DragOptions(hover_expand=True)
        d.pointer(m,DragPointer('down',6,3,24,6),o)
        d.pointer(m,DragPointer('move',10,4,24,6),o)
        self.assertTrue(d.allowed);self.assertIn('c',d._expanded);self.assertNotIn('c',m.expanded)
        self.assertIn('c1',[n.id for n in d.preview_layout(m,24,6).rows])
        request=d.pointer(m,DragPointer('up',10,4,24,6),o)
        self.assertEqual((request.source_id,request.target_id,request.position),('b','c','inside'))
        self.assertEqual(vars(m),before)
        permission={'allowed':True};policy=lambda _:permission['allowed']
        d.pointer(m,DragPointer('down',6,3,24,6),o,policy);d.pointer(m,DragPointer('move',10,4,24,6),o,policy)
        permission['allowed']=False
        self.assertIsNone(d.pointer(m,DragPointer('up',10,4,24,6),o,policy));self.assertEqual(d.result,'reject')
        self.assertEqual(vars(m),before)

    def test_stale_data_state_and_render_context(self):
        for change in ('state','data','size','palette'):
            with self.subTest(change=change):
                m=tabs();d=DragState(True);c=Canvas(60,2);d.draw(m,c,Rect(0,0,60,2))
                d.pointer(m,DragPointer('down',3,0,60,2))
                if change=='state':m.focused='b'
                elif change=='data':m.items[0].title='new title'
                elif change=='size':c=Canvas(59,2)
                elif change=='palette':c=Canvas(60,2,Palette('light','8'))
                d.draw(m,c,Rect(0,0,c.width,2));self.assertFalse(d.captured);self.assertEqual(d.result,'stale')
        m=tabs();r=m.request_drop('a','c','after');m.items[0].edited=False
        with self.assertRaisesRegex(DropError,'stale'):m.apply_drop(r)

    def test_keyboard_and_model_metadata(self):
        m=tabs();m.focused='c';r=m.keyboard_drop('previous');self.assertEqual((r.source_id,r.target_id,r.position),('c','b','before'))
        n=m.apply_drop(r);self.assertEqual(n.focused,'c');self.assertTrue(n.items[0].edited)
        t=tree();t.selected='b';r=t.keyboard_drop('inside');self.assertEqual((r.target_id,r.position),('a','inside'))
        n=t.apply_drop(r);self.assertEqual(n.selected,'b');self.assertEqual(n.by_id['b'].parent,'a')
        n.selected='b';r=n.keyboard_drop('outside');self.assertEqual((r.target_id,r.position),('a','after'))

    def test_all_palettes_feedback_actual_background_and_wide_edges(self):
        for theme in ('dark','light','blackwhite'):
            for colors in ('8','16','256','truecolor'):
                for ascii in (False,True):
                    m=tree();before=deepcopy(vars(m));d=DragState(True);c=Canvas(28,8,Palette(theme,colors),'button.focus')
                    area=Rect(1,1,24,6);d.draw(m,c,area,ascii=ascii)
                    d.pointer(m,DragPointer('down',6,3,24,6));d.pointer(m,DragPointer('move',10,4,24,6))
                    d.draw(m,c,area,ascii=ascii);marker=c.data[5][1]
                    self.assertEqual(marker.text,'+'if ascii else'↳');self.assertTrue(marker.style.bold and marker.style.underline)
                    self.assertEqual(marker.style.background,c.palette.style('button.focus').background);self.assertIsNone(c.cursor)
                    for row in c.data:
                        for cell in row:
                            if cell.continuation:self.assertGreater(cells(row[cell.owner].text),1)
                    self.assertEqual(vars(m),before);d.cancel()

    def test_reentrant_policy_and_atomic_invalid_input(self):
        m=tabs();d=DragState(True);d.pointer(m,DragPointer('down',3,0,60,1))
        before=(d.phase,d.source_id)
        with self.assertRaises(DropError):d.pointer(m,DragPointer('move',10,0,-1,1))
        self.assertEqual((d.phase,d.source_id),before)
        target=next(c for c in m.layout(60)if c.id=='c');x=target.start+target.width-1
        d.pointer(m,DragPointer('move',x,0,60,1),allow=lambda _:d.cancel())
        self.assertFalse(d.allowed);self.assertEqual(d.reason,'policy')

    def test_depth_limit_and_focus_loss(self):
        nodes=[Node('n0')]
        for i in range(1,129):nodes.append(Node('n'+str(i),parent='n'+str(i-1),branch=i==128))
        nodes.append(Node('move'))
        m=Tree(nodes)
        with self.assertRaisesRegex(DropError,'depth'):m.request_drop('move','n128','inside')
        m=tabs();d=DragState(True);c=Canvas(60,2);d.draw(m,c,Rect(0,0,60,2));d.pointer(m,DragPointer('down',3,0,60,2))
        before=(d.phase,d.source_id)
        with self.assertRaisesRegex(DropError,'bounds'):d.draw(m,c,Rect(0,0,65536,2))
        self.assertEqual((d.phase,d.source_id),before)
        d.draw(m,c,Rect(0,0,60,2),focused=False);self.assertEqual(d.result,'cancel');self.assertFalse(d.captured)

    def test_preview_and_render_context_reentry_is_rejected(self):
        for name in ('preview', 'render'):
            m=tabs();d=DragState(True)
            d.pointer(m,DragPointer('down',3,0,60,1))
            target=next(c for c in m.layout(60)if c.id=='c')
            def policy(_):
                if name=='preview':d.preview_layout(m,60,1)
                else:d.render_key('changed inside policy')
                return True
            d.pointer(m,DragPointer('move',target.start+target.width-1,0,60,1),allow=policy)
            self.assertFalse(d.allowed);self.assertEqual(d.reason,'policy');self.assertTrue(d.captured)
