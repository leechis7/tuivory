package style

import (
	"testing"

	"github.com/gdamore/tcell/v2"
	"github.com/leechis7/tuivory/go/internal/tokens"
)

func TestResolvePreservesColorKindsAndWeight(t *testing.T) {
	d, err := tokens.Candidate()
	if err != nil {
		t.Fatal(err)
	}
	for name, source := range d.Palettes {
		palette, err := Resolve(source)
		if err != nil {
			t.Fatal(err)
		}
		for role, pair := range palette {
			fg, bg, _ := pair.Style().Decompose()
			isRGB := source[role].Foreground[0] == '#'
			if fg.IsRGB() != isRGB || bg.IsRGB() != (source[role].Background[0] == '#') {
				t.Fatalf("lost color kind: %s/%s", name, role)
			}
			if !isRGB && int(fg&^tcell.ColorValid) > 255 {
				t.Fatal("lost ANSI index")
			}
		}
	}
	p, err := Resolve(tokens.Palette{"body": {Foreground: "7", Background: "0", FontWeight: "bold"}})
	if err != nil {
		t.Fatal(err)
	}
	_, _, attrs := p["body"].Style().Decompose()
	if attrs&tcell.AttrBold == 0 {
		t.Fatal("lost weight")
	}
	if _, err := Resolve(tokens.Palette{"body": {Foreground: "256", Background: "0", FontWeight: "none"}}); err == nil {
		t.Fatal("invalid color accepted")
	}
}
