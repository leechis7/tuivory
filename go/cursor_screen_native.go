//go:build aix || darwin || dragonfly || freebsd || linux || netbsd || openbsd || solaris || zos || plan9 || windows

package tuivory

import (
	"os"
	"runtime"
)

// NewCursorScreen creates a terminfo screen that preserves terminal cursor
// shape/blink settings. Connect it with Application.SetScreen before Run.
// Like NewScreen, this does not initialize the screen. Requires a usable TTY.
func NewCursorScreen() (Screen, error) {
	tty, err := NewDevTty()
	if err != nil {
		return nil, err
	}
	tty = PreserveCursorTty(tty)
	var screen Screen
	if runtime.GOOS == "windows" && os.Getenv("TERM") == "" {
		ti, e := LookupTerminfo("xterm-256color")
		if e != nil {
			_ = tty.Close()
			return nil, e
		}
		screen, err = NewTerminfoScreenFromTtyTerminfo(tty, ti)
	} else {
		screen, err = NewTerminfoScreenFromTty(tty)
	}
	if err != nil {
		_ = tty.Close()
	}
	return screen, err
}
