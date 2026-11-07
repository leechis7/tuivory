/** Optional Node-compatible terminal I/O; models do not require Node typings. */
export interface InputEvent {
  key: string;
  text: string;
  x: number;
  y: number;
  button: number;
}
const input = (
  key: string,
  text = "",
  x = 0,
  y = 0,
  button = 0,
): InputEvent => ({ key, text, x, y, button });
const keys: Readonly<Record<string, string>> = {
  "\x1b[A": "up",
  "\x1b[B": "down",
  "\x1b[C": "right",
  "\x1b[D": "left",
  "\x1b[H": "home",
  "\x1b[F": "end",
  "\x1b[5~": "page_up",
  "\x1b[6~": "page_down",
  "\x1b[3~": "delete",
  "\x1b[Z": "shift_tab",
  "\x1bOP": "f1",
  "\x1bOQ": "f2",
  "\x1b[21~": "f10",
  "\x1b[21;2~": "shift_f10",
};
/** Incremental UTF-8/escape parser, independent of the actual terminal session. */
export class InputDecoder {
  private buffer = "";
  private bytes = new Uint8Array();
  private paste: string | null = null;
  private pasteBytes = 0;
  private rejected = false;
  feed(chunk: string | Uint8Array): void {
    if (typeof chunk === "string") this.buffer += chunk;
    else {
      const values = new Uint8Array(this.bytes.length + chunk.length);
      values.set(this.bytes);
      values.set(chunk, this.bytes.length);
      this.bytes = new Uint8Array();
      for (let i = 0; i < values.length;) {
        const first = values[i],
          n =
            first < 128
              ? 1
              : first >= 0xc2 && first <= 0xdf
                ? 2
                : first >= 0xe0 && first <= 0xef
                  ? 3
                  : first >= 0xf0 && first <= 0xf4
                    ? 4
                    : 0;
        if (!n) {
          this.buffer += "\ufffd";
          i++;
          continue;
        }
        if (i + n > values.length) {
          this.bytes = values.slice(i);
          break;
        }
        let cp = first & (n === 1 ? 127 : n === 2 ? 31 : n === 3 ? 15 : 7),
          valid = true;
        for (let j = 1; j < n; j++) {
          const b = values[i + j];
          if ((b & 0xc0) !== 0x80) {
            valid = false;
            break;
          }
          cp = (cp << 6) | (b & 63);
        }
        if (
          !valid ||
          cp > 0x10ffff ||
          (cp >= 0xd800 && cp <= 0xdfff) ||
          (n === 2 && cp < 128) ||
          (n === 3 && cp < 2048) ||
          (n === 4 && cp < 65536)
        ) {
          this.buffer += "\ufffd";
          i++;
          continue;
        }
        this.buffer += String.fromCodePoint(cp);
        i += n;
      }
    }
    if (this.buffer.length > 16 * 1024 * 1024 + 64) {
      this.buffer = "";
      this.bytes = new Uint8Array();
      this.paste = null;
      this.pasteBytes = 0;
      this.rejected = true;
    }
  }
  get waitingEscape(): boolean {
    return this.paste === null && this.buffer.startsWith("\x1b");
  }
  next(flushEscape = false): InputEvent | null {
    if (this.rejected) {
      this.rejected = false;
      return input("paste_rejected");
    }
    if (this.paste !== null) {
      const end = this.buffer.indexOf("\x1b[201~");
      const count = end < 0 ? Math.max(0, this.buffer.length - 5) : end;
      const part = this.buffer.slice(0, count);
      for (const char of part) {
        const cp = char.codePointAt(0)!;
        this.pasteBytes += cp < 128 ? 1 : cp < 2048 ? 2 : cp < 65536 ? 3 : 4;
      }
      if (this.pasteBytes > 16 * 1024 * 1024) {
        this.buffer = "";
        this.paste = null;
        this.pasteBytes = 0;
        return input("paste_rejected");
      }
      this.paste += part;
      this.buffer = this.buffer.slice(count);
      if (end < 0) return null;
      const value = this.paste;
      this.paste = null;
      this.pasteBytes = 0;
      this.buffer = this.buffer.slice(6);
      return input("paste", value);
    }
    if (!this.buffer) return null;
    if (this.buffer.startsWith("\x1b[200~")) {
      this.buffer = this.buffer.slice(6);
      this.paste = "";
      this.pasteBytes = 0;
      return this.next(flushEscape);
    }
    const mouse = this.buffer.match(/^\x1b\[<(\d+);(\d+);(\d+)([Mm])/);
    if (mouse) {
      this.buffer = this.buffer.slice(mouse[0].length);
      const b = Number(mouse[1]),
        x = Number(mouse[2]) - 1,
        y = Number(mouse[3]) - 1;
      if (
        ![b, x, y].every(
          (n) => Number.isSafeInteger(n) && n >= 0 && n <= 1000000000,
        )
      )
        return input("unknown");
      return input(
        mouse[4] === "m"
          ? "mouse_release"
          : b & 64
            ? "wheel"
            : b & 32
              ? "mouse_move"
              : "mouse",
        "",
        x,
        y,
        b,
      );
    }
    for (const [seq, key] of Object.entries(keys))
      if (this.buffer.startsWith(seq)) {
        this.buffer = this.buffer.slice(seq.length);
        return input(key);
      }
    if (this.buffer[0] === "\x1b") {
      if (
        !flushEscape &&
        (Object.keys(keys).some((s) => s.startsWith(this.buffer)) ||
          "\x1b[200~".startsWith(this.buffer) ||
          (this.buffer.startsWith("\x1b[<") && !/[Mm]/.test(this.buffer)))
      )
        return null;
      const csi = this.buffer.match(/^\x1b\[[0-?]*[ -/]*[@-~]/);
      if (csi) {
        this.buffer = this.buffer.slice(csi[0].length);
        return input("unknown");
      }
      this.buffer = this.buffer.slice(1);
      return input("escape");
    }
    const cp = this.buffer.codePointAt(0)!,
      c = String.fromCodePoint(cp);
    this.buffer = this.buffer.slice(c.length);
    if (cp < 32 || cp === 127)
      return input(
        (
          {
            9: "tab",
            10: "enter",
            13: "enter",
            8: "backspace",
            127: "backspace",
          } as Record<number, string>
        )[cp] ?? "ctrl_" + String.fromCharCode(cp + 96),
      );
    return input("text", c);
  }
}
export interface TerminalInput {
  isTTY?: boolean;
  isRaw?: boolean;
  readableFlowing?: boolean | null;
  setRawMode(enabled: boolean): unknown;
  resume(): unknown;
  pause(): unknown;
  isPaused?(): boolean;
  on(event: string, listener: (...args: unknown[]) => void): unknown;
  removeListener(
    event: string,
    listener: (...args: unknown[]) => void,
  ): unknown;
}
export interface TerminalOutput {
  isTTY?: boolean;
  columns?: number;
  rows?: number;
  write(value: string): unknown;
  on(event: string, listener: (...args: unknown[]) => void): unknown;
  removeListener(
    event: string,
    listener: (...args: unknown[]) => void,
  ): unknown;
}
export interface TerminalIO {
  stdin: TerminalInput;
  stdout: TerminalOutput;
}
export interface TerminalOptions {
  mouse?: boolean;
  mouseMotion?: boolean;
  io?: TerminalIO;
}
const timers = globalThis as unknown as {
  setTimeout(callback: () => void, ms: number): unknown;
  clearTimeout(id: unknown): void;
};
/** Explicit open/read/close lifecycle. Hosts own signals, global keys and focus. */
export class Terminal {
  private io: TerminalIO;
  private decoder = new InputDecoder();
  private reading = false;
  private active = false;
  private closed = false;
  private raw = false;
  private paused = false;
  private ended = false;
  private escapeAt = 0;
  private resized = false;
  private waiter: (() => void) | null = null;
  private readonly mouse: boolean;
  private readonly motion: boolean;
  private data = (chunk: unknown): void => {
    if (typeof chunk === "string" || chunk instanceof Uint8Array) {
      if (!this.escapeAt) this.escapeAt = Date.now();
      this.decoder.feed(chunk);
      this.waiter?.();
    }
  };
  private end = (): void => {
    this.ended = true;
    this.waiter?.();
  };
  private resize = (): void => {
    this.resized = true;
    this.waiter?.();
  };
  constructor(options: TerminalOptions = {}) {
    const runtime = globalThis as unknown as { process?: TerminalIO };
    const io = options.io ?? runtime.process;
    if (!io) throw new Error("Terminal requires Node-compatible TTY streams");
    this.io = io;
    this.mouse = options.mouse ?? true;
    this.motion = options.mouseMotion ?? false;
  }
  get size(): readonly [number, number] {
    return [this.io.stdout.columns || 80, this.io.stdout.rows || 24];
  }
  open(): this {
    if (this.active || this.closed)
      throw new Error("Terminal session cannot be reopened");
    if (!this.io.stdin.isTTY || !this.io.stdout.isTTY)
      throw new Error("interactive Terminal requires a TTY");
    this.raw = !!this.io.stdin.isRaw;
    this.paused = this.io.stdin.readableFlowing !== true;
    this.active = true;
    try {
      this.io.stdin.setRawMode(true);
      this.io.stdin.on("data", this.data);
      this.io.stdin.on("end", this.end);
      this.io.stdin.on("error", this.end);
      this.io.stdout.on("resize", this.resize);
      this.io.stdin.resume();
      this.write(
        "\x1b[?1049h\x1b[?2004h" +
          (this.mouse
            ? (this.motion ? "\x1b[?1002h" : "\x1b[?1000h") + "\x1b[?1006h"
            : ""),
      );
    } catch (error) {
      this.close();
      throw error;
    }
    return this;
  }
  write(value: string): void {
    if (!this.active) throw new Error("Terminal is closed");
    this.io.stdout.write(value);
  }
  close(): void {
    if (!this.active) return;
    this.active = false;
    this.closed = true;
    try {
      this.io.stdout.write(
        "\x1b[0m\x1b[?1000l\x1b[?1002l\x1b[?1006l\x1b[?2004l\x1b[?25h\x1b[?1049l",
      );
    } finally {
      this.io.stdin.removeListener("data", this.data);
      this.io.stdin.removeListener("end", this.end);
      this.io.stdin.removeListener("error", this.end);
      this.io.stdout.removeListener("resize", this.resize);
      try {
        this.io.stdin.setRawMode(this.raw);
      } finally {
        if (this.paused) this.io.stdin.pause();
        this.waiter?.();
      }
    }
  }
  async read(timeout = 100): Promise<InputEvent | null> {
    if (!Number.isFinite(timeout) || timeout < 0 || timeout > 3600000)
      throw new Error("invalid terminal timeout");
    if (!this.active) return input("eof");
    if (this.reading) throw new Error("only one terminal read may be pending");
    this.reading = true;
    try {
      const take = (): InputEvent | null => {
        if (!this.active) return input("eof");
        if (this.resized) {
          this.resized = false;
          const [x, y] = this.size;
          return input("resize", "", x, y);
        }
        const event = this.decoder.next(
          this.decoder.waitingEscape && Date.now() - this.escapeAt >= 100,
        );
        if (event) {
          this.escapeAt = this.decoder.waitingEscape ? Date.now() : 0;
          return event;
        }
        return this.ended ? input("eof") : null;
      };
      const ready = take();
      if (ready || timeout === 0) return ready;
      await new Promise<void>((resolve) => {
        let timer: unknown;
        const done = () => {
          if (timer !== undefined) timers.clearTimeout(timer);
          this.waiter = null;
          resolve();
        };
        this.waiter = done;
        timer = timers.setTimeout(
          done,
          Math.min(
            timeout,
            this.decoder.waitingEscape
              ? Math.max(1, 100 - (Date.now() - this.escapeAt))
              : timeout,
          ),
        );
      });
      return take();
    } finally {
      this.reading = false;
    }
  }
}
