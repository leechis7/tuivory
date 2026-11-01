package tuivory

import "testing"

func TestDarkEightSyntaxRolesAfterShow(t *testing.T) {
	tokens, _ := CandidateTokens()
	raw, _ := tokens.Palette("dark", "8")
	palette, _ := Resolve(raw)
	styles, _ := NewStyles("dark", "8")
	roles := []string{"keyword", "function", "type", "string", "number", "comment", "parameter"}
	doc := NewEditor("xKFTSNCP")
	doc.LineNumbers = false
	doc.Buffer.Select(0, 0)
	for i, role := range roles {
		doc.Syntax = append(doc.Syntax, SyntaxSpan{Start: i + 1, End: i + 2, Role: "syntax." + role})
	}
	screen := NewSimulationScreen("UTF-8")
	if err := screen.Init(); err != nil {
		t.Fatal(err)
	}
	defer screen.Fini()
	screen.SetSize(20, 3)
	view, err := NewEditorView(doc, palette, nil)
	if err != nil {
		t.Fatal(err)
	}
	view.SetRect(0, 0, 20, 3)
	view.Draw(screen)
	screen.Show()
	cells, _, _ := screen.GetContents()
	seen := map[[3]uint64]bool{}
	for i, role := range roles {
		fg, bg, attrs := cells[i+1].Style.Decompose()
		want := styles.SyntaxStyle(SyntaxKind(i+1), styles.EditorStyle())
		wfg, wbg, wa := want.Decompose()
		if fg != wfg || bg != wbg || attrs != wa {
			t.Errorf("%s: physical style %v != %v", role, cells[i+1].Style, want)
		}
		if surfaceContrast(fg, bg) < 4.5 {
			t.Errorf("%s: contrast", role)
		}
		seen[[3]uint64{uint64(fg), uint64(bg), uint64(attrs)}] = true
	}
	if len(seen) != 7 {
		t.Fatalf("only %d distinguishable syntax styles", len(seen))
	}
}
