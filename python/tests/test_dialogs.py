import json,unittest
from pathlib import Path
import tuivory as ui
F=json.loads((Path(__file__).resolve().parents[2]/'design/dialog-cases.json').read_text())
class Dialogs(unittest.TestCase):
    def dialog(self):return ui.Dialog('Confirm',F['message'],[ui.DialogButton(**b)for b in F['buttons']],'cancel')
    def test_shared_wrapping_and_request_only_actions(self):
        d=self.dialog();self.assertEqual(d.focused,'cancel')
        for f in F['layouts']:
            l=d.layout(f['width'],f['height']);self.assertEqual(l.body,f['body']);self.assertEqual([[b.id,b.rect.x,b.rect.y,b.rect.width,b.rect.height]for b in l.buttons],f['buttons']);self.assertEqual((l.hidden_buttons,l.body_truncated),(f['hidden'],f['truncated']))
        self.assertEqual(d.handle('activate').id,'cancel');self.assertEqual(d.handle('cancel').kind,'cancel');self.assertEqual(d.focused,'cancel');self.assertEqual(d.message,F['message'])
        buttons=d.buttons;buttons[-1].disabled=True;d.set_buttons(buttons);self.assertEqual(d.focused,'retry');self.assertEqual(d.handle('cancel').kind,'');self.assertFalse(d.focus('cancel'));self.assertEqual(d.handle('next').id,'details');self.assertEqual(d.handle('next').id,'retry')
        before=d.buttons
        with self.assertRaises(ValueError):d.set_buttons([ui.DialogButton('same'),ui.DialogButton('same')])
        self.assertEqual(d.buttons,before)
    def test_actual_narrow_cancel_state_hit_and_snapshot(self):
        for theme in ['dark','light','blackwhite']:
            for colors in ['8','16','256','truecolor']:
                for ascii in (False,True):
                    d=self.dialog();c=ui.Canvas(40,12,ui.Palette(theme,colors));d.draw(c,ui.Rect(0,0,40,12),ascii=ascii);hit=next(r for r,id,off in d._hits if id=='cancel');self.assertTrue(hit.x+hit.width<=40);self.assertIn('Cancel',c.lines()[hit.y]);self.assertIsNone(c.cursor);self.assertEqual(d.click(hit.x,hit.y).id,'cancel')
                    d.draw(c,ui.Rect(0,0,40,12),ascii=ascii);buttons=d.buttons;buttons[-1].disabled=True;d.set_buttons(buttons);self.assertEqual(d.click(hit.x,hit.y).kind,'');d.draw(c,ui.Rect(0,0,40,12),ascii=ascii);off=next(r for r,id,disabled in d._hits if id=='cancel');focus=d.focused;self.assertEqual(d.click(off.x,off.y).kind,'');self.assertEqual(d.focused,focus);self.assertTrue(c.data[off.y][off.x].style.dim)
                    for w in range(12):
                        tiny=ui.Canvas(w,5,c.palette);layout=d.draw(tiny,ui.Rect(0,0,w,5),ascii=ascii)
                        for r,id,disabled in d._hits:self.assertTrue(0<=r.x<r.x+r.width<=w and 0<=r.y<5)
        d=self.dialog();d.set_text(message='한글\r\né [error]literal[/]');self.assertEqual(d.message,'한글\r\né [error]literal[/]');self.assertTrue(any('[error]'in s for s in d.layout(40,12).body))
    def test_public_star_exports_cover_completed_components(self):
        values={};exec('from tuivory import *',values)
        for name in ['Container','Surface','Shadow','Dialog']:self.assertIn(name,values)

    def test_button_rows_center_for_bilingual_labels(self):
        for labels in (
            ('확인', '다시 연결한 다음 계속', '설정 열기', '취소'),
            ('OK', 'Reconnect and continue', 'Open settings', 'Cancel'),
        ):
            for count in range(1, len(labels) + 1):
                buttons = [ui.DialogButton(str(i), label) for i, label in enumerate(labels[:count])]
                dialog = ui.Dialog(buttons=buttons, cancel_id='0')
                for width in (36, 116):
                    layout = dialog.layout(width, 12)
                    self.assertEqual(len(layout.buttons), count)
                    rows = {}
                    for button in layout.buttons:
                        rect = button.rect
                        left = rows.get(rect.y, (rect.x,))[0]
                        rows[rect.y] = left, rect.x + rect.width
                    for left, right in rows.values():
                        self.assertLessEqual(right, width)
                        self.assertEqual(left, (width - (right - left)) // 2)
