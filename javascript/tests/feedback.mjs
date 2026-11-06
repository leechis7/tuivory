import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import * as ui from "../dist/index.js";
const f = JSON.parse(
  readFileSync(new URL("../../design/feedback-cases.json", import.meta.url)),
);
const notice = (n) => {
  const result = structuredClone(n);
  if ("expires_at" in result) {
    result.expiresAt = result.expires_at;
    delete result.expires_at;
  }
  return result;
};
{
  const q = new ui.NoticeQueue(3);
  for (const n of f.notice_items) q.push(notice(n));
  for (const s of f.notice_steps) {
    switch (s.operation) {
      case "visible":
        assert.deepEqual(
          q.visible(s.now).map((n) => n.id),
          s.ids,
        );
        break;
      case "handle":
        assert.deepEqual(q.handle(s.action, s.now, s.height), s.event);
        break;
      case "expire":
        assert.deepEqual(
          q.expire(s.now).map((n) => n.id),
          s.ids,
        );
        break;
      case "dismiss":
        assert.equal(q.dismiss(s.id), s.result);
        break;
    }
  }
  for (const s of f.evictions) {
    const q = new ui.NoticeQueue(s.capacity);
    for (const n of s.initial) q.push(notice(n));
    if (s.accepted) q.push(notice(s.incoming));
    else assert.throws(() => q.push(notice(s.incoming)));
    assert.deepEqual(
      q.visible().map((n) => n.id),
      s.ids,
    );
  }
}
{
  const q = new ui.NoticeQueue(3),
    n = notice(f.notice_items[2]);
  q.push(n);
  n.text = "changed";
  n.actions[0].disabled = false;
  assert.equal(q.visible()[0].text, "Failure");
  const snapshot = q.items;
  snapshot[0].text = "changed again";
  assert.equal(q.items[0].text, "Failure");
  for (const n of [
    { id: "" },
    { id: "bad", severity: "bad" },
    { id: "error", actions: [{ id: "same" }, { id: "same" }] },
  ])
    assert.throws(() => q.push(n));
  assert.equal(q.items.length, 1);
  q.push({ id: "info", text: "Short", expiresAt: 5 });
  for (let width = 0; width < 80; width++)
    for (let height = 0; height < 6; height++) {
      const rows = q.layout(width, height);
      assert.ok(rows.length <= height);
      for (const row of rows) {
        assert.ok(ui.cells(row.text) <= width);
        for (const s of row.spans) {
          assert.ok(s.start + s.width <= width);
          assert.equal(ui.cells(s.text), s.width);
        }
      }
    }
  q.focused = "info";
  q.layout(80, 5);
  for (const x of [NaN, 0.5, -1, Infinity]) {
    assert.equal(q.click(x, 0).kind, "");
    assert.equal(q.focused, "info");
  }
  const rows = q.layout(80, 5),
    disabled = rows[0].spans.find((s) => s.disabled),
    enabled = rows[0].spans.find((s) => !s.disabled);
  assert.equal(q.click(disabled.start, 0).kind, "");
  assert.equal(q.focused, "info");
  assert.equal(q.click(enabled.start, 0).action, "retry");
  assert.equal(q.items.length, 2);
  assert.equal(q.click(1, 1, 100).kind, "");
  q.push({ id: "third", text: "Third" });
  assert.equal(q.layout(10, 2).at(-1).text, "+2");
  assert.equal(q.layout(10, 1).length, 1);
}
{
  for (const s of f.progress) {
    const { cancel, role, contains, ...options } = s,
      p = new ui.Progress(options),
      rows = p.layout(40);
    assert.equal(Boolean(p.requestCancel().kind), cancel);
    assert.equal(rows[0].role, role);
    assert.ok(rows[1].text.includes(contains));
  }
  const p = new ui.Progress({
    id: "p",
    label: "Job 한글",
    cancellable: true,
    cancelLabel: "Cancel",
  });
  assert.equal(
    new Set([0, 1, 2, 3].map((i) => p.layout(40, i)[1].text)).size,
    4,
  );
  assert.equal(p.requestCancel().kind, "cancel");
  assert.equal(p.status, "loading");
  for (const [kind, role] of Object.entries(f.data_states))
    assert.equal(
      new ui.DataState(kind, "State", "Detail").layout(10)[0].role,
      role,
    );
  const q = new ui.NoticeQueue(3);
  for (const n of f.notice_items) q.push(notice(n));
  for (const theme of ["dark", "light", "blackwhite"])
    for (const colors of ["8", "16", "256", "truecolor"])
      for (let w = 0; w < 20; w++) {
        const c = new ui.Canvas(w, 12, new ui.Palette(theme, colors));
        q.draw(c, ui.rect(0, 0, w, 4));
        p.draw(c, ui.rect(0, 4, w, 4));
        new ui.DataState("error", "Error", "Detail").draw(
          c,
          ui.rect(0, 8, w, 4),
        );
        assert.equal(c.cursor, null);
      }
  for (const bad of [-1, 2 ** 53, NaN, Infinity, 0.5]) {
    assert.throws(() => q.push({ id: "invalid", expiresAt: bad }));
    assert.equal(q.items.length, 3);
    assert.throws(() => q.visible(bad));
    assert.throws(() => new ui.Progress({ current: bad }).layout(10));
  }
}
console.log(
  "Feedback shared lifetimes, capacity retention, host-approved requests, action clipping and palette rendering passed",
);
const { FeedbackDemo } = await import("../examples/feedback-host.mjs");
{
  const h = new FeedbackDemo(true),
    c = new ui.Canvas(72, 18);
  h.draw(c, ui.rect(1, 1, 70, 15), false);
  h.queue.focused = "info";
  h.draw(c, ui.rect(1, 1, 70, 15), false);
  const row = h.queue.layout(h.noticeArea.width, h.noticeArea.height)[0],
    off = row.spans.find((s) => s.disabled),
    retry = row.spans.find((s) => !s.disabled);
  h.pointer(h.noticeArea.x + off.start, h.noticeArea.y, 0);
  assert.equal(h.queue.focused, "info");
  h.pointer(h.noticeArea.x + retry.start, h.noticeArea.y, 0);
  assert.equal(h.state.kind, "ready");
  assert.ok(h.queue.items.some((n) => n.text === "Retry accepted"));
  h.handle("insert", "t");
  assert.equal(h.now, 10);
  assert.ok(!h.queue.items.some((n) => n.id === "info"));
  h.pointer(h.progressArea.x, h.progressArea.y + 2, 0);
  assert.equal(h.progress.status, "cancelled");
  h.draw(c, ui.rect(1, 1, 70, 15), false);
  assert.equal(c.cursor, null);
  assert.ok(c.lines().join("\n").includes("Export cancelled"));
  h.handle("delete");
  assert.equal(h.queue.items.length, 1);
}
