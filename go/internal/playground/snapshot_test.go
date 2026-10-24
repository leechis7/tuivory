package playground

import (
	"fmt"
	"html"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/gdamore/tcell/v2"
)

// Opt-in static documentation images rendered from real widget cells.
func TestSnapshot(t *testing.T) {
	dir := os.Getenv("TUIVORY_SNAPSHOT_DIR")
	if dir == "" {
		t.Skip("set TUIVORY_SNAPSHOT_DIR to render documentation images")
	}
	if err := os.MkdirAll(dir, 0755); err != nil {
		t.Fatal(err)
	}
	ui, terminal := testUI(t)
	for i, theme := range themeNames {
		ui.theme.SetCurrentOption(i)
		drawUI(ui, terminal)
		if err := writeSVG(filepath.Join(dir, "playground-"+theme+".svg"), terminal); err != nil {
			t.Fatal(err)
		}
	}
	ui.theme.SetCurrentOption(0)
	ui.openPreview()
	drawUI(ui, terminal)
	if err := writeSVG(filepath.Join(dir, "playground-popup.svg"), terminal); err != nil {
		t.Fatal(err)
	}
}
func writeSVG(path string, screen tcell.Screen) error {
	w, h := screen.Size()
	var out strings.Builder
	fmt.Fprintf(&out, `<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d"><title>TUIVORY live widget preview</title><desc>SimulationScreen reference rendering; not an actual remote terminal screenshot.</desc>`, w*10, h*22, w*10, h*22)
	color := func(c tcell.Color) string {
		if !c.Valid() {
			c = tcell.ColorBlack
		}
		r, g, b := c.RGB()
		return fmt.Sprintf("#%02x%02x%02x", r, g, b)
	}
	for y := 0; y < h; y++ {
		start := 0
		_, _, st, _ := screen.GetContent(0, y)
		_, bg, _ := st.Decompose()
		last := color(bg)
		for x := 1; x <= w; x++ {
			next := ""
			if x < w {
				_, _, st, _ := screen.GetContent(x, y)
				_, bg, _ := st.Decompose()
				next = color(bg)
			}
			if next != last {
				fmt.Fprintf(&out, `<rect x="%d" y="%d" width="%d" height="22" fill="%s"/>`, start*10, y*22, (x-start)*10, last)
				start = x
				last = next
			}
		}
	}
	out.WriteString(`<g font-family="D2Coding,monospace" font-size="20">`)
	for y := 0; y < h; y++ {
		for x := 0; x < w; x++ {
			r, comb, style, width := screen.GetContent(x, y)
			if width == 0 || r == ' ' || r == 0 {
				continue
			}
			fg, _, attrs := style.Decompose()
			opacity := "1"
			if attrs&tcell.AttrDim != 0 {
				opacity = "0.45"
			}
			text := html.EscapeString(string(append([]rune{r}, comb...)))
			fmt.Fprintf(&out, `<text x="%d" y="%d" fill="%s" opacity="%s">%s</text>`, x*10, y*22+18, color(fg), opacity, text)
			if attrs&tcell.AttrUnderline != 0 {
				fmt.Fprintf(&out, `<path d="M%d %dh%d" stroke="%s"/>`, x*10, y*22+20, width*10, color(fg))
			}
		}
	}
	out.WriteString(`</g></svg>`)
	return os.WriteFile(path, []byte(out.String()), 0644)
}
