package tuivory

import (
	"bytes"
	"io"
	"strings"
	"sync"
)

// PreserveCursorTty filters backend cursor-shape and blink changes, including
// default DECSCUSR and terminfo ?12h/l. Position and visibility remain intact.
// Use NewCursorScreen for a ready-to-use screen; no terminal settings are forced.
func PreserveCursorTty(tty Tty) Tty {
	if tty == nil {
		return nil
	}
	if _, ok := tty.(*cursorTty); ok {
		return tty
	}
	return &cursorTty{Tty: tty}
}

type cursorTty struct {
	Tty
	mu      sync.Mutex
	pending []byte
}

func (t *cursorTty) Write(p []byte) (int, error) {
	t.mu.Lock()
	defer t.mu.Unlock()
	data := append(t.pending, p...)
	t.pending = nil
	var out bytes.Buffer
	for len(data) > 0 {
		if data[0] != 0x1b {
			out.WriteByte(data[0])
			data = data[1:]
			continue
		}
		if len(data) < 2 {
			t.pending = append([]byte(nil), data...)
			break
		}
		if data[1] != '[' {
			out.Write(data[:2])
			data = data[2:]
			continue
		}
		end := 2
		for end < len(data) && data[end] >= 0x20 && data[end] <= 0x3f {
			end++
		}
		if end == len(data) && end < 1024 {
			t.pending = append([]byte(nil), data...)
			break
		}
		if end == len(data) || data[end] < 0x40 || data[end] > 0x7e {
			out.Write(data[:2])
			data = data[2:]
			continue
		}
		params := string(data[2:end])
		final := data[end]
		seq := data[:end+1]
		data = data[end+1:]
		if final == 'q' && strings.HasSuffix(params, " ") {
			continue
		}
		if (final == 'h' || final == 'l') && strings.HasPrefix(params, "?") {
			parts := strings.Split(params[1:], ";")
			keep := parts[:0]
			for _, v := range parts {
				if strings.TrimLeft(v, "0") != "12" {
					keep = append(keep, v)
				}
			}
			if len(keep) != len(parts) {
				if len(keep) > 0 {
					out.WriteString("\x1b[?" + strings.Join(keep, ";") + string(final))
				}
				continue
			}
		}
		out.Write(seq)
	}
	err := t.writeAll(out.Bytes())
	return len(p), err
}
func (t *cursorTty) writeAll(p []byte) error {
	for len(p) > 0 {
		n, err := t.Tty.Write(p)
		if err != nil {
			return err
		}
		if n <= 0 || n > len(p) {
			return io.ErrShortWrite
		}
		p = p[n:]
	}
	return nil
}
func (t *cursorTty) flush() error { p := t.pending; t.pending = nil; return t.writeAll(p) }
func (t *cursorTty) Stop() error {
	t.mu.Lock()
	defer t.mu.Unlock()
	err := t.flush()
	stop := t.Tty.Stop()
	if err != nil {
		return err
	}
	return stop
}
func (t *cursorTty) Close() error {
	t.mu.Lock()
	defer t.mu.Unlock()
	err := t.flush()
	closeErr := t.Tty.Close()
	if err != nil {
		return err
	}
	return closeErr
}
