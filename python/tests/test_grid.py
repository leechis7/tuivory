"""Grid state/host boundary and real Canvas output, shared across independent ports."""
import json
from pathlib import Path
import unittest
from tuivory import *

ROOT = Path(__file__).resolve().parents[2]


def model(rows=None):
    g=Grid([Column('a','Name',6,True),Column('b','Value',8,True)],
           rows if rows is not None else [Record('r1',{'a':'한글','b':None}),Record('r2',{'a':'Straße','b':'two'})])
    g.edit_enabled=True
    return g


class GridWork(unittest.TestCase):
    def test_shared_strict_tsv(self):
        for case in json.loads((ROOT/'design/grid-work-cases.json').read_text())['cases']:
            with self.subTest(case=case['id']):
                if case['accepted']:
                    rows=parse_grid_tsv(case['text'])
                    self.assertEqual([v for row in rows for v in row],case['values'])
                    self.assertEqual(parse_grid_tsv(format_grid_tsv(rows)),rows)
                else:
                    with self.assertRaises(ValueError): parse_grid_tsv(case['text'])
        with self.assertRaises(ValueError): parse_grid_tsv('a\tb',1)

    def test_real_cursor_fixtures(self):
        for case in json.loads((ROOT/'design/grid-cursor-cases.json').read_text())['cases']:
            with self.subTest(case=case['id']):
                g=Grid([Column('a','A',case['width'],True)],[Record('r',{'a':case['text']})]);g.edit_enabled=True
                self.assertTrue(g.begin_edit());g.edit['buffer'].select(case['cursor'],case['cursor'])
                c=Canvas(case['width'],2);g.draw(c,Rect(0,0,c.width,c.height))
                self.assertEqual(c.lines()[1],case['visible_text']+' '*(case['width']-cells(case['visible_text'])))
                self.assertEqual(c.cursor,(case['x'],1))
                self.assertIn('\x1b[?25h',c.ansi())
                event=g.handle('submit');c=Canvas(c.width,c.height);g.draw(c,Rect(0,0,c.width,c.height));self.assertIsNone(c.cursor)
                self.assertTrue(g.resolve_edit(event.data['id'],error='retry'))

    def test_nonce_retry_stale_and_ownership(self):
        original=[Record('r',{'a':'old'})];g=model(original);original[0].cells['a']='outside'
        self.assertEqual(g.rows[0].cells['a'],'old')
        snapshot=g.rows;snapshot[0].cells['a']='snapshot'
        self.assertEqual(g.rows[0].cells['a'],'old')
        g.begin_edit();g.handle('insert',text='!');first=g.handle('submit')
        self.assertEqual(g.rows[0].cells['a'],'old')
        self.assertTrue(g.resolve_edit(first.data['id'],error='denied'))
        second=g.handle('submit');self.assertNotEqual(first.data['id'],second.data['id'])
        self.assertFalse(g.resolve_edit(first.data['id']))
        g.columns[0].editable=False
        self.assertFalse(g.resolve_edit(second.data['id']));self.assertIsNone(g.edit)
        g.columns[0].editable=True;g.begin_edit();third=g.handle('submit')
        g.set_rows([Record('r',{'a':'replacement'})]);self.assertFalse(g.resolve_edit(third.data['id']))

    def test_row_and_cell_permission_are_combined(self):
        for flag in ('disabled','busy','read_only'):
            with self.subTest(flag=flag):
                g=model([Record('r',{'a':'x'},ControlState(**{flag:True}),{'a':ControlState()})])
                self.assertFalse(g.begin_edit());self.assertEqual(g.paste('new').kind,'paste_rejected')
        g=model();g.prepare=lambda r,c:False
        self.assertFalse(g.begin_edit());self.assertEqual(g.paste('new').kind,'paste_rejected')
        g.prepare=None;g.begin_edit();g.prepare=lambda r,c:False
        self.assertEqual(g.handle('insert',text='x').kind,'edit_stale');self.assertIsNone(g.edit)

    def test_paste_atomic_permissions_and_detached_events(self):
        g=model();e=g.paste('one\ttwo\nthree\tfour');self.assertEqual(e.kind,'paste_request')
        e.data['changes'][0]['row_id']='tamper'
        self.assertEqual(g.pending_paste['changes'][0]['row_id'],'r1')
        g.columns[1].editable=False
        self.assertFalse(g.resolve_paste(e.data['id']));self.assertIsNone(g.pending_paste)
        self.assertEqual(g.rows[0].cells['a'],'한글')
        g.columns[1].editable=True;e=g.paste('one\ttwo')
        self.assertTrue(g.resolve_paste(e.data['id']));self.assertFalse(g.resolve_paste(e.data['id']))
        self.assertEqual(g.rows[0].cells['a'],'한글')
        e=g.paste('NULL\t""',null_text='NULL');self.assertEqual([v['value'] for v in e.data['changes']],[None,''])

    def test_virtual_source_bounded_work_and_deep_copy(self):
        class Source:
            calls=0
            def __len__(self): return 10_000_000
            def row(self,i):
                self.calls+=1
                return Record(str(i),{'a':'한글','b':str(i)})
            def index_of(self,id): return int(id) if id.isdigit() and int(id)<len(self) else None
        source=Source();g=Grid([Column('a',width=5),Column('b',width=5)],source)
        g.focus('9999999','a');c=Canvas(20,6);g.draw(c,Rect(0,0,20,6))
        self.assertLess(source.calls,100);self.assertEqual(g.row_id,'9999999')
        class Invalid(Source):
            def index_of(self,id): return 0
        with self.assertRaises(ValueError): g.set_source(Invalid())
        self.assertEqual(g.row_id,'9999999')

    def test_copy_find_display_null_and_limits(self):
        g=model();g.set_selection(GridRange('r1','a','r2','b'))
        self.assertEqual(parse_grid_tsv(g.copy_selection().text),[['한글','NULL'],['Straße','two']])
        o=g.options;o.max_copy_cells=3;g.set_options(o);self.assertEqual(g.copy_selection().kind,'copy_rejected')
        self.assertTrue(g.find('STRASSE'));self.assertEqual((g.row_id,g.column_id),('r2','a'))
        g.case_sensitive=True;self.assertFalse(g.find('STRASSE'))
        info=GridCellInfo(display='shown',has_display=True,numeric=True)
        g.cell_info=lambda r,c:info;g.use_display=True;self.assertTrue(g.find('shown'))
        self.assertEqual(info.state,ControlState())
        g.case_sensitive=False;g.use_display=False;self.assertFalse(g.find('shown'))

    def test_requests_stale_async_data_and_next_edit(self):
        g=model();one=g.request('search','old');two=g.request('search','new')
        self.assertFalse(g.apply_source(one.data['revision'],MemoryRows([Record('old')])) )
        self.assertTrue(g.apply_source(two.data['revision'],MemoryRows([Record('new',{'a':'fresh'})])))
        self.assertFalse(g.apply_source(two.data['revision'],MemoryRows([])))
        self.assertEqual(g.row_id,'new');g.begin_edit();e=g.handle('next')
        self.assertEqual(g.column_id,'a');self.assertTrue(g.resolve_edit(e.data['id']))
        self.assertEqual(g.column_id,'b');self.assertEqual(g.edit['column_id'],'b')

    def test_atomic_view_restore_and_callback_mutation(self):
        g=model();g.set_selection(GridRange('r1','a','r2','b'));view=g.save_view()
        g.focus('r2','b');g.restore_view(view);self.assertEqual((g.row_id,g.column_id),('r1','a'))
        before=g.save_view();bad=g.save_view();bad['columns'][0]['width']=0
        g.begin_edit()
        with self.assertRaises(ValueError):g.restore_view(bad)
        self.assertEqual(g.save_view(),before);self.assertIsNotNone(g.edit)
        g.prepare=lambda r,c:g.set_rows([])
        with self.assertRaises(ValueError):g.handle('submit')
        self.assertEqual(len(g.rows),2)

    def test_all_palettes_render_cursor_disabled_and_narrow(self):
        for theme in ('dark','light','blackwhite'):
            for colors in ('8','16','256','truecolor'):
                for ascii in (False,True):
                    g=model();o=grid_preset('data').with_density('comfortable');o.ascii=ascii;g.set_options(o)
                    g.cell_info=lambda r,c:GridCellInfo(state=ControlState(disabled=r.id=='r2'))
                    for width in (0,1,4,12,30):
                        c=Canvas(width,6,Palette(theme,colors));g.draw(c,Rect(0,0,width,6),ascii=ascii)
                        for row in c.data:
                            for i,cell in enumerate(row):
                                if cell.continuation:self.assertGreater(cells(row[cell.owner].text),1)
                        self.assertIsNone(c.cursor)
                    c=Canvas(30,6,Palette(theme,colors));g.draw(c,Rect(0,0,30,6))
                    self.assertTrue(any(cell.style.dim for cell in c.data[3]))
                    self.assertEqual(g.click(4,3,30,6).kind,'')
                    self.assertEqual(g.click(4,1,29,6).kind,'')

    def test_pins_pan_and_view_selection_stable_ids(self):
        g=Grid([Column('a',width=3,pin='left'),Column('b',width=5),Column('c',width=3,pin='right')],[Record('r',{'a':'A','b':'a한bc','c':'C'})])
        g.set_column_options('b',GridColumnOptions(overflow='scroll'));g.pan_cell('b',2)
        c=Canvas(11,3);g.draw(c,Rect(0,0,11,3));self.assertEqual(c.lines()[1],'A   bc  C  ')
        spans=g.geometry(11,3).columns;self.assertEqual([(s.id,s.x) for s in spans],[('a',0),('b',3),('c',8)])
        g.set_selection(GridRange('r','a','r','c'));g.set_rows([Record('r',{'a':'new'})]);self.assertIsNotNone(g.selected)

    def test_virtual_source_reentry_and_stale_pointer_ids(self):
        class Source:
            def __init__(self): self.items=[Record('r1',{'a':'first'}),Record('r2',{'a':'second'})]; self.reenter=False; self.grid=None
            def __len__(self): return len(self.items)
            def row(self,i):
                if self.reenter: self.grid.focus('r2','a')
                return self.items[i]
            def index_of(self,id): return next((i for i,r in enumerate(self.items) if r.id==id),None)
        source=Source();g=Grid([Column('a',width=8,editable=True)],source);source.grid=g
        c=Canvas(10,4);g.draw(c,Rect(0,0,10,4));source.items.reverse()
        self.assertEqual(g.click(1,1,10,4).kind,'')
        g.draw(c,Rect(0,0,10,4));self.assertEqual(g.click(1,1,10,4).id,'r2')
        g.columns[0].width=4;self.assertEqual(g.click(1,0,10,4).kind,'')
        source.reenter=True;before=c.lines()
        with self.assertRaises(ValueError):g.draw(c,Rect(0,0,10,4))
        self.assertEqual(c.lines(),before)
        source.reenter=False;self.assertEqual(g.row_id,'r2')

    def test_prepared_values_and_callback_focus_guard(self):
        g=model();g.set_edit_options(GridEditOptions(True,True,True,lambda r,c:GridValue('prepared')))
        self.assertEqual(g.handle('insert',text='typed').kind,'edit_begin');self.assertEqual(g.edit['buffer'].value,'typed')
        g.handle('cancel');self.assertTrue(g.begin_edit());self.assertEqual(g.edit['buffer'].value,'prepared')
        g.handle('null');self.assertIsNone(g.handle('submit').data['value'])
        g.set_edit_options(GridEditOptions(True,False,False,lambda r,c:None));self.assertFalse(g.begin_edit())
        g.prepare=lambda r,c:g.focus('r2','b')
        with self.assertRaises(ValueError):g.begin_edit()
        self.assertEqual((g.row_id,g.column_id),('r1','a'))

    def test_auto_fit_labels_are_literal_and_preserve_editor(self):
        g=Grid([Column('a','A',2,True)],[Record('r',{'a':None})])
        g.set_labels(GridLabels(null_text='한글'));g.set_column_options('a',GridColumnOptions(auto_fit=True,max_width=8))
        self.assertEqual(g.geometry(20,4).columns[0].width,4);self.assertEqual(g.columns[0].width,2)
        g.set_edit_options(GridEditOptions(True,False,True));self.assertTrue(g.begin_edit())
        c=Canvas(20,4);g.draw(c,Rect(0,0,20,4));self.assertIn('한글',c.lines()[1]);self.assertIsNone(c.cursor)
        self.assertIsNotNone(g.edit);e=g.handle('submit');g.geometry(20,4);self.assertTrue(g.edit['pending']);self.assertTrue(g.resolve_edit(e.data['id']))
        external=g.labels;external.null_text='outside';self.assertEqual(g.labels.null_text,'한글')
        g.set_labels(GridLabels(null_text='[x]'));g.draw(c,Rect(0,0,20,4));self.assertIn('[x]',c.lines()[1])

if __name__=='__main__':unittest.main()
