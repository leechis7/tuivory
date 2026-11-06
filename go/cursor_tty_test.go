package tuivory_test

import (
	"bytes"
	ui "github.com/leechis7/tuivory/go"
	"testing"
)

type cursorTestTty struct {
	ui.Tty
	bytes.Buffer
	closed, stopped bool
}

func (t *cursorTestTty) Read(p []byte) (int, error)  { return t.Buffer.Read(p) }
func (t *cursorTestTty) Write(p []byte) (int, error) { return t.Buffer.Write(p) }
func (t *cursorTestTty) Close() error                { t.closed = true; return nil }
func (t *cursorTestTty) Stop() error                 { t.stopped = true; return nil }
func TestCursorTtyPreservesShapeAndBlinkAcrossWrites(t *testing.T) {
	source := []byte("한글\x1b[0 q\x1b[6 q\x1b[ q\x1b[?12l\x1b[?12h\x1b[?12;25h\x1b[?25;12l\x1b[12;5H\x1b[?2026h\x1b[31mQq\x1b[?25h")
	expected := []byte("한글\x1b[?25h\x1b[?25l\x1b[12;5H\x1b[?2026h\x1b[31mQq\x1b[?25h")
	for split := 0; split <= len(source); split++ {
		raw := &cursorTestTty{}
		tty := ui.PreserveCursorTty(raw)
		if ui.PreserveCursorTty(tty) != tty || ui.PreserveCursorTty(nil) != nil {
			t.Fatal("identity")
		}
		for _, part := range [][]byte{source[:split], source[split:]} {
			n, err := tty.Write(part)
			if n != len(part) || err != nil {
				t.Fatal(n, err)
			}
		}
		if err := tty.Stop(); err != nil {
			t.Fatal(err)
		}
		if err := tty.Close(); err != nil {
			t.Fatal(err)
		}
		if !bytes.Equal(raw.Bytes(), expected) || !raw.closed || !raw.stopped {
			t.Fatalf("split %d: %q", split, raw.Bytes())
		}
	}
}
