import json
from pathlib import Path
import unittest
import tuivory as ui
F = json.loads((Path(__file__).resolve().parents[2] / 'design/canvas-copy-cases.json').read_text())

class CanvasCopy(unittest.TestCase):

    def test_copy_edges_palette_and_cursor(self):
        for theme in ['dark', 'light', 'blackwhite']:
            for colors in ['8', '16', '256', 'truecolor']:
                palette = ui.Palette(theme, colors)
                for case in F['cases']:
                    src = ui.Canvas(8, 1, palette)
                    src.write(0, 0, F['text'], 'selection')
                    src.set_cursor(4, 0, 2)
                    dst = ui.Canvas(case['width'], 1, palette)
                    dst.blit(src, ui.Rect(*case['region']), *case['at'])
                    self.assertEqual(dst.lines(), [case['expected']])
                    self.assertEqual(list(dst.cursor) if dst.cursor else None, case['cursor'])
                    for cell in dst.data[0]:
                        if cell.text not in (' ', ''):
                            self.assertEqual(cell.style, palette.style('selection'))
                    if dst.cursor:
                        self.assertIn('\x1b[?25h', dst.ansi())
                    else:
                        self.assertNotIn('\x1b[?25h', dst.ansi())

    def test_snapshot_ownership_and_opaque_cursor(self):
        c = ui.Canvas(8, 1)
        c.write(0, 0, 'a界b한c')
        c.set_cursor(4, 0, 2)
        c.blit(c, ui.Rect(0, 0, 6, 1), 2, 0)
        self.assertEqual(c.lines(), ['a a界b한'])
        self.assertEqual(c.cursor, (6, 0))
        c.fill(ui.Rect(7, 0, 1, 1))
        self.assertIsNone(c.cursor)
        self.assertEqual(c.lines(), ['a a界b  '])
        c.set_cursor(2, 0)
        c.clear_cursor(ui.Rect(4, 0, 1, 1))
        self.assertIsNotNone(c.cursor)
        c.clear_cursor()
        self.assertIsNone(c.cursor)
        s = ui.Canvas(2, 1)
        s.write(0, 0, '界')
        d = ui.Canvas(4, 1)
        d.write(0, 0, '界界')
        d.set_cursor(0, 0, 2)
        d.blit(s, ui.Rect(0, 0, 2, 1), 1, 0)
        self.assertEqual(d.lines(), [' 界 '])
        self.assertIsNone(d.cursor)
        s.fill(ui.Rect(0, 0, 2, 1))
        self.assertEqual(d.lines(), [' 界 '])
        with self.assertRaises(ValueError):
            d.blit(s, ui.Rect(0, 0, -1, 1), 0, 0)
