//go:build !(aix || darwin || dragonfly || freebsd || linux || netbsd || openbsd || solaris || zos || plan9 || windows)

package tuivory

import "fmt"

// NewCursorScreen requires a native TTY backend. Use the host's screen on other targets.
func NewCursorScreen() (Screen, error) {
	return nil, fmt.Errorf("cursor-preserving TTY screen is unavailable on this target")
}
