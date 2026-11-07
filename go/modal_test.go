package tuivory_test

import (
	"fmt"
	ui "github.com/leechis7/tuivory/go"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestModalWrappedButtonsAfterShow(t *testing.T) {
	for _, theme := range []string{"dark", "light", "blackwhite"} {
		for _, profile := range []string{"8", "16", "256", "truecolor"} {
			for _, en := range []bool{false, true} {
				t.Run(fmt.Sprintf("%s/%s/en=%t", theme, profile, en), func(t *testing.T) {
					labels := []string{"커밋 후 접속", "롤백 후 접속", "취소"}
					if en {
						labels = []string{"Commit and connect", "Roll back and connect", "Cancel"}
					}
					message := "한글 CJK 界 😀 좁은 확인창"
					if en {
						message = "Unicode CJK 界 😀 narrow confirmation"
					}
					m := ui.NewModal().SetText(message).AddButtons(labels[:2]).AddButtons(labels[2:]).SetFocus(2)
					styles, _ := ui.NewStyles(theme, profile)
					styler := ui.Styler{Styles: styles}
					styler.Modal(m)
					var form *ui.WidgetForm
					m.Focus(func(p ui.Primitive) { form = p.(*ui.WidgetForm) })
					screen := ui.NewSimulationScreen("UTF-8")
					if e := screen.Init(); e != nil {
						t.Fatal(e)
					}
					defer screen.Fini()
					app := ui.NewApplication().SetScreen(screen).SetRoot(m, true).SetFocus(m)
					got := -99
					text := ""
					m.SetDoneFunc(func(i int, s string) { got = i; text = s })
					for _, size := range [][2]int{{120, 40}, {80, 24}, {40, 16}, {20, 10}, {8, 6}, {3, 2}, {1, 1}, {40, 16}, {120, 40}} {
						screen.SetSize(size[0], size[1])
						app.ForceDraw()
						if dir := os.Getenv("TUIVORY_MODAL_SNAPSHOT_DIR"); dir != "" && size == [2]int{40, 16} && profile == "8" && (theme == "dark" || theme == "light") {
							suffix := ""
							if en {
								suffix = "-en"
							}
							writeModalSVG(t, filepath.Join(dir, "modal-"+theme+suffix+".svg"), screen)
						}
						button := form.GetButton(2)
						x, y, w, h := button.GetRect()
						if x < 0 || y < 0 || w < 1 || h < 1 || x+w > size[0] || y+h > size[1] {
							t.Fatalf("%v cancel outside screen: %d,%d %dx%d", size, x, y, w, h)
						}
						cells, sw, _ := screen.GetContents()
						if size[0] >= 40 {
							mx, my, _, _ := m.GetRect()
							fg, bg, _ := cells[my*sw+mx].Style.Decompose()
							if fg == bg {
								t.Fatalf("invisible modal border: %s/%s", theme, profile)
							}
						}
						visible := false
						for xx := x; xx < x+w; xx++ {
							if len(cells[y*sw+xx].Runes) > 0 && strings.TrimSpace(string(cells[y*sw+xx].Runes)) != "" {
								visible = true
							}
						}
						if !visible && w >= ui.TaggedStringWidth(string([]rune(labels[2])[0])) {
							t.Fatalf("%v focused button blank", size)
						}
						if size[0] >= 40 {
							var b strings.Builder
							for xx := x; xx < x+w; xx++ {
								text := string(cells[y*sw+xx].Runes)
								b.WriteString(text)
								xx += max(0, ui.TaggedStringWidth(text)-1)
							}
							if !strings.Contains(b.String(), labels[2]) {
								t.Fatalf("cancel label lost: %q", b.String())
							}
						}
					}
					app.GetFocus().InputHandler()(ui.NewEventKey(ui.KeyEnter, 0, ui.ModNone), func(p ui.Primitive) { app.SetFocus(p) })
					if got != 2 || text != labels[2] {
						t.Fatalf("callback %d %q", got, text)
					}
					got = -99
					app.SetFocus(m)
					app.GetFocus().InputHandler()(ui.NewEventKey(ui.KeyEscape, 0, ui.ModNone), func(p ui.Primitive) { app.SetFocus(p) })
					if got != -1 {
						t.Fatal("escape callback", got)
					}
					styler.Apply(ui.Roles{}, m)
					app.ForceDraw()
				})
			}
		}
	}
}

func writeModalSVG(t *testing.T, path string, screen ui.SimulationScreen) {
	t.Helper()
	cells, w, h := screen.GetContents()
	var b strings.Builder
	fmt.Fprintf(&b, `<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d"><g font-family="monospace" font-size="14">`, w*9, h*18, w*9, h*18)
	for y := 0; y < h; y++ {
		for x := 0; x < w; x++ {
			c := cells[y*w+x]
			_, bg, _ := c.Style.Decompose()
			br, bgGreen, bb := bg.RGB()
			fmt.Fprintf(&b, `<rect x="%d" y="%d" width="9" height="18" fill="#%02x%02x%02x"/>`, x*9, y*18, max(0, br), max(0, bgGreen), max(0, bb))
		}
	}
	for y := 0; y < h; y++ {
		for x := 0; x < w; x++ {
			c := cells[y*w+x]
			fg, _, a := c.Style.Decompose()
			fr, fgreen, fb := fg.RGB()
			if len(c.Runes) == 0 || strings.TrimSpace(string(c.Runes)) == "" {
				continue
			}
			text := strings.NewReplacer("&", "&amp;", "<", "&lt;", ">", "&gt;").Replace(string(c.Runes))
			weight := "normal"
			if a&ui.AttrBold != 0 {
				weight = "bold"
			}
			fmt.Fprintf(&b, `<text x="%d" y="%d" fill="#%02x%02x%02x" font-weight="%s">%s</text>`, x*9, y*18+14, max(0, fr), max(0, fgreen), max(0, fb), weight, text)
			if a&ui.AttrUnderline != 0 {
				fmt.Fprintf(&b, `<path d="M%d %dh%d" stroke="#%02x%02x%02x"/>`, x*9, y*18+16, max(1, ui.TaggedStringWidth(string(c.Runes)))*9, max(0, fr), max(0, fgreen), max(0, fb))
			}
		}
	}
	b.WriteString("</g></svg>\n")
	if e := os.MkdirAll(filepath.Dir(path), 0755); e != nil {
		t.Fatal(e)
	}
	if e := os.WriteFile(path, []byte(b.String()), 0644); e != nil {
		t.Fatal(e)
	}
}

func TestModalKeyboardMouseAndInteroperability(t *testing.T) {
	m := ui.NewModal().SetText("Choose").AddButtons([]string{"First", "Second", "Cancel"}).SetFocus(2)
	if m.Modal == nil {
		t.Fatal("missing explicit backend interoperability")
	}
	s := ui.NewSimulationScreen("UTF-8")
	s.Init()
	defer s.Fini()
	s.SetSize(40, 16)
	app := ui.NewApplication().SetScreen(s).SetRoot(m, true).SetFocus(m)
	var form *ui.WidgetForm
	m.Focus(func(p ui.Primitive) { form = p.(*ui.WidgetForm) })
	got := -1
	m.SetDoneFunc(func(i int, _ string) { got = i })
	for _, key := range []ui.Key{ui.KeyBacktab, ui.KeyRight, ui.KeyTab, ui.KeyLeft} {
		app.GetFocus().InputHandler()(ui.NewEventKey(key, 0, ui.ModNone), func(p ui.Primitive) { app.SetFocus(p) })
		app.ForceDraw()
		_, i := form.GetFocusedItemIndex()
		if i < 0 {
			t.Fatal("lost button focus")
		}
	}
	app.ForceDraw()
	x, y, w, _ := form.GetButton(1).GetRect()
	m.MouseHandler()(ui.MouseLeftDown, ui.NewEventMouse(x+w/2, y, ui.Button1, 0), func(p ui.Primitive) { app.SetFocus(p) })
	m.MouseHandler()(ui.MouseLeftClick, ui.NewEventMouse(x+w/2, y, 0, 0), func(p ui.Primitive) { app.SetFocus(p) })
	if got != 1 {
		t.Fatal("mouse callback", got)
	}
	m.ClearButtons().AddButtons([]string{"New"}).SetFocus(0)
	app.SetFocus(m)
	app.ForceDraw()
	app.GetFocus().InputHandler()(ui.NewEventKey(ui.KeyEnter, 0, 0), func(p ui.Primitive) { app.SetFocus(p) })
	if got != 0 {
		t.Fatal("clear/add callback", got)
	}
}

func TestModalCentersPaintedButtonRows(t *testing.T) {
	for _, labels := range [][]string{
		{"확인", "다시 연결한 다음 계속", "설정 열기", "취소"},
		{"OK", "Reconnect and continue", "Open settings", "Cancel"},
	} {
		for count := 1; count <= len(labels); count++ {
			for _, width := range []int{40, 120} {
				t.Run(fmt.Sprintf("%s/%d/%d", labels[0], count, width), func(t *testing.T) {
					modal := ui.NewModal().SetText("Choose").AddButtons(labels[:count]).SetFocus(count - 1)
					screen := ui.NewSimulationScreen("UTF-8")
					if err := screen.Init(); err != nil {
						t.Fatal(err)
					}
					defer screen.Fini()
					screen.SetSize(width, 16)
					app := ui.NewApplication().SetScreen(screen).SetRoot(modal, true).SetFocus(modal)
					var form *ui.WidgetForm
					modal.Focus(func(p ui.Primitive) { form = p.(*ui.WidgetForm) })
					got := -1
					modal.SetDoneFunc(func(index int, _ string) { got = index })
					app.ForceDraw()
					cells, screenWidth, _ := screen.GetContents()
					left, _, innerWidth, _ := modal.GetInnerRect()
					left++
					innerWidth -= 2
					rows := map[int][2]int{}
					for i := 0; i < count; i++ {
						x, y, w, h := form.GetButton(i).GetRect()
						if x < left || x+w > left+innerWidth || h != 1 {
							t.Fatalf("button %d outside content: %d,%d %dx%d", i, x, y, w, h)
						}
						if _, ok := rows[y]; !ok {
							rows[y] = [2]int{x, x + w}
						} else {
							rows[y] = [2]int{rows[y][0], x + w}
						}
						var text strings.Builder
						for column := x; column < x+w; column++ {
							text.WriteString(string(cells[y*screenWidth+column].Runes))
						}
						if !strings.Contains(strings.ReplaceAll(text.String(), " ", ""), strings.ReplaceAll(labels[i], " ", "")) {
							t.Fatalf("label %q missing in painted button: %q", labels[i], text.String())
						}
						modal.MouseHandler()(ui.MouseLeftClick, ui.NewEventMouse(x, y, 0, 0), func(p ui.Primitive) { app.SetFocus(p) })
						if got != i {
							t.Fatalf("hit for button %d: %d", i, got)
						}
					}
					for _, row := range rows {
						if row[0]-left != (innerWidth-(row[1]-row[0]))/2 {
							t.Fatalf("row %v not centered in [%d,%d)", row, left, left+innerWidth)
						}
					}
				})
			}
		}
	}
}
