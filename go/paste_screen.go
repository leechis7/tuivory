package tuivory

import "github.com/gdamore/tcell/v2"

// PasteSafeScreen preserves LF/CRLF pasted through the compatibility Application.
// Its backend collects only Enter keys while pasting; raw LF arrives as Ctrl+J.
// Wrap the screen before Application.SetScreen/Run. Outside bracketed paste,
// Ctrl+J and every other event retain their original identity.
func PasteSafeScreen(screen Screen) Screen {
	if screen == nil {
		return nil
	}
	if _, ok := screen.(*pasteSafeScreen); ok {
		return screen
	}
	return &pasteSafeScreen{Screen: screen}
}

type pasteSafeScreen struct {
	tcell.Screen
	pasting, afterCR bool
}

func (s *pasteSafeScreen) PollEvent() tcell.Event {
	for {
		e := s.Screen.PollEvent()
		if e == nil {
			s.pasting = false
			s.afterCR = false
			return nil
		}
		if p, ok := e.(*tcell.EventPaste); ok {
			s.pasting = p.Start()
			s.afterCR = false
			return e
		}
		if s.pasting {
			if k, ok := e.(*tcell.EventKey); ok {
				wasCR := s.afterCR
				s.afterCR = k.Key() == tcell.KeyEnter
				if k.Key() == tcell.KeyCtrlJ {
					if wasCR {
						continue
					}
					return tcell.NewEventKey(tcell.KeyEnter, 0, k.Modifiers())
				}
			} else {
				s.afterCR = false
			}
		}
		return e
	}
}
