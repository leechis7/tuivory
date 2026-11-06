import json
from pathlib import Path
import unittest
import tuivory as ui
F = json.loads((Path(__file__).resolve().parents[2] / 'design/controls-cases.json').read_text())['layout']

def item(d):
    d = dict(d)
    if 'track' in d:
        d['track'] = ui.Track(**d['track'])
    if 'area' in d:
        d['area'] = ui.Rect(**d['area'])
    return ui.LayoutItem(**d)

def options(d):
    d = dict(d)
    for key in ['rows', 'columns']:
        if key in d:
            d[key] = [ui.Track(**t) for t in d[key]]
    return ui.ContainerOptions(**d)

class Containers(unittest.TestCase):

    def test_shared_geometry_and_tiny_bounds(self):
        for f in F:
            items = [item(i) for i in f['items']]
            o = options(f['options'])
            r = ui.compute_container(ui.Rect(**f['bounds']), items, o)
            self.assertEqual([[n.id, n.rect.x, n.rect.y, n.rect.width, n.rect.height] for n in r], f['expected'])
            for w in range(25):
                for h in range(10):
                    for n in ui.compute_container(ui.Rect(2, 3, w, h), items, o):
                        b = n.rect
                        self.assertTrue(2 <= b.x <= b.x + b.width <= 2 + w)
                        self.assertTrue(3 <= b.y <= b.y + b.height <= 3 + h)
        with self.assertRaises(ValueError):
            ui.compute_container(ui.Rect(), [ui.LayoutItem('x'), ui.LayoutItem('x')], ui.ContainerOptions())

    def test_modal_restoration_capture_and_atomic_update(self):
        items = [ui.LayoutItem('a'), ui.LayoutItem('b')]
        s = ui.ContainerState()
        s.reconcile(items)
        self.assertEqual(s.move_focus(items), 'b')
        items.append(ui.LayoutItem('popup', modal=True))
        s.reconcile(items)
        self.assertEqual(s.focused, 'popup')
        self.assertEqual(s.eligible(items), ['popup'])
        items.append(ui.LayoutItem('nested', modal=True))
        s.reconcile(items)
        self.assertEqual(s.focused, 'nested')
        s.captured = 'nested'
        items = items[:2]
        s.reconcile(items)
        self.assertEqual(s.focused, 'b')
        self.assertEqual(s.captured, '')
        container = ui.Container(items)
        items[0].id = 'changed'
        self.assertEqual(container.items[0].id, 'a')
        with self.assertRaises(ValueError):
            container.set_items([ui.LayoutItem('same'), ui.LayoutItem('same')])
        self.assertEqual(container.items[0].id, 'a')

    def test_clipped_callbacks_scroll_actual_cursor_and_failure(self):
        items = [ui.LayoutItem('top', track=ui.Track(fixed=1)), ui.LayoutItem('editor', track=ui.Track(fixed=1))]
        o = ui.ContainerOptions(kind='column', virtual_width=8, virtual_height=3)
        container = ui.Container(items, o)
        container.state.focused = 'editor'
        container.scroll_x = 2
        container.scroll_y = 1

        def paint(id, c, focused):
            c.write(-1, 0, '界a界b한c', 'selection')
            c.write(0, 99, 'overflow')
            c.set_cursor(3, 0, 2)
        c = ui.Canvas(9, 4)
        c.write(0, 0, 'Outside')
        container.draw(c, ui.Rect(1, 1, 5, 1), paint)
        self.assertEqual(c.cursor, (2, 1))
        self.assertEqual(container.pointer(2, 1, True), 'editor')
        self.assertEqual(container.pointer(50, 50, release=True), 'editor')
        self.assertEqual(container.state.captured, '')
        self.assertEqual(c.lines()[0], 'Outside  ')
        self.assertEqual(c.lines()[2], ' ' * 9)
        before = c.ansi()

        def fail(*args):
            raise RuntimeError('host')
        with self.assertRaises(RuntimeError):
            container.draw(c, ui.Rect(1, 1, 5, 1), fail)
        self.assertEqual(c.ansi(), before)
        container.set_items([ui.LayoutItem('editor', disabled=True)], ui.ContainerOptions())
        container.draw(c, ui.Rect(1, 1, 5, 1), paint)
        self.assertIsNone(c.cursor)
        container.scroll_x = 1000001
        with self.assertRaises(ValueError):
            container.draw(c, ui.Rect(1, 1, 5, 1), paint)
