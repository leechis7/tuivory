package tuivory_test

import (
	"encoding/json"
	ui "github.com/leechis7/tuivory/go"
	"github.com/rivo/uniseg"
	"os"
	"reflect"
	"strings"
	"testing"
)

func TestLayoutTokensAndStackBounds(t *testing.T) {
	raw, e := os.ReadFile("testdata/layout-tokens.json")
	if e != nil {
		t.Fatal(e)
	}
	var data struct {
		CompactBelow         int `json:"compact_below"`
		Compact, Comfortable struct {
			Gap, Padding int
			ControlGap   int `json:"control_gap"`
		}
	}
	if e = json.Unmarshal(raw, &data); e != nil {
		t.Fatal(e)
	}
	compact, _ := ui.ResolveSpacing(ui.DensityAuto, 79)
	comfortable, _ := ui.ResolveSpacing(ui.DensityAuto, 80)
	if compact.Gap != data.Compact.Gap || compact.Padding != data.Compact.Padding || compact.ControlGap != data.Compact.ControlGap || comfortable.Gap != data.Comfortable.Gap || comfortable.Padding != data.Comfortable.Padding || comfortable.ControlGap != data.Comfortable.ControlGap || compact.CompactBelow != data.CompactBelow {
		t.Fatal("shared tokens")
	}
	items := []ui.StackItem{{ID: "main", Min: 12, Preferred: 40, Weight: 1}, {ID: "aside", Min: 10, Preferred: 24}}
	original := append([]ui.StackItem(nil), items...)
	for width := 0; width < 241; width++ {
		r, e := ui.StackLayout(items, width, 2)
		if e != nil {
			t.Fatal(e)
		}
		end := 0
		for _, slot := range r.Slots {
			if slot.Start < end || slot.Start+slot.Size > width || slot.Size < 0 {
				t.Fatal("bounds/overlap", width, r)
			}
			if slot.Size > 0 {
				end = slot.Start + slot.Size
			}
		}
		rects, _, e := ui.StackRects(ui.CellRect{X: 2, Y: 3, Width: width, Height: 20}, items, comfortable, false)
		if e != nil {
			t.Fatal(e)
		}
		for _, r := range rects {
			if r.Rect.X < 2 || r.Rect.X+r.Rect.Width > 2+width || r.Rect.Y < 3 || r.Rect.Y+r.Rect.Height > 23 {
				t.Fatal("rect bounds", r)
			}
		}
	}
	if !reflect.DeepEqual(items, original) {
		t.Fatal("preferences mutated")
	}
	narrow, _ := ui.StackLayout(items, 8, 2)
	if narrow.Slots[0].Size != 8 || len(narrow.Hidden) != 1 {
		t.Fatal("narrow fallback")
	}
	if !ui.DrawerLayout(ui.CellRect{Width: 30, Height: 10}, 24, 40).Overlay || ui.DrawerLayout(ui.CellRect{Width: 100, Height: 10}, 24, 40).Overlay {
		t.Fatal("drawer threshold")
	}
	if _, e := ui.StackLayout([]ui.StackItem{{ID: "a", Min: 1}, {ID: "a", Min: 1}}, 20, 1); e == nil {
		t.Fatal("duplicate")
	}
}
func TestBadgeChipAndKeyboardHelp(t *testing.T) {
	zero := uint64(0)
	large := uint64(123)
	if (ui.Badge{Label: "Count", Count: &zero}).Line(30).Text != "Count [0]" || (ui.Badge{Label: "Count", Count: &large}).Line(30).Text != "Count [99+]" {
		t.Fatal("count semantics")
	}
	chip := ui.Chip{ID: "filter", Label: "한글 필터", Removable: true}
	if chip.RequestRemove().Kind != "remove" || !chip.Removable {
		t.Fatal("request")
	}
	chip.State.ReadOnly = true
	if chip.RequestRemove().Kind != "" {
		t.Fatal("readonly remove")
	}
	if uniseg.StringWidth(chip.Line(6).Text) > 6 {
		t.Fatal("chip clip")
	}
	help, e := ui.NewHelp([]ui.Shortcut{{Key: "x", Text: "Remove", Priority: 1}, {Key: "F1", Text: "Help", Priority: 10}})
	if e != nil {
		t.Fatal(e)
	}
	if !strings.Contains(help.Layout(20, 1)[0].Text, "F1") {
		t.Fatal("priority")
	}
	if _, e := ui.NewHelp([]ui.Shortcut{{Key: "F1"}, {Key: "f1"}}); e == nil {
		t.Fatal("conflicting shortcuts")
	}
}
