package tuivory

import (
	"fmt"

	"github.com/gdamore/tcell/v2"
)

// ControlState describes independent host-owned states. Read-only and busy
// controls remain focusable so their contents and status can be inspected.
type ControlState struct {
	Disabled bool `json:"disabled"`
	ReadOnly bool `json:"read_only"`
	Busy     bool `json:"busy"`
	Selected bool `json:"selected"`
	Edited   bool `json:"edited"`
	Invalid  bool `json:"invalid"`
}

type ControlVisual struct {
	Role, Markers                    string
	Focusable, Activatable, Editable bool
}

// Visual preserves every state marker even when a higher-priority color wins.
func (s ControlState) Visual() ControlVisual {
	v := ControlVisual{Role: "body", Focusable: !s.Disabled,
		Activatable: !s.Disabled && !s.Busy, Editable: !s.Disabled && !s.Busy && !s.ReadOnly}
	switch {
	case s.Disabled:
		v.Role = "disabled"
	case s.Invalid:
		v.Role = "error"
	case s.Selected:
		v.Role = "selection"
	case s.Edited:
		v.Role = "edited"
	}
	for _, m := range []struct {
		on   bool
		text string
	}{
		{s.Disabled, "-"}, {s.Invalid, "!"}, {s.Selected, ">"},
		{s.Edited, "*"}, {s.Busy, "~"}, {s.ReadOnly, "="},
	} {
		if m.on {
			v.Markers += m.text
		}
	}
	return v
}

// ControlStyle resolves shared roles without replacing the host's data or focus.
// Draw Visual().Markers separately; color is not the sole state indication.
func ControlStyle(palette Palette, state ControlState, focused bool) (tcell.Style, error) {
	v := state.Visual()
	pair, ok := palette[v.Role]
	if !ok {
		return tcell.StyleDefault, fmt.Errorf("missing control role %q", v.Role)
	}
	return pair.Style().Underline(focused && v.Focusable), nil
}

type FocusTarget struct {
	ID     string       `json:"id"`
	State  ControlState `json:"state"`
	Hidden bool         `json:"hidden"`
}

type focusScope struct {
	id, focused, restore string
	targets              []FocusTarget
	dismissible          bool
}

func targetsCopy(targets []FocusTarget) ([]FocusTarget, error) {
	seen := map[string]bool{}
	for _, target := range targets {
		if target.ID == "" || seen[target.ID] {
			return nil, fmt.Errorf("empty or duplicate focus target %q", target.ID)
		}
		seen[target.ID] = true
	}
	return append([]FocusTarget(nil), targets...), nil
}

func (s *focusScope) focus(id string) bool {
	for _, target := range s.targets {
		if target.ID == id && !target.Hidden && !target.State.Disabled {
			s.focused = id
			return true
		}
	}
	return false
}

func (s *focusScope) reconcile() {
	if s.focus(s.focused) {
		return
	}
	s.focused = ""
	for _, target := range s.targets {
		if !target.Hidden && !target.State.Disabled {
			s.focused = target.ID
			return
		}
	}
}

// FocusStack is host-owned state for a root scope and modal popup scopes.
// It owns neither framework widgets nor a terminal/event loop. The zero value
// must be initialized with NewFocusStack before use.
type FocusStack struct{ scopes []focusScope }

func NewFocusStack(rootID string, targets []FocusTarget) (*FocusStack, error) {
	if rootID == "" {
		return nil, fmt.Errorf("empty root scope")
	}
	copy, err := targetsCopy(targets)
	if err != nil {
		return nil, err
	}
	s := &FocusStack{scopes: []focusScope{{id: rootID, targets: copy}}}
	s.scopes[0].reconcile()
	return s, nil
}

func (s *FocusStack) top() *focusScope {
	if len(s.scopes) == 0 {
		return nil
	}
	return &s.scopes[len(s.scopes)-1]
}

func (s *FocusStack) ScopeID() string {
	if top := s.top(); top != nil {
		return top.id
	}
	return ""
}
func (s *FocusStack) Focused() string {
	if top := s.top(); top != nil {
		return top.focused
	}
	return ""
}
func (s *FocusStack) Depth() int {
	if len(s.scopes) == 0 {
		return 0
	}
	return len(s.scopes) - 1
}
func (s *FocusStack) Targets() []FocusTarget {
	if top := s.top(); top != nil {
		return append([]FocusTarget(nil), top.targets...)
	}
	return nil
}

// Focus affects only the active scope, including for mouse input.
func (s *FocusStack) Focus(id string) bool {
	if top := s.top(); top != nil {
		return top.focus(id)
	}
	return false
}

func (s *FocusStack) Move(backwards bool) string {
	top := s.top()
	if top == nil {
		return ""
	}
	ids := []string{}
	current := -1
	for _, target := range top.targets {
		if target.Hidden || target.State.Disabled {
			continue
		}
		if target.ID == top.focused {
			current = len(ids)
		}
		ids = append(ids, target.ID)
	}
	if len(ids) == 0 {
		top.focused = ""
		return ""
	}
	if backwards {
		if current < 0 {
			current = 0
		}
		current = (current + len(ids) - 1) % len(ids)
	} else {
		current = (current + 1) % len(ids)
	}
	top.focused = ids[current]
	return top.focused
}

// Update reconciles IDs after host data changes. Invalid updates are atomic.
func (s *FocusStack) Update(scopeID string, targets []FocusTarget) error {
	copy, err := targetsCopy(targets)
	if err != nil {
		return err
	}
	for i := range s.scopes {
		if s.scopes[i].id == scopeID {
			s.scopes[i].targets = copy
			s.scopes[i].reconcile()
			return nil
		}
	}
	return fmt.Errorf("unknown focus scope %q", scopeID)
}

// Open captures the parent focus. Empty scopes still block background input.
func (s *FocusStack) Open(id string, targets []FocusTarget, initial string, dismissible bool) error {
	if s.top() == nil || id == "" || len(s.scopes) >= 65 {
		return fmt.Errorf("invalid popup scope or depth")
	}
	for _, scope := range s.scopes {
		if scope.id == id {
			return fmt.Errorf("duplicate focus scope %q", id)
		}
	}
	copy, err := targetsCopy(targets)
	if err != nil {
		return err
	}
	next := focusScope{id: id, targets: copy, restore: s.Focused(), dismissible: dismissible}
	next.reconcile()
	if initial != "" && !next.focus(initial) {
		return fmt.Errorf("initial target %q is not focusable", initial)
	}
	s.scopes = append(s.scopes, next)
	return nil
}

type PopupCloseRequest struct{ ID, Reason string }

// RequestClose handles Escape without changing the stack. The host must approve
// and call Close; outside pointer input is only blocked, never auto-dismissed.
func (s *FocusStack) RequestClose() *PopupCloseRequest {
	if s.Depth() == 0 || !s.top().dismissible {
		return nil
	}
	return &PopupCloseRequest{ID: s.ScopeID(), Reason: "escape"}
}

// Close requires the exact top ID, rejecting stale callbacks. The host may
// explicitly close a non-dismissible popup when its work is complete.
func (s *FocusStack) Close(id string) error {
	if s.Depth() == 0 || s.ScopeID() != id {
		return fmt.Errorf("popup %q is not on top", id)
	}
	restore := s.top().restore
	s.scopes = s.scopes[:len(s.scopes)-1]
	if !s.top().focus(restore) {
		s.top().reconcile()
	}
	return nil
}

type InputRoute struct {
	ScopeID string
	Blocked bool
}

// Route uses an empty target for keyboard input. A click must supply its hit
// scope ID; input aimed at an inactive/unknown scope is consumed by the host.
func (s *FocusStack) Route(targetScope string) InputRoute {
	active := s.ScopeID()
	return InputRoute{ScopeID: active, Blocked: active == "" || targetScope != "" && targetScope != active}
}
