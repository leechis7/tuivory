package tuivory_test

import (
	"encoding/json"
	"fmt"
	"github.com/gdamore/tcell/v2"
	ui "github.com/leechis7/tuivory/go"
	"os"
	"testing"
)

func TestInteractionContract(t *testing.T) {
	var data struct {
		States []struct {
			State                            ui.ControlState
			Role, Markers                    string
			Focusable, Activatable, Editable bool
		}
		Root  []ui.FocusTarget
		Steps []struct {
			Op, ID, Initial, Target, Request                 string
			ExpectScope                                      string `json:"expect_scope"`
			ExpectFocus                                      string `json:"expect_focus"`
			ExpectDepth                                      int    `json:"expect_depth"`
			Targets                                          []ui.FocusTarget
			Dismissible, Backwards, Blocked, Accepted, Error bool
		}
	}
	raw, err := os.ReadFile("testdata/interaction-cases.json")
	if err != nil {
		t.Fatal(err)
	}
	if err = json.Unmarshal(raw, &data); err != nil {
		t.Fatal(err)
	}
	for _, c := range data.States {
		v := c.State.Visual()
		if v.Role != c.Role || v.Markers != c.Markers || v.Focusable != c.Focusable || v.Activatable != c.Activatable || v.Editable != c.Editable {
			t.Fatalf("state %+v: %+v", c.State, v)
		}
		for _, theme := range []string{"dark", "light", "blackwhite"} {
			for _, profile := range []string{"8", "16", "256", "truecolor"} {
				doc, _ := ui.CandidateTokens()
				source, _ := doc.Palette(theme, profile)
				palette, _ := ui.Resolve(source)
				style, e := ui.ControlStyle(palette, c.State, true)
				if e != nil {
					t.Fatal(e)
				}
				fg, bg, attr := style.Decompose()
				expectedFG, expectedBG, _ := palette[c.Role].Style().Decompose()
				if fg != expectedFG || bg != expectedBG || (attr&tcell.AttrUnderline != 0) != c.Focusable {
					t.Fatal("control state style mismatch")
				}
			}
		}
	}
	stack, err := ui.NewFocusStack("root", data.Root)
	if err != nil {
		t.Fatal(err)
	}
	for i, c := range data.Steps {
		t.Run(fmt.Sprint(i, "-", c.Op), func(t *testing.T) {
			var e error
			switch c.Op {
			case "move":
				stack.Move(c.Backwards)
			case "focus":
				if stack.Focus(c.ID) != c.Accepted {
					t.Fatal("focus acceptance")
				}
			case "open":
				e = stack.Open(c.ID, c.Targets, c.Initial, c.Dismissible)
			case "close":
				e = stack.Close(c.ID)
			case "update":
				e = stack.Update(c.ID, c.Targets)
			case "route":
				route := stack.Route(c.Target)
				if route.ScopeID != c.ExpectScope || route.Blocked != c.Blocked {
					t.Fatal(route)
				}
			case "request":
				request := stack.RequestClose()
				id := ""
				if request != nil {
					id = request.ID
					if request.Reason != "escape" {
						t.Fatal(request)
					}
				}
				if id != c.Request {
					t.Fatal(id, c.Request)
				}
			default:
				t.Fatal(c.Op)
			}
			if (e != nil) != c.Error {
				t.Fatalf("error: %v", e)
			}
			if stack.ScopeID() != c.ExpectScope || stack.Focused() != c.ExpectFocus || stack.Depth() != c.ExpectDepth {
				t.Fatalf("scope=%s focus=%s depth=%d", stack.ScopeID(), stack.Focused(), stack.Depth())
			}
		})
	}
}

func TestFocusOwnershipAndLimits(t *testing.T) {
	targets := []ui.FocusTarget{{ID: "a"}, {ID: "b"}}
	stack, _ := ui.NewFocusStack("root", targets)
	targets[0].ID = "changed"
	copy := stack.Targets()
	copy[0].ID = "also changed"
	if stack.Focused() != "a" || stack.Targets()[0].ID != "a" {
		t.Fatal("aliased host storage")
	}
	if e := stack.Update("root", []ui.FocusTarget{{ID: "b"}, {ID: "a"}}); e != nil {
		t.Fatal(e)
	}
	if stack.Focused() != "a" || stack.Move(false) != "b" || stack.Move(true) != "a" {
		t.Fatal("stable ID and wrap")
	}
	for i := 0; i < 64; i++ {
		if e := stack.Open(fmt.Sprint(i), nil, "", true); e != nil {
			t.Fatal(e)
		}
	}
	if stack.Open("overflow", nil, "", true) == nil || stack.Depth() != 64 {
		t.Fatal("popup depth not bounded")
	}
	if _, e := ui.NewFocusStack("root", []ui.FocusTarget{{ID: ""}}); e == nil {
		t.Fatal("empty target accepted")
	}
	if _, e := ui.ControlStyle(ui.Palette{}, ui.ControlState{}, false); e == nil {
		t.Fatal("missing role accepted")
	}
}
