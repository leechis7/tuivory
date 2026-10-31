package terminal

import (
	"github.com/gdamore/tcell/v2/terminfo"
	"golang.org/x/text/encoding"
)

// Terminfo and Encoding keep optional screen/encoding setup SDK-import-only.
type Terminfo = terminfo.Terminfo
type Encoding = encoding.Encoding
