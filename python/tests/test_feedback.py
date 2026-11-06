import json
import unittest
from pathlib import Path
import tuivory as ui

F = json.loads((Path(__file__).resolve().parents[2]/'design/feedback-cases.json').read_text())
def notice(source):
    source = dict(source)
    source['actions'] = [ui.NoticeAction(**a) for a in source.get('actions', [])]
    return ui.Notice(**source)


class Feedback(unittest.TestCase):
    def test_shared_lifetime_requests_and_eviction(self):
        q = ui.NoticeQueue(3)
        for n in F['notice_items']:
            q.push(notice(n))
        for s in F['notice_steps']:
            op = s['operation']
            if op == 'visible':
                self.assertEqual([n.id for n in q.visible(s['now'])], s['ids'])
            elif op == 'handle':
                e = q.handle(s['action'], s['now'], s['height'])
                self.assertEqual(vars(e), s['event'])
            elif op == 'expire':
                self.assertEqual([e.id for e in q.expire(s['now'])], s['ids'])
            else:
                self.assertEqual(q.dismiss(s['id']), s['result'])
        for s in F['evictions']:
            q = ui.NoticeQueue(s['capacity'])
            for n in s['initial']:
                q.push(notice(n))
            if s['accepted']:
                q.push(notice(s['incoming']))
            else:
                with self.assertRaises(ValueError):
                    q.push(notice(s['incoming']))
            self.assertEqual([n.id for n in q.visible()], s['ids'])

    def test_ownership_atomicity_clipped_actions_and_expiry_hits(self):
        q = ui.NoticeQueue(3)
        n = notice(F['notice_items'][2]);q.push(n);n.text = 'changed';n.actions[0].disabled = False
        self.assertEqual(q.visible()[0].text, 'Failure')
        snapshot = q.items;snapshot[0].text = 'changed again'
        self.assertEqual(q.items[0].text, 'Failure')
        for n in [ui.Notice('', 'Invalid'), ui.Notice('bad', severity='bad'),ui.Notice('error', actions=[ui.NoticeAction('same'),ui.NoticeAction('same')])]:
            with self.assertRaises(ValueError):q.push(n)
        self.assertEqual(len(q.items), 1)
        q.push(ui.Notice('info', 'Short', expires_at=5))
        for width in range(80):
            for height in range(6):
                rows = q.layout(width, height)
                self.assertLessEqual(len(rows),height)
                for row in rows:
                    self.assertLessEqual(ui.cells(row.text),width)
                    for span in row.spans:
                        self.assertLessEqual(span.start+span.width,width)
                        self.assertEqual(ui.cells(span.text),span.width)
        q.focused = 'info';rows = q.layout(80,5)
        disabled = next(s for s in rows[0].spans if s.disabled)
        self.assertEqual(q.click(disabled.start,0).kind,'');self.assertEqual(q.focused,'info')
        enabled = next(s for s in rows[0].spans if not s.disabled)
        self.assertEqual(q.click(enabled.start,0).action,'retry');self.assertEqual(len(q.items),2)
        self.assertEqual(q.click(1,1,100).kind,'')
        q.push(ui.Notice('third','Third'))
        self.assertEqual(q.layout(10,2)[-1].text,'+2')
        self.assertEqual(len(q.layout(10,1)),1)

    def test_progress_states_spinners_and_palettes(self):
        for s in F['progress']:
            p = ui.Progress(**{k:v for k,v in s.items() if k not in ('cancel','role','contains')})
            rows = p.layout(40)
            self.assertEqual(bool(p.request_cancel().kind),s['cancel'])
            self.assertEqual(rows[0].role,s['role']);self.assertIn(s['contains'],rows[1].text)
        p = ui.Progress('p',label='Job 한글',cancellable=True,cancel_label='Cancel')
        self.assertEqual(len({p.layout(40,i)[1].text for i in range(4)}),4)
        self.assertEqual(p.request_cancel().kind,'cancel');self.assertEqual(p.status,'loading')
        for kind,role in F['data_states'].items():self.assertEqual(ui.DataState(kind,'State','Detail').layout(10)[0].role,role)
        q = ui.NoticeQueue(3)
        for n in F['notice_items']:q.push(notice(n))
        for theme in ['dark','light','blackwhite']:
            for colors in ['8','16','256','truecolor']:
                for width in range(20):
                    c = ui.Canvas(width,12,ui.Palette(theme,colors))
                    q.draw(c,ui.Rect(0,0,width,4));p.draw(c,ui.Rect(0,4,width,4));ui.DataState('error','Error','Detail').draw(c,ui.Rect(0,8,width,4))
                    self.assertIsNone(c.cursor)
        for bad in [-1,2**53,float('nan'),True]:
            with self.assertRaises(ValueError):q.visible(bad)
            with self.assertRaises(ValueError):ui.Progress(current=bad).layout(10)

    def test_example_host_owns_approval_and_time(self):
        from tuivory._feedback_example import FeedbackDemo
        h=FeedbackDemo(True);c=ui.Canvas(72,18);h.draw(c,ui.Rect(1,1,70,15))
        h.queue.focused='info';h.draw(c,ui.Rect(1,1,70,15));row=h.queue.layout(h.notice_area.width,h.notice_area.height)[0]
        off=next(s for s in row.spans if s.disabled)
        h.pointer(h.notice_area.x+off.start,h.notice_area.y,0);self.assertEqual(h.queue.focused,'info')
        retry=next(s for s in row.spans if not s.disabled)
        h.pointer(h.notice_area.x+retry.start,h.notice_area.y,0);self.assertEqual(h.state.kind,'ready');self.assertIn('Retry accepted',[n.text for n in h.queue.items])
        h.handle('insert',text='t');self.assertEqual(h.now,10);self.assertNotIn('info',[n.id for n in h.queue.items])
        h.pointer(h.progress_area.x,h.progress_area.y+2,0);self.assertEqual(h.progress.status,'cancelled')
        h.draw(c,ui.Rect(1,1,70,15));self.assertIsNone(c.cursor);self.assertIn('Export cancelled','\n'.join(c.lines()))
        h.handle('delete');self.assertEqual(len(h.queue.items),1)
