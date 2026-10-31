//go:build aix || darwin || dragonfly || freebsd || linux || netbsd || openbsd || solaris || zos

package terminal

import native "github.com/gdamore/tcell/v2"

// NewDevTtyFromDev preserves the backend's Unix-only device selection API.
func NewDevTtyFromDev(device string) (Tty, error) { return native.NewDevTtyFromDev(device) }
