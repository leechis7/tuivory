package tuivory_test

import (
	"encoding/json"
	ui "github.com/leechis7/tuivory/go"
	terminal "github.com/leechis7/tuivory/go/terminal"
	"github.com/rivo/uniseg"
	"os"
	"reflect"
	"strings"
	"testing"
)

func editGrid(t *testing.T) *ui.Grid {
	g := optionGrid(t)
	g.SetEditOptions(ui.GridEditOptions{Enabled: true, StartTyping: true, AllowNull: true})
	return g
}
func key(k string, mods ...string) ui.InputEvent {
	return ui.InputEvent{Kind: "key", Key: k, Modifiers: mods}
}
func TestGridEditApprovalRetryCancelAndStale(t *testing.T) {
	g := editGrid(t)
	raw := g.Handle("copy", 8).Text
	if g.Input(key("enter"), 60, 8).Kind != "edit_begin" {
		t.Fatal("begin")
	}
	g.EditInput("select_all", "")
	g.EditInput("insert", "새값👩‍💻e\u0301")
	g.EditInput("left", "")
	g.EditInput("backspace", "")
	s, _ := g.EditSession()
	if s.Value.Text != "새값e\u0301" {
		t.Fatalf("grapheme editing %q", s.Value.Text)
	}
	if g.Input(key("tab"), 60, 8).Kind != "edit_submit" {
		t.Fatal("submit")
	}
	s, _ = g.EditSession()
	id := s.ID
	g.EditInput("insert", "blocked")
	if g.ColumnID != "name" || g.Handle("copy", 8).Kind != "" {
		t.Fatal("pending moved/copied")
	}
	if g.ResolveEdit(id+1, "", nil) || !g.ResolveEdit(id, "거절", nil) {
		t.Fatal("revision validation")
	}
	s, _ = g.EditSession()
	if s.Pending || s.Error != "거절" || s.Value.Text != "새값e\u0301" {
		t.Fatal(s)
	}
	g.EditInput("null", "")
	s, _ = g.EditSession()
	if !s.Value.Null {
		t.Fatal("NULL")
	}
	g.EditInput("next", "")
	s, _ = g.EditSession()
	if !g.ResolveEdit(s.ID, "", nil) {
		t.Fatal("accept")
	}
	s, _ = g.EditSession()
	if s.ColumnID != "value" {
		t.Fatal("next edit", s)
	}
	g.Input(key("escape"), 60, 8)
	g.Focus("a", "name")
	if g.Handle("copy", 8).Text != raw {
		t.Fatal("source mutated without host")
	}
	g.BeginEdit("")
	g.EditInput("submit", "")
	s, _ = g.EditSession()
	g.RequestFilter("new")
	if g.ResolveEdit(s.ID, "", nil) {
		t.Fatal("late response")
	}
	g.BeginEdit("x")
	g.EditInput("submit", "")
	s, _ = g.EditSession()
	rows, _ := ui.NewMemoryRows(nil)
	g.SetSource(rows)
	if g.ResolveEdit(s.ID, "", nil) {
		t.Fatal("replaced source")
	}
}
func TestGridEditPreparePermissionAndSourceAcceptance(t *testing.T) {
	g := editGrid(t)
	g.SetEditOptions(ui.GridEditOptions{Enabled: true, Prepare: func(r ui.GridRecord, c ui.GridColumn) (ui.GridValue, bool) {
		return ui.GridValue{Text: "typed", Null: true}, c.ID == "value"
	}})
	if g.BeginEdit("") {
		t.Fatal("host denied")
	}
	g.Focus("a", "value")
	if !g.BeginEdit("") {
		t.Fatal("prepare")
	}
	s, _ := g.EditSession()
	if s.Value.Text != "typed" || !s.Value.Null {
		t.Fatal(s)
	}
	g.EditInput("null", "")
	s, _ = g.EditSession()
	if !s.Value.Null {
		t.Fatal("NULL should be disabled")
	}
	g.EditInput("submit", "")
	s, _ = g.EditSession()
	source, _ := ui.NewMemoryRows([]ui.GridRecord{{ID: "a", Cells: map[string]string{"value": "accepted"}}})
	if !g.ResolveEdit(s.ID, "", source) || g.Handle("copy", 8).Text != "accepted" {
		t.Fatal("host acceptance")
	}
}
func TestGridColumnsPinHideMoveAndViewState(t *testing.T) {
	rows, _ := ui.NewMemoryRows([]ui.GridRecord{{ID: "r", Cells: map[string]string{"a": "A", "b": "B", "c": "C", "d": "D"}}})
	g, _ := ui.NewGrid([]ui.GridColumn{{ID: "a", Width: 8, Editable: true}, {ID: "b", Width: 20, Editable: true}, {ID: "c", Width: 20, Editable: true}, {ID: "d", Width: 8, Editable: true}}, rows)
	if !g.PinColumn("a", "left") || !g.PinColumn("d", "right") || !g.HideColumn("b", true) {
		t.Fatal("columns")
	}
	g.Focus("r", "c")
	geo := g.Geometry(48, 6)
	if len(geo.Columns) != 3 || geo.Columns[0].ID != "a" || geo.Columns[2].ID != "d" {
		t.Fatal(geo)
	}
	g.Handle("left", 6)
	if g.ColumnID != "a" {
		t.Fatal("hidden navigation")
	}
	if g.Focus("r", "b") {
		t.Fatal("hidden focus")
	}
	saved := g.SaveViewState()
	if !g.MoveColumn("c", 0) {
		t.Fatal("reorder")
	}
	g.HideColumn("b", false)
	if err := g.RestoreViewState(saved); err != nil {
		t.Fatal(err)
	}
	if !reflect.DeepEqual(saved, g.SaveViewState()) {
		t.Fatal("restore mismatch")
	}
	bad := saved
	bad.Columns = append([]ui.GridColumnLayout(nil), saved.Columns...)
	bad.Columns[1].ID = "missing"
	if g.RestoreViewState(bad) == nil || !reflect.DeepEqual(saved, g.SaveViewState()) {
		t.Fatal("non atomic")
	}
	for w := 0; w < 70; w++ {
		for _, s := range g.Geometry(w, 5).Columns {
			if s.Start < 0 || s.Start+s.Width > w {
				t.Fatal("pin overflow", w, s)
			}
		}
	}
}
func TestGridPasteQuotedTSVAndAtomicPermissions(t *testing.T) {
	g := editGrid(t)
	raw := g.Handle("copy", 6).Text
	p, err := g.RequestPaste("\"한글\t셀\"\t\"줄1\n줄2\"\n\"\"\tNULL", ui.GridPasteOptions{ParseNull: true, NullText: "NULL"})
	if err != nil {
		t.Fatal(err)
	}
	if len(p.Changes) != 4 || p.Changes[0].Value.Text != "한글\t셀" || p.Changes[1].Value.Text != "줄1\n줄2" || !p.Changes[3].Value.Null {
		t.Fatal(p)
	}
	p.Changes[0].Value.Text = "tamper"
	pending, _ := g.PendingPaste()
	if pending.Changes[0].Value.Text == "tamper" {
		t.Fatal("aliased request")
	}
	if g.ResolvePaste(p.ID+1, nil) || !g.ResolvePaste(p.ID, nil) {
		t.Fatal("paste token")
	}
	if g.Handle("copy", 6).Text != raw {
		t.Fatal("paste mutated")
	}
	for _, text := range []string{"\"unterminated", "a\tb\tc", "a\tb\nc", "a\nb\nc\nd"} {
		if _, err := g.RequestPaste(text, ui.GridPasteOptions{}); err == nil {
			g.CancelPaste()
			t.Fatal("invalid batch accepted", text)
		}
	}
	g.SetCellInfo(func(r ui.GridRecord, c ui.GridColumn) ui.GridCellInfo {
		return ui.GridCellInfo{State: ui.ControlState{ReadOnly: c.ID == "value"}}
	})
	if _, err := g.RequestPaste("a\tb", ui.GridPasteOptions{}); err == nil {
		t.Fatal("read only")
	}
	g.SetCellInfo(nil)
	p, _ = g.RequestPaste("a", ui.GridPasteOptions{})
	g.RequestFilter("replacement")
	if g.ResolvePaste(p.ID, nil) {
		t.Fatal("late paste")
	}
}
func TestGridFindDetailsAndGutterSeparation(t *testing.T) {
	g := editGrid(t)
	g.SetFind("한글", ui.GridFindOptions{})
	r, ok := g.FindNext(false)
	if !ok || r.RowID != "a" || r.ColumnID != "name" {
		t.Fatal(r)
	}
	if g.RequestSearch("outside").Kind != "search_request" {
		t.Fatal("global search")
	}
	g.Input(key("f", "ctrl"), 60, 8)
	g.Input(key("escape"), 60, 8)
	if !g.OpenDetails() {
		t.Fatal("details")
	}
	for w := 0; w < 65; w++ {
		for h := 0; h < 12; h++ {
			lines := g.Layout(w, h)
			if len(lines) > h {
				t.Fatal("detail height", w, h, len(lines))
			}
			for _, l := range lines {
				for _, s := range l.Spans {
					if s.Start+s.Width > w || uniseg.StringWidth(s.Text) > s.Width {
						t.Fatal("detail span", w, h, s)
					}
				}
			}
		}
	}
	g.CloseDetails()
	rows, _ := ui.NewMemoryRows([]ui.GridRecord{{ID: "a", Cells: map[string]string{"name": "one", "value": "two"}, State: ui.ControlState{Edited: true}}})
	g.SetSource(rows)
	o, _ := ui.GridPreset("data")
	g.SetOptions(o)
	g.SetCellInfo(func(r ui.GridRecord, c ui.GridColumn) ui.GridCellInfo {
		return ui.GridCellInfo{State: ui.ControlState{Edited: c.ID == "name"}}
	})
	for _, l := range g.Layout(50, 6) {
		if l.ID != "a" {
			continue
		}
		for _, s := range l.Spans {
			if s.Start == 0 && !strings.Contains(s.Text, "*") {
				t.Fatal("missing gutter marker")
			}
			if s.Start == g.Geometry(50, 6).Columns[1].Start && s.Role == "grid.edited" {
				t.Fatal("row edited inherited")
			}
		}
	}
}
func TestGridNewViewPhysicalOutputAllPalettes(t *testing.T) {
	for _, theme := range []string{"dark", "light", "blackwhite"} {
		for _, colors := range []string{"8", "16", "256", "truecolor"} {
			for _, ascii := range []bool{false, true} {
				doc, _ := ui.CandidateTokens()
				raw, _ := doc.Palette(theme, colors)
				p, err := ui.Resolve(raw)
				if err != nil {
					t.Fatal(err)
				}
				g := editGrid(t)
				o, _ := ui.GridPreset("data")
				o.ASCII = ascii
				g.SetOptions(o)
				g.SetCellInfo(func(r ui.GridRecord, c ui.GridColumn) ui.GridCellInfo {
					return ui.GridCellInfo{State: ui.ControlState{Edited: c.ID == "name"}}
				})
				v, err := ui.NewGridView(g, p, nil)
				if err != nil {
					t.Fatal(err)
				}
				screen := terminal.NewSimulationScreen("UTF-8")
				screen.Init()
				screen.SetSize(60, 10)
				v.SetRect(0, 0, 60, 10)
				v.Focus(func(ui.Primitive) {})
				v.Draw(screen)
				screen.Show()
				if !physicalContains(screen, "한글") {
					t.Fatal("CJK initial")
				}
				v.InputHandler()(terminal.NewEventKey(terminal.KeyEnter, 0, 0), func(ui.Primitive) {})
				g.EditInput("select_all", "")
				g.EditInput("insert", "수정한글")
				v.Draw(screen)
				screen.Show()
				if !physicalContains(screen, "수정한글") {
					t.Fatalf("CJK edit %#v session=%#v", g.Layout(60, 10), func() ui.GridEditSession { s, _ := g.EditSession(); return s }())
				}
				g.EditInput("submit", "")
				s, _ := g.EditSession()
				g.ResolveEdit(s.ID, "검증 실패", nil)
				v.Draw(screen)
				screen.Show()
				if !physicalContains(screen, "검증 실패") {
					t.Fatal("error hidden")
				}
				g.CancelEdit()
				for _, w := range []int{40, 20, 8, 3, 1, 60} {
					screen.SetSize(w, 10)
					v.SetRect(0, 0, w, 10)
					v.Draw(screen)
					screen.Show()
				}
				screen.Fini()
			}
		}
	}
}
func physicalContains(s terminal.SimulationScreen, want string) bool {
	w, h := s.Size()
	for y := 0; y < h; y++ {
		line := ""
		for x := 0; x < w; {
			r, comb, _, width := s.GetContent(x, y)
			line += string(append([]rune{r}, comb...))
			x += max(1, width)
		}
		if strings.Contains(line, want) {
			return true
		}
	}
	return false
}

func TestGridSharedPasteCases(t *testing.T) {
	var data struct {
		Cases []struct {
			ID, Text string
			Accepted bool
			Values   []string
		}
	}
	raw, err := os.ReadFile("testdata/grid-work-cases.json")
	if err != nil {
		t.Fatal(err)
	}
	if err = json.Unmarshal(raw, &data); err != nil {
		t.Fatal(err)
	}
	for _, c := range data.Cases {
		t.Run(c.ID, func(t *testing.T) {
			g := editGrid(t)
			p, err := g.RequestPaste(c.Text, ui.GridPasteOptions{})
			if (err == nil) != c.Accepted {
				t.Fatalf("accept %v: %v", c.Accepted, err)
			}
			values := []string{}
			for _, v := range p.Changes {
				values = append(values, v.Value.Text)
			}
			if !reflect.DeepEqual(values, c.Values) {
				t.Fatalf("%q != %q", values, c.Values)
			}
		})
	}
}
func TestGridEditedCombinationsPhysical(t *testing.T) {
	for _, theme := range []string{"dark", "light", "blackwhite"} {
		for _, profile := range []string{"8", "16", "256", "truecolor"} {
			for _, ascii := range []bool{false, true} {
				doc, _ := ui.CandidateTokens()
				raw, _ := doc.Palette(theme, profile)
				p, _ := ui.Resolve(raw)
				for mask := 0; mask < 64; mask++ {
					g := editGrid(t)
					o, _ := ui.GridPreset("data")
					o.ASCII = ascii
					o.PreserveEdited = mask&32 != 0
					g.SetOptions(o)
					g.SetCellInfo(func(r ui.GridRecord, c ui.GridColumn) ui.GridCellInfo {
						return ui.GridCellInfo{Null: mask&16 != 0, State: ui.ControlState{Edited: c.ID == "name", Disabled: mask&1 != 0, Invalid: mask&2 != 0, ReadOnly: mask&4 != 0, Busy: mask&8 != 0}}
					})
					g.Handle("select", 8)
					v, _ := ui.NewGridView(g, p, nil)
					screen := terminal.NewSimulationScreen("UTF-8")
					screen.Init()
					screen.SetSize(60, 8)
					v.SetRect(0, 0, 60, 8)
					v.Draw(screen)
					screen.Show()
					if !physicalContains(screen, "*") {
						t.Fatalf("dirty cue hidden %s/%s/%v/%d", theme, profile, ascii, mask)
					}
					span := g.Geometry(60, 8).Columns[0]
					_, _, style, _ := screen.GetContent(span.Start+2, 1)
					fg, bg, _ := style.Decompose()
					if fg == bg {
						t.Fatalf("invisible text %s/%s/%v/%d", theme, profile, ascii, mask)
					}
					screen.Fini()
				}
			}
		}
	}
}
func TestGridColumnMouseAndCopyHidden(t *testing.T) {
	g := editGrid(t)
	geo := g.Geometry(60, 8)
	g.Pointer("down", geo.Columns[0].Start, 0, 60, 8, false)
	if g.Pointer("move", geo.Columns[1].Start, 0, 60, 8, false).Kind != "columns" {
		t.Fatal("header drag")
	}
	g.Pointer("up", 0, 0, 60, 8, false)
	if g.Columns()[0].ID != "value" {
		t.Fatal("reorder")
	}
	g.HideColumn("value", true)
	g.Focus("a", "name")
	if g.Handle("copy_row", 8).Text != "한글😀e\u0301 long" {
		t.Fatal("hidden copy")
	}
	g.BeginEdit("")
	s, _ := g.EditSession()
	geo = g.Geometry(60, 8)
	if g.Pointer("click", geo.Columns[0].Start, 1, 60, 8, false).Kind != "edit_select" {
		t.Fatal("editor click")
	}
	g.EditInput("submit", "")
	s, _ = g.EditSession()
	o := g.Options()
	o.DisableEditing = true
	g.SetOptions(o)
	if g.ResolveEdit(s.ID, "", nil) {
		t.Fatal("disabled accepted")
	}
}

func TestGridInputGuardsCaretAndRemovedApprovalRow(t *testing.T) {
	g := editGrid(t)
	o := g.Options()
	o.DisableKeyboard = true
	g.SetOptions(o)
	if g.Input(ui.PasteInput("x"), 60, 8).Kind != "" {
		t.Fatal("disabled paste")
	}
	o.DisableKeyboard = false
	g.SetOptions(o)
	g.BeginEdit("abcdef")
	g.EditInput("home", "")
	g.EditInput("right", "")
	g.EditInput("right", "")
	g.EditInput("right", "")
	geo := g.Geometry(60, 8)
	g.Pointer("click", geo.Columns[0].Start+4, 1, 60, 8, false)
	g.EditInput("insert", "X")
	s, _ := g.EditSession()
	if s.Value.Text != "abcdXef" {
		t.Fatal("caret click", s.Value.Text)
	}
	g.EditInput("next", "")
	s, _ = g.EditSession()
	empty, _ := ui.NewMemoryRows(nil)
	if !g.ResolveEdit(s.ID, "", empty) {
		t.Fatal("accept")
	}
	if _, ok := g.EditSession(); ok {
		t.Fatal("removed row reopened")
	}
	g = editGrid(t)
	g.SetEditOptions(ui.GridEditOptions{Prepare: func(ui.GridRecord, ui.GridColumn) (ui.GridValue, bool) { return ui.GridValue{}, false }})
	if _, err := g.RequestPaste("x", ui.GridPasteOptions{}); err == nil {
		t.Fatal("host eligibility ignored")
	}
}

func TestGridPasteRechecksHostEligibility(t *testing.T) {
	g := editGrid(t)
	allowed := true
	g.SetEditOptions(ui.GridEditOptions{Prepare: func(ui.GridRecord, ui.GridColumn) (ui.GridValue, bool) { return ui.GridValue{}, allowed }})
	p, err := g.RequestPaste("x", ui.GridPasteOptions{})
	if err != nil {
		t.Fatal(err)
	}
	allowed = false
	if g.ResolvePaste(p.ID, nil) {
		t.Fatal("revoked paste accepted")
	}
}

func TestGridHidingCurrentColumnWithEmptySource(t *testing.T) {
	g := editGrid(t)
	empty, _ := ui.NewMemoryRows(nil)
	g.SetSource(empty)
	if !g.HideColumn("name", true) || g.ColumnID != "value" {
		t.Fatal("hidden current column in empty grid")
	}
}
