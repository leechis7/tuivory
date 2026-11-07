import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { EventEmitter } from "node:events";
import { InputDecoder, Terminal } from "../dist/index.js";
const cases = JSON.parse(
  readFileSync(
    new URL("../../design/terminal-input-cases.json", import.meta.url),
  ),
).cases;
for (const c of cases) {
  const d = new InputDecoder(),
    events = [];
  for (const chunk of c.chunks) {
    d.feed(Buffer.from(chunk, "hex"));
    let e;
    while ((e = d.next()) !== null) events.push(e);
  }
  if (c.flush_escape) {
    let e;
    while ((e = d.next(true)) !== null) events.push(e);
  }
  assert.deepEqual(events, c.events, c.name);
}
class Input extends EventEmitter {
  isTTY = true;
  isRaw = false;
  readableFlowing = null;
  raw = [];
  paused = 0;
  setRawMode(value) {
    this.isRaw = value;
    this.raw.push(value);
  }
  resume() {
    this.readableFlowing = true;
  }
  pause() {
    this.readableFlowing = false;
    this.paused++;
  }
}
class Output extends EventEmitter {
  isTTY = true;
  columns = 80;
  rows = 24;
  written = "";
  write(value) {
    this.written += value;
  }
}
{
  const stdin = new Input(),
    stdout = new Output(),
    external = () => {};
  stdin.on("data", external);
  const t = new Terminal({ io: { stdin, stdout }, mouseMotion: true }).open();
  assert.deepEqual(stdin.raw, [true]);
  assert.ok(stdout.written.includes("\x1b[?1002h"));
  stdin.emit("data", Buffer.from("한"));
  assert.equal((await t.read(0)).text, "한");
  stdout.columns = 40;
  stdout.rows = 18;
  stdout.emit("resize");
  assert.deepEqual(await t.read(0), {
    key: "resize",
    text: "",
    x: 40,
    y: 18,
    button: 0,
  });
  assert.equal(await t.read(1), null);
  const pending = t.read(10000);
  await assert.rejects(t.read(1), /one terminal read/);
  t.close();
  assert.equal((await pending).key, "eof");
  assert.deepEqual(stdin.raw, [true, false]);
  assert.equal(stdin.paused, 1);
  assert.equal(stdin.listenerCount("data"), 1);
  assert.equal(stdout.listenerCount("resize"), 0);
  assert.ok(
    stdout.written.includes("\x1b[?1002l") &&
      stdout.written.includes("\x1b[?2004l"),
  );
  t.close();
  assert.throws(() => t.open(), /reopened/);
}
{
  const stdin = new Input(),
    stdout = new Output();
  stdin.isRaw = true;
  stdin.readableFlowing = true;
  const t = new Terminal({ io: { stdin, stdout }, mouse: false }).open();
  stdin.emit("end");
  assert.equal((await t.read(0)).key, "eof");
  t.close();
  assert.deepEqual(stdin.raw, [true, true]);
  assert.equal(stdin.paused, 0);
}
{
  const stdin = new Input(),
    stdout = new Output();
  const write = stdout.write.bind(stdout);
  let fail = true;
  stdout.write = (value) => {
    if (fail) {
      fail = false;
      throw Error("write failed");
    }
    write(value);
  };
  assert.throws(
    () => new Terminal({ io: { stdin, stdout } }).open(),
    /write failed/,
  );
  assert.deepEqual(stdin.raw, [true, false]);
  assert.equal(stdin.listenerCount("data"), 0);
  assert.ok(stdout.written.includes("\x1b[?1049l"));
}
{
  const d = new InputDecoder();
  d.feed(Buffer.from([255]));
  assert.equal(d.next().text, "\ufffd");
  d.feed("\x1b[<0;0;2M");
  assert.equal(d.next().key, "unknown");
  d.feed("\x1b[200~" + "a".repeat(16 * 1024 * 1024 + 1) + "\x1b[201~");
  assert.equal(d.next().key, "paste_rejected");
}
console.log(
  "Terminal shared input, structural I/O, read cancellation, raw/flow/listener restoration and partial-open cleanup passed",
);
