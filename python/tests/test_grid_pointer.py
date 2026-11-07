import json,unittest
from pathlib import Path
from tuivory import *
F=json.loads((Path(__file__).resolve().parents[2]/'design/grid-pointer-cases.json').read_text())

def model(source=None):
    rows=[Record(r['id'],{'a':r['a'],'b':'b','c':'c'},ControlState(disabled=r.get('disabled',False),read_only=r.get('read_only',False)))for r in F['rows']]
    g=Grid([Column(c['id'],c['id'].upper(),c['width'],True)for c in F['columns']],source if source is not None else rows)
    g.set_options(grid_preset('data'));g.set_column_options('a',GridColumnOptions(min_width=4,max_width=14));g.set_edit_options(GridEditOptions(True))
    return g

def draw(g,width=64,height=10,theme='dark',focused=True):
    c=Canvas(width,height,Palette(theme,'8'));g.draw(c,Rect(0,0,width,height),focused=focused);return c

def point(g,location,width,height,origin):
    kind,*args=location
    if kind=='outside':return -3,height+3
    if kind=='delta':return origin[0]+args[0],origin[1]+args[1]
    geo=g.geometry(width,height)
    if kind in ('header','divider'):
        span=next(s for s in geo.columns if s.id==args[0]);return (span.x+span.width if kind=='divider'else span.x),0
    index=next(i for i,r in enumerate(F['rows'])if r['id']==args[0]);y=geo.header_rows+(index-geo.top)*geo.stride
    if kind=='gutter':return 0,y
    span=next(s for s in geo.columns if s.id==args[1])
    return span.x+(g.options.padding+args[2]if kind=='editor'else 0),y

class GridPointer(unittest.TestCase):
    def test_shared_pointer_cases(self):
        for case in F['cases']:
            with self.subTest(case=case['name']):
                g=model();origin=(0,0);width,height=F['width'],F['height'];draw(g,width,height)
                for step in case['steps']:
                    w,h=step.get('viewport',(width,height))
                    if 'key'in step:e=g.handle(step['key'],h)
                    else:
                        x,y=point(g,step['at'],w,h,origin)
                        if step['action']=='down':origin=(x,y)
                        e=g.pointer(step['action'],x,y,w,h,step.get('extend',False))
                    self.assertEqual(e.kind,step['event'],step)
                    for key,value in [('row',g.row_id),('column',g.column_id),('captured',g.pointer_captured),('range',list(vars(g.selected).values())if g.selected else None),('order',[c.id for c in g.columns]),('caret',[g.edit['buffer'].anchor,g.edit['buffer'].cursor]if g.edit else None)]:
                        if key in step:self.assertEqual(value,step[key],step)
                    if 'width'in step:self.assertEqual(next(c.width for c in g.columns if c.id==step['width'][0]),step['width'][1])
                    draw(g,w,h);width,height=w,h

    def test_stale_target_and_focus_or_palette_cancel_capture(self):
        class Source:
            def __init__(self):self.rows=[Record(r['id'],{'a':r['a'],'b':'b','c':'c'})for r in F['rows']]
            def __len__(self):return len(self.rows)
            def row(self,i):return self.rows[i]
            def index_of(self,id):return next((i for i,r in enumerate(self.rows)if r.id==id),None)
        src=Source();g=model(src);draw(g)
        x,y=point(g,['cell','r1','a'],64,10,(0,0));g.pointer('down',x,y,64,10);self.assertTrue(g.pointer_captured)
        src.rows[2],src.rows[3]=src.rows[3],src.rows[2]
        x,y=point(g,['cell','r3','b'],64,10,(0,0));self.assertFalse(g.pointer('move',x,y,64,10).kind)
        self.assertFalse(g.pointer_captured);self.assertEqual(g.row_id,'r1');self.assertIsNone(g.selected)
        draw(g);x,y=point(g,['cell','r1','a'],64,10,(0,0));g.pointer('down',x,y,64,10);draw(g,theme='light');self.assertFalse(g.pointer_captured)
        g.pointer('down',x,y,64,10);draw(g,theme='light',focused=False);self.assertFalse(g.pointer_captured)

    def test_selected_editor_grapheme_is_drawn_without_splitting(self):
        g=model();draw(g);x,y=point(g,['editor','r1','a',0],64,10,(0,0))
        g.pointer('double',x,y,64,10);draw(g);g.pointer('down',x+1,y,64,10);g.pointer('move',x+3,y,64,10)
        c=draw(g);self.assertEqual(c.data[y][x].text,'한');self.assertTrue(c.data[y][x+1].continuation)
        self.assertEqual(c.data[y][x].style.background,c.palette.style('selection').background)
        self.assertEqual(c.cursor[:2],(x+2,y))
