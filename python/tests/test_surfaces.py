import unittest,json
from pathlib import Path
from copy import deepcopy
import tuivory as ui
from tuivory.drawing import color_contrast
F=json.loads((Path(__file__).resolve().parents[2]/'design/surface-cases.json').read_text())
class Surfaces(unittest.TestCase):
    def test_reference_styles_and_state_precedence(self):
        for f in F['text']:
            p=ui.Palette(f['theme'],f['colors']);before=deepcopy(p.roles);s=p.text_on_surface(f['role'],f['surface'])
            self.assertEqual((s.foreground,s.background,s.dim),(f['foreground'],f['background'],f.get('dim',False)));self.assertEqual(before,p.roles)
        for theme in ['dark','light','blackwhite']:
            for colors in ['8','16','256','truecolor']:
                p=ui.Palette(theme,colors)
                for surface in F['surfaces']:
                    for role in F['plain_roles']:
                        s=p.text_on_surface(role,surface);raw=p.style(role);base=p.style(surface)
                        self.assertEqual(s.background,base.background)
                        self.assertGreaterEqual(color_contrast(s.foreground,base.background)+1e-12,color_contrast(raw.foreground,base.background))
                    for role in F['explicit_roles']:
                        c=ui.Canvas(2,1,p,surface);c.write(0,0,'X',role)
                        self.assertEqual(c.data[0][0].style,p.style(role))
                    for name in ['selected','edited']:
                        state=ui.ControlState(**{name:True});self.assertEqual(p.control_on_surface(state,surface),p.style(state.role))
                    s=p.control_on_surface(ui.ControlState(disabled=True,selected=True),surface,focused=True);self.assertFalse(s.underline);self.assertTrue(s.dim)
                    self.assertFalse(p.text_on_surface('disabled',surface,focused=True).underline)
    def test_borderless_nested_painting_exact_styles_and_failure(self):
        for theme in ['dark','light','blackwhite']:
            for colors in ['8','16','256','truecolor']:
                for surface in F['surfaces']:
                    c=ui.Canvas(26,10,ui.Palette(theme,colors));c.write(0,0,'Outside')
                    def paint(child):
                        self.assertEqual(child.surface_role,surface)
                        ui.Badge(label='Text').draw(child,ui.Rect(0,0,20,1));ui.Chip('off','Disabled',ui.ControlState(disabled=True)).draw(child,ui.Rect(0,1,20,1))
                        ui.Help([ui.Shortcut('x','Help')]).draw(child,ui.Rect(0,2,20,1))
                        child.panel(ui.Rect(0,3,20,3),'Panel',True)
                        child.write(0,6,'Selection','selection')
                        ui.Container([ui.LayoutItem('body')]).draw(child,ui.Rect(20,0,2,2),lambda id,inner,focused: inner.write(0,0,'OK'))
                        child.write_style(0,7,'Raw',child.palette.style('body'))
                    ui.Surface(surface).draw(c,ui.Rect(1,1,24,8),paint)
                    bg=c.palette.style(surface).background
                    for y in [1,2,3,4,5,6]:
                        for x in range(1,21):self.assertEqual(c.data[y][x].style.background,bg)
                    self.assertEqual(c.data[7][1].style.background,c.palette.style('selection').background)
                    self.assertEqual(c.data[1][21].style.background,bg)
                    self.assertEqual(c.data[8][1].style,c.palette.style('body'))
                    self.assertEqual(c.lines()[0],'Outside'+' '*19)
                    before=c.ansi()
                    def fail(child):child.write(0,0,'changed');raise RuntimeError('host')
                    with self.assertRaises(RuntimeError):ui.Surface(surface).draw(c,ui.Rect(1,1,24,8),fail)
                    self.assertEqual(before,c.ansi())
