import unittest,json
from pathlib import Path
import tuivory as ui
R=Path(__file__).resolve().parents[2]
GEOMETRY=json.loads((R/'design/popup-shadow-cases.json').read_text())['cases']
RENDER=json.loads((R/'design/popup-shadow-render-cases.json').read_text())['cases']
class Popups(unittest.TestCase):
    def test_shared_popup_placement_and_hit_excludes_shadow(self):
        for f in GEOMETRY:
            o=f['options'];layout=ui.popup_placement(ui.Rect(*f['anchor']),ui.Rect(*f['viewport']),f['width'],f['height'],ui.ShadowOptions(o['mode'],o['offsetX'],o['offsetY']))
            for key,values in f['expected'].items():self.assertEqual(list(vars(getattr(layout,key)).values()),values,f['name'])
            for r in layout.shadow_regions():
                for y in range(r.y,r.y+r.height):
                    for x in range(r.x,r.x+r.width):self.assertFalse(layout.hit(x,y),f['name'])
        with self.assertRaises(ValueError):ui.ShadowOptions('invalid').layout(ui.Rect())
        with self.assertRaises(ValueError):ui.popup_placement(ui.Rect(),ui.Rect(),-1,1)
    def test_known_actual_backdrops_and_half_ascii_shape(self):
        for f in RENDER:
            for ascii in (False,True):
                c=ui.Canvas(20,10,ui.Palette(f['theme'],f['colors']));style=ui.Style('1',f['backdrop'],True,False,True)
                for y in range(10):c.write_style(0,y,'A'*20,style)
                layout=ui.Shadow(ui.ShadowOptions(f['mode'])).draw(c,ui.Rect(2,1,10,7),lambda child:child.panel(ui.Rect(0,0,child.width,child.height),'Popup',ascii=ascii),ascii=ascii)
                for x,y,symbol in [(11,1,'▄'),(3,7,'▀')]:
                    cell=c.data[y][x];self.assertEqual(cell.text,'.'if ascii else symbol);self.assertEqual(cell.style,ui.Style(f['shade'],f['backdrop']))
                middle=c.data[2][11];self.assertEqual(middle.text,'.'if ascii else' ');self.assertEqual(middle.style.background,f['backdrop']if ascii else f['shade'])
                self.assertFalse(layout.hit(11,2));self.assertIn('\x1b[',c.ansi())
    def test_wide_edges_dim_ownership_cursor_and_failure(self):
        for theme in ['dark','light','blackwhite']:
            for colors in ['8','16','256','truecolor']:
                for mode in ['off','auto','solid','dim']:
                    for ascii in (False,True):
                        c=ui.Canvas(22,12,ui.Palette(theme,colors));style=c.palette.style('body')
                        for y in range(12):c.write_style(0,y,'界'*11,style)
                        old_styles=[[cell.style for cell in row]for row in c.data];c.set_cursor(6,8,2)
                        bounds=ui.Rect(3,2,10,7);shadow=ui.Shadow(ui.ShadowOptions(mode));layout=shadow.draw(c,bounds,lambda child:child.panel(ui.Rect(0,0,child.width,child.height),'Popup',ascii=ascii),ascii=ascii)
                        self.assertIsNone(c.cursor)
                        for x,y,symbol in [(layout.card.x,layout.card.y,'┌'),(layout.card.x+layout.card.width-1,layout.card.y,'┐'),(layout.card.x,layout.card.y+layout.card.height-1,'└'),(layout.card.x+layout.card.width-1,layout.card.y+layout.card.height-1,'┘')]:self.assertEqual(c.data[y][x].text,'+'if ascii else symbol)
                        for y,row in enumerate(c.data):
                            for x,cell in enumerate(row):
                                if not bounds.contains(x,y):self.assertEqual(cell.style,old_styles[y][x])
                                if cell.continuation:self.assertTrue(0<=cell.owner<x and not row[cell.owner].continuation and ui.cells(row[cell.owner].text)>x-cell.owner)
                        if mode=='dim':self.assertTrue(c.data[8][6].style.dim);self.assertEqual(c.data[8][6].text,'界')
                        c.set_cursor(0,0,2);shadow.draw(c,bounds,lambda child:child.panel(ui.Rect(0,0,child.width,child.height),'Popup',ascii=ascii),ascii=ascii);self.assertEqual(c.cursor,(0,0))
                        before=c.ansi()
                        def fail(child):child.fill(ui.Rect(0,0,child.width,child.height));raise RuntimeError('host')
                        with self.assertRaises(RuntimeError):shadow.draw(c,bounds,fail,ascii=ascii)
                        self.assertEqual(c.ansi(),before)
                        shadow.draw(c,ui.Rect(100,100,10,7),lambda child:None);self.assertEqual(c.ansi(),before)
