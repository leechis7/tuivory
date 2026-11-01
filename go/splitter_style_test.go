package tuivory

import "testing"

func TestSplitterReferenceContrastAcrossThemesAndProfiles(t *testing.T) {
	for _, theme := range []string{"dark", "light", "blackwhite"} {
		for _, profile := range []string{"8", "16", "256", "truecolor"} {
			styles, err := NewStyles(theme, profile)
			if err != nil {
				t.Fatal(err)
			}
			fg, bg, _ := styles.SplitterStyle().Decompose()
			if ratio := surfaceContrast(fg, bg); ratio < 3 {
				t.Errorf("%s/%s: divider contrast %.3f < 3:1 (%v/%v)", theme, profile, ratio, fg, bg)
			}
		}
	}
}

func TestDarkEightSyntaxReferenceContrastPolicy(t *testing.T) {
	styles, _ := NewStyles("dark", "8")
	base := styles.EditorStyle()
	for kind := SyntaxKeyword; kind <= SyntaxParameter; kind++ {
		fg, bg, attrs := styles.SyntaxStyle(kind, base).Decompose()
		if fg.IsRGB() || fg&^ColorValid > 7 {
			t.Errorf("kind %d requires more than eight colors", kind)
		}
		if ratio := surfaceContrast(fg, bg); ratio < 4.5 {
			t.Errorf("kind %d text contrast %.3f < 4.5:1", kind, ratio)
		}
		if kind == SyntaxKeyword && attrs&AttrUnderline == 0 {
			t.Error("keyword lost its non-color cue")
		}
	}
}
