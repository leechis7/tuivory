import dataclasses
import json
from pathlib import Path
import unittest
import tuivory as ui

ROOT = Path(__file__).resolve().parents[2]


class SharedCases(unittest.TestCase):
    def test_tree_navigation(self):
        fixture = json.loads((ROOT / 'design/tree-navigation.json').read_text())
        tree = ui.Tree([ui.Node(**n) for n in fixture['nodes']])
        for step in fixture['steps']:
            if step['action'] == 'click':
                event = tree.click(step['column'], step['row'], fixture['height'])
            else:
                event = tree.handle(step['action'], fixture['height'])
            self.assertEqual(tree.selected, step['selected'], step)
            self.assertEqual(sorted(tree.expanded), step['expanded'], step)
            self.assertEqual(tree.scroll, step['scroll'], step)
            self.assertEqual(tree.horizontal, step['horizontal'], step)
            self.assertEqual([n.id for n in tree.visible()], step['visible'], step)
            self.assertEqual((event.kind, event.id), (step.get('event', ''), step.get('id', '')), step)

    def test_tabs(self):
        fixture = json.loads((ROOT / 'design/components-cases.json').read_text())['tabs']
        tabs = ui.Tabs([ui.Tab(**n) for n in fixture['items']])
        for step in fixture['steps']:
            event = tabs.handle(step['action'])
            self.assertEqual((tabs.active, tabs.focused, event.kind, event.id),
                             (step['active'], step['focused'], step.get('event', ''), step.get('id', '')))

    def test_shared_unicode_widths(self):
        fixture = json.loads((ROOT / 'design/language-unicode-cases.json').read_text())
        for case in fixture['cases']:
            self.assertEqual(ui.cells(case['text']), case['cells'], case)

    def test_state(self):
        fixture = json.loads((ROOT / 'design/interaction-cases.json').read_text())
        for case in fixture['states']:
            state = ui.ControlState(**case['state'])
            for key in ('role', 'markers', 'focusable', 'activatable', 'editable'):
                self.assertEqual(getattr(state, key), case[key])


class Rendering(unittest.TestCase):
    def test_overlay_both_edges_and_cursor(self):
        for theme in ('dark', 'light', 'blackwhite'):
            for colors in ('8', '16', '256', 'truecolor'):
                p = ui.Palette(theme, colors)
                canvas = ui.Canvas(12, 3, p)
                canvas.write(0, 0, '한글💻abc')
                before = canvas.data[0][0].style
                canvas.write(1, 0, ' X', 'selection', width=2)
                self.assertEqual(canvas.data[0][0].text, ' ')
                self.assertEqual(canvas.data[0][0].style, before)
                self.assertFalse(canvas.data[0][3].continuation)
                self.assertEqual(canvas.data[0][3].text, " ")
                self.assertEqual(canvas.data[0][3].style, before)
                for i, cell in enumerate(canvas.data[0]):
                    if cell.continuation:
                        self.assertLess(cell.owner, i)
                        self.assertGreater(ui.cells(canvas.data[0][cell.owner].text), 1)
                editor = ui.Text('한글👩‍💻e\u0301', multiline=False)
                editor.draw(canvas, ui.Rect(2, 1, 4, 1))
                self.assertIsNotNone(canvas.cursor)
                output = canvas.ansi()
                self.assertNotIn(' q', output)
                self.assertNotIn('\x1b[?12', output)
                self.assertNotIn('|', canvas.lines()[1])
                self.assertIn('\x1b[?25h', output)

    def test_literal_escape_and_narrow(self):
        for width in range(0, 20):
            c = ui.Canvas(width, 4)
            tree = ui.Tree([ui.Node('a', '\x1b[31m한글'), ui.Node('b', 'emoji 👩‍💻')])
            tree.draw(c, ui.Rect(0, 0, width, 4))
            self.assertTrue(all(ui.cells(line) <= width for line in c.lines()))
            self.assertNotIn('\x1b', '\n'.join(c.lines()))

    def test_disabled_blocks_keys_and_mouse_all_palettes(self):
        for theme in ('dark', 'light', 'blackwhite'):
            for colors in ('8', '16', '256', 'truecolor'):
                form = ui.Form([ui.Field('off', kind='checkbox', state=ui.ControlState(disabled=True)),
                                ui.Field('on', kind='button', label='Run')])
                self.assertEqual(form.click(0, 0).kind, '')
                self.assertEqual(form.focused, 'on')
                c = ui.Canvas(20, 3, ui.Palette(theme, colors))
                form.draw(c, ui.Rect(0, 0, 20, 3))
                self.assertTrue(c.data[0][0].style.dim)
                self.assertFalse(form.fields[0].checked)


class HostBoundary(unittest.TestCase):
    def test_grid_approval_lifetime_and_raw_values(self):
        rows = [ui.Record('r', {'a': '한글|', 'b': 'unchanged'})]
        grid = ui.Grid([ui.Column('a', editable=True), ui.Column('b', editable=True)], rows)
        grid.edit_enabled = True
        self.assertTrue(grid.begin_edit())
        grid.handle('end')
        grid.handle('insert', text='💻')
        event = grid.handle('submit')
        self.assertEqual(rows[0].cells['a'], '한글|')
        self.assertEqual(event.data['value'], '한글|💻')
        c = ui.Canvas(30, 4)
        grid.draw(c, ui.Rect(0, 0, 30, 4))
        self.assertIsNone(c.cursor)
        self.assertTrue(grid.resolve_edit(event.data['id'], error='retry'))
        grid.draw(c, ui.Rect(0, 0, 30, 4))
        self.assertIsNotNone(c.cursor)
        grid.handle('submit')
        grid.set_rows([ui.Record('r', {'a': 'new source'})])
        self.assertFalse(grid.resolve_edit(event.data['id']))
        self.assertEqual(rows[0].cells['b'], 'unchanged')

    def test_paste_is_atomic_request_and_permissions(self):
        rows = [ui.Record('r', {'a': 'old', 'b': 'old'})]
        grid = ui.Grid([ui.Column('a', editable=True), ui.Column('b')], rows)
        self.assertEqual(grid.paste('one\ttwo').kind, 'paste_rejected')
        self.assertEqual(rows[0].cells, {'a': 'old', 'b': 'old'})
        grid.columns[1].editable = True
        request = grid.paste('"one\nline"\ttwo')
        self.assertEqual(request.kind, 'paste_request')
        self.assertEqual(request.data['changes'][0]['value'], 'one\nline')
        self.assertTrue(grid.resolve_paste(request.data['id']))
        self.assertFalse(grid.resolve_paste(request.data['id']))
        self.assertEqual(rows[0].cells['a'], 'old')

    def test_focus_menu_and_secret(self):
        focus = ui.Focus('root', [ui.FocusTarget('open')])
        focus.open('popup', [ui.FocusTarget('close')])
        self.assertTrue(focus.blocked('root'))
        self.assertEqual(focus.close('popup').id, 'open')
        form = ui.Form([ui.Field('pw', kind='password', value='private 한글')])
        self.assertEqual(form.value('pw'), 'private 한글')
        c = ui.Canvas(20, 3)
        form.draw(c, ui.Rect(0, 0, 20, 3))
        self.assertNotIn('private', ''.join(c.lines()))
        form.handle('select_all')
        self.assertEqual(form.handle('copy').text, '')
        menu = ui.Menu([ui.Item('root'), ui.Item('off', parent='root', disabled=True), ui.Item('run', parent='root')])
        menu.open('root', 'editor')
        self.assertEqual(menu.click(0, 0).kind, '')
        event = menu.handle('activate')
        self.assertEqual((event.id, event.data['return_id']), ('run', 'editor'))

    def test_layout_never_overflows(self):
        for width in range(40):
            rect = ui.Rect(0, 0, width, 8)
            a, divider, b = ui.split(rect, 20, 10, 10)
            self.assertEqual(a.width + divider.width + b.width, width)
            popup = ui.popup_placement(ui.Rect(width, 7, 1, 1), rect, 20, 6, ui.ShadowOptions("auto"))
            card, bounds = popup.card,popup.bounds
            self.assertLessEqual(bounds.x + bounds.width, width)
            self.assertLessEqual(bounds.y + bounds.height, 8)
            self.assertLessEqual(card.width, bounds.width)


if __name__ == '__main__':
    unittest.main()
