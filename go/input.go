package tuivory

import (
	"fmt"
	terminal "github.com/leechis7/tuivory/go/terminal"
	ui "github.com/leechis7/tuivory/go/ui"
	"strings"
)

// InputEvent is the language-neutral terminal input envelope. Positions are
// screen cells; text is original UTF-8. Modifiers use shift,ctrl,alt,meta order.
// Applications handle global keys before forwarding EditingAction to a model.
type InputEvent struct {
	Kind      string   `json:"kind"`
	Key       string   `json:"key,omitempty"`
	Text      string   `json:"text,omitempty"`
	Modifiers []string `json:"modifiers,omitempty"`
	Phase     string   `json:"phase,omitempty"`
	X         int      `json:"x,omitempty"`
	Y         int      `json:"y,omitempty"`
	Button    string   `json:"button,omitempty"`
	Width     int      `json:"width,omitempty"`
	Height    int      `json:"height,omitempty"`
}

func InputFromKey(e *terminal.EventKey) InputEvent {
	if e == nil {
		return InputEvent{}
	}
	key, text := "unknown", ""
	mod := e.Modifiers()
	switch e.Key() {
	case terminal.KeyRune:
		key = string(e.Rune())
		text = key
	case terminal.KeyCtrlSpace:
		key = " "
		mod |= terminal.ModCtrl
	case terminal.KeyTab:
		key = "tab"
	case terminal.KeyBacktab:
		key = "tab"
		mod |= terminal.ModShift
	case terminal.KeyEnter:
		key = "enter"
	case terminal.KeyEscape:
		key = "escape"
	case terminal.KeyBackspace, terminal.KeyBackspace2:
		key = "backspace"
	case terminal.KeyDelete:
		key = "delete"
	case terminal.KeyInsert:
		key = "insert"
	case terminal.KeyUp:
		key = "up"
	case terminal.KeyDown:
		key = "down"
	case terminal.KeyLeft:
		key = "left"
	case terminal.KeyRight:
		key = "right"
	case terminal.KeyHome:
		key = "home"
	case terminal.KeyEnd:
		key = "end"
	case terminal.KeyPgUp:
		key = "page_up"
	case terminal.KeyPgDn:
		key = "page_down"
	default:
		if e.Key() >= terminal.KeyCtrlA && e.Key() <= terminal.KeyCtrlZ {
			key = string(rune('a' + e.Key() - terminal.KeyCtrlA))
			mod |= terminal.ModCtrl
		}
		if e.Key() >= terminal.KeyF1 && e.Key() <= terminal.KeyF64 {
			key = fmt.Sprintf("f%d", e.Key()-terminal.KeyF1+1)
		}
	}
	if mod&terminal.ModCtrl != 0 {
		key = strings.ToLower(key)
		text = ""
	}
	return InputEvent{Kind: "key", Key: key, Text: text, Phase: "press", Modifiers: inputModifiers(mod)}
}
func inputModifiers(mod terminal.ModMask) []string {
	var out []string
	for _, m := range []struct {
		flag terminal.ModMask
		name string
	}{{terminal.ModShift, "shift"}, {terminal.ModCtrl, "ctrl"}, {terminal.ModAlt, "alt"}, {terminal.ModMeta, "meta"}} {
		if mod&m.flag != 0 {
			out = append(out, m.name)
		}
	}
	return out
}

func InputFromMouse(action ui.MouseAction, e *terminal.EventMouse) InputEvent {
	if e == nil {
		return InputEvent{}
	}
	x, y := e.Position()
	out := InputEvent{Kind: "pointer", X: x, Y: y, Button: "none"}
	switch action {
	case ui.MouseLeftDown:
		out.Phase = "down"
		out.Button = "left"
	case ui.MouseLeftUp:
		out.Phase = "up"
		out.Button = "left"
	case ui.MouseLeftClick:
		out.Phase = "click"
		out.Button = "left"
	case ui.MouseLeftDoubleClick:
		out.Phase = "double_click"
		out.Button = "left"
	case ui.MouseRightDown:
		out.Phase = "down"
		out.Button = "right"
	case ui.MouseRightUp:
		out.Phase = "up"
		out.Button = "right"
	case ui.MouseRightClick:
		out.Phase = "click"
		out.Button = "right"
	case ui.MouseRightDoubleClick:
		out.Phase = "double_click"
		out.Button = "right"
	case ui.MouseMiddleDown:
		out.Phase = "down"
		out.Button = "middle"
	case ui.MouseMiddleUp:
		out.Phase = "up"
		out.Button = "middle"
	case ui.MouseMiddleClick:
		out.Phase = "click"
		out.Button = "middle"
	case ui.MouseMiddleDoubleClick:
		out.Phase = "double_click"
		out.Button = "middle"
	case ui.MouseMove:
		out.Phase = "move"
		if e.Buttons()&terminal.Button1 != 0 {
			out.Phase = "drag"
			out.Button = "left"
		} else if e.Buttons()&terminal.ButtonSecondary != 0 {
			out.Phase = "drag"
			out.Button = "right"
		} else if e.Buttons()&terminal.ButtonMiddle != 0 {
			out.Phase = "drag"
			out.Button = "middle"
		}
	case ui.MouseScrollUp:
		out.Phase = "scroll_up"
	case ui.MouseScrollDown:
		out.Phase = "scroll_down"
	case ui.MouseScrollLeft:
		out.Phase = "scroll_left"
	case ui.MouseScrollRight:
		out.Phase = "scroll_right"
	default:
		out.Phase = "unknown"
	}
	out.Modifiers = inputModifiers(e.Modifiers())
	return out
}
func PasteInput(text string) InputEvent { return InputEvent{Kind: "paste", Text: text} }
func ResizeInput(width, height int) InputEvent {
	return InputEvent{Kind: "resize", Width: max(0, width), Height: max(0, height)}
}

// EditingAction returns a model action/request, never clipboard or business I/O.
// Enter inserts a newline; a form host can map enter to activate/submit instead.
func (e InputEvent) EditingAction() (string, string) {
	if e.Kind == "paste" {
		return "paste", e.Text
	}
	if e.Kind != "key" || e.Phase == "release" {
		return "", ""
	}
	has := func(name string) bool {
		for _, m := range e.Modifiers {
			if m == name {
				return true
			}
		}
		return false
	}
	if has("ctrl") {
		action := map[string]string{"a": "select_all", "c": "copy", "x": "cut", "z": "undo", "y": "redo"}[strings.ToLower(e.Key)]
		return action, ""
	}
	action := map[string]string{"enter": "newline", "backspace": "backspace", "delete": "delete", "left": "left", "right": "right", "up": "up", "down": "down", "home": "home", "end": "end", "page_up": "page_up", "page_down": "page_down"}[e.Key]
	if has("alt") && (action == "left" || action == "right") {
		return "scroll_" + action, ""
	}
	if has("shift") && (action == "left" || action == "right" || action == "up" || action == "down" || action == "home" || action == "end") {
		action = "select_" + action
	}
	if action != "" {
		return action, ""
	}
	if e.Text != "" {
		return "insert", e.Text
	}
	return "", ""
}
