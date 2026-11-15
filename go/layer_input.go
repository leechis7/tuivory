package tuivory

import "slices"

// LayerRoute identifies a recipient of pointer input. An empty Target consumes
// the action. Action can be "click" when a backend double click crossed scopes.
type LayerRoute struct {
	Target, Action string
}

type layerPress struct {
	target string
	down   bool
}

// LayerInput enforces a front layer and retains ownership of pointer gestures.
// A host supplies stable layer IDs, hit tests, and an explicit pass-through
// decision for each pointer position. Its zero value has no front restriction.
type LayerInput struct {
	front     string
	press     map[int]layerPress
	lastClick map[int]string
}

// SetFront changes the input scope. Cancel gestures on each returned layer ID.
// Invalidate explicitly when replacing the contents of a layer with the same ID.
func (s *LayerInput) SetFront(id string) []string {
	if s.front == id {
		return nil
	}
	s.front = id
	return s.Invalidate()
}

// Invalidate cancels recorded presses and blocks their remaining move, up and
// click events. It does not change the current front layer.
func (s *LayerInput) Invalidate() []string {
	var cancelled []string
	buttons := make([]int, 0, len(s.press))
	for button := range s.press {
		buttons = append(buttons, button)
	}
	slices.Sort(buttons)
	for _, button := range buttons {
		press := s.press[button]
		if press.down && press.target != "" {
			if !slices.Contains(cancelled, press.target) {
				cancelled = append(cancelled, press.target)
			}
		}
		s.press[button] = layerPress{down: press.down}
	}
	clear(s.lastClick)
	return cancelled
}

// KeyboardTarget applies equally to keyboard and paste. No focus means that
// input is consumed. A pointer pass-through never grants keyboard access.
func (s *LayerInput) KeyboardTarget(focused string) string {
	if s.front != "" && focused != s.front {
		return ""
	}
	return focused
}

// Pointer routes down, move, up, click, double or wheel actions. Use a consistent
// button ID throughout each gesture (zero for buttonless move and wheel).
// Pass-through only affects hit testing; drag and release stay with the press.
func (s *LayerInput) Pointer(action string, button int, hit string, through bool) LayerRoute {
	if !through && s.front != "" && hit != s.front {
		hit = ""
	}
	result := LayerRoute{Action: action}
	press, seen := s.press[button]
	switch action {
	case "down":
		if s.press == nil {
			s.press = make(map[int]layerPress)
		}
		s.press[button] = layerPress{target: hit, down: true}
		result.Target = hit
	case "move":
		if !seen && button == 0 {
			// A backend that reports buttonless moves cannot disambiguate
			// simultaneous presses. Route only an unambiguous active gesture.
			for _, active := range s.press {
				if active.down {
					if seen {
						return result
					}
					press, seen = active, true
				}
			}
		}
		if seen && press.down {
			result.Target = press.target
		} else {
			result.Target = hit
		}
	case "up":
		if seen {
			press.down = false
			s.press[button] = press
			result.Target = press.target
		}
	case "click", "double":
		delete(s.press, button)
		if seen && !press.down && press.target == hit {
			result.Target = hit
		}
		if result.Target != "" {
			if action == "double" && s.lastClick[button] != result.Target {
				result.Action = "click"
			}
			if s.lastClick == nil {
				s.lastClick = make(map[int]string)
			}
			s.lastClick[button] = result.Target
		} else {
			delete(s.lastClick, button)
		}
	case "wheel":
		result.Target = hit
	}
	return result
}
