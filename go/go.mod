module github.com/leechis7/tuivory/go

go 1.24.0

// Windows facade compilation fails in v0.10.1. Do not use; upgrade to v0.10.2 or later.
retract v0.10.1

require github.com/gdamore/tcell/v2 v2.13.10

require (
	github.com/gdamore/encoding v1.0.1 // indirect
	github.com/lucasb-eyer/go-colorful v1.3.0 // indirect
	github.com/rivo/tview v0.42.0
	github.com/rivo/uniseg v0.4.7
	golang.org/x/sys v0.38.0 // indirect
	golang.org/x/term v0.37.0 // indirect
	golang.org/x/text v0.31.0
)
