package tuivory_test

import (
	"encoding/json"
	"fmt"
	ui "github.com/leechis7/tuivory/go"
	"os"
	"reflect"
	"strings"
	"testing"
)

func TestSQLSyntaxShared(t *testing.T) {
	raw, e := os.ReadFile("testdata/syntax-cases.json")
	if e != nil {
		t.Fatal(e)
	}
	var f struct {
		Cases []struct {
			Name, Source, Language, Dialect string
			Tokens                          []ui.SyntaxToken
		}
		Roles map[string]string `json:"role_fallbacks"`
	}
	if e = json.Unmarshal(raw, &f); e != nil {
		t.Fatal(e)
	}
	analyzer := ui.NewSQLAnalyzer()
	for _, c := range f.Cases {
		t.Run(c.Name, func(t *testing.T) {
			a, e := analyzer.AnalyzeSyntax(c.Source, ui.SyntaxRequest{Language: c.Language, Dialect: c.Dialect})
			if e != nil {
				t.Fatal(e)
			}
			if a.Source != c.Source || a.Language != c.Language || a.Dialect != c.Dialect || !reflect.DeepEqual(a.Tokens, c.Tokens) {
				t.Fatalf("%+v != %+v", a.Tokens, c.Tokens)
			}
			d := ui.NewEditor(c.Source)
			d.Buffer.Select(0, 0)
			if e = d.SetSyntaxAnalyzer(analyzer, ui.SyntaxRequest{Language: c.Language}); e != nil {
				t.Fatal(e)
			}
			d.Layout(40, 8)
			// Every valid UTF-8 prefix is a legitimate incomplete editor input.
			for i := range c.Source {
				a, e := analyzer.AnalyzeSyntax(c.Source[:i], ui.SyntaxRequest{})
				if e != nil {
					t.Fatal(e)
				}
				if e = a.Validate(c.Source[:i]); e != nil {
					t.Fatal(e)
				}
				d.SetText(c.Source[:i])
				if e = d.SyntaxError(); e != nil {
					t.Fatal(e)
				}
			}
		})
	}
	for role, want := range f.Roles {
		if got := ui.SyntaxRoleStyle(role); got != want {
			t.Fatalf("%s: %s != %s", role, got, want)
		}
	}
	for _, r := range []ui.SyntaxRequest{{Language: "go"}, {Dialect: "postgresql"}} {
		if _, e = analyzer.AnalyzeSyntax("select 1", r); e == nil {
			t.Fatal("unsupported analyzer request")
		}
	}
}
func TestSyntaxBindingAndByteEdits(t *testing.T) {
	d := ui.NewEditor("SELECT '한글 é 😀' FROM 표")
	a := ui.NewSQLAnalyzer()
	if e := d.SetSyntaxAnalyzer(a, ui.SyntaxRequest{}); e != nil {
		t.Fatal(e)
	}
	original := d.Buffer.Text()
	d.Buffer.Select(0, 6)
	before := d.Syntax
	for _, bad := range []ui.SyntaxAnalysis{{Source: "stale"}, {Source: original, Tokens: []ui.SyntaxToken{{Start: 1, End: 3}, {Start: 2, End: 4}}}, {Source: original, Tokens: []ui.SyntaxToken{{Start: 9, End: 10, Role: "string"}}}} {
		e := d.SetSyntaxAnalyzer(ui.SyntaxAnalyzerFunc(func(string, ui.SyntaxRequest) (ui.SyntaxAnalysis, error) { return bad, nil }), ui.SyntaxRequest{})
		if e == nil || !reflect.DeepEqual(before, d.Syntax) {
			t.Fatal("non-atomic invalid result")
		}
	}
	calls := 0
	custom := ui.SyntaxAnalyzerFunc(func(s string, r ui.SyntaxRequest) (ui.SyntaxAnalysis, error) {
		calls++
		if strings.Contains(s, "!") {
			return ui.SyntaxAnalysis{}, fmt.Errorf("failed")
		}
		return ui.SyntaxAnalysis{Source: s, Tokens: []ui.SyntaxToken{{Start: 0, End: len(s), Role: "future-role"}}}, nil
	})
	if e := d.SetSyntaxAnalyzer(custom, ui.SyntaxRequest{}); e != nil {
		t.Fatal(e)
	}
	for i := 0; i < 5; i++ {
		d.Layout(20, 4)
	}
	if calls != 1 || d.Syntax[0].Role != "body" {
		t.Fatal("cache/fallback")
	}
	d.Buffer.Select(0, 0)
	d.Handle("insert", "!")
	if d.SyntaxError() == nil || len(d.Syntax) != 0 {
		t.Fatal("stale highlighting")
	}
	d.Handle("undo", "")
	if d.SyntaxError() != nil || d.Buffer.Text() != original {
		t.Fatal("undo analysis")
	}
	if e := d.SetSyntaxAnalyzer(a, ui.SyntaxRequest{}); e != nil {
		t.Fatal(e)
	}
	start := strings.Index(original, "한")
	end := start + len("한글")
	if e := d.Buffer.SelectBytes(end, start); e != nil {
		t.Fatal(e)
	}
	lo, hi := d.Buffer.SelectionBytes()
	if lo != start || hi != end {
		t.Fatal(lo, hi)
	}
	if e := d.Buffer.SelectBytes(start+1, end); e == nil {
		t.Fatal("split byte selected")
	}
	event, e := d.Buffer.ReplaceBytes(start, end, "가\r\n나")
	if e != nil || event.Kind != "change" {
		t.Fatal(e)
	}
	if e = d.RefreshSyntax(); e != nil {
		t.Fatal(e)
	}
	if !strings.Contains(d.Buffer.Text(), "가\r\n나") {
		t.Fatal("literal edit normalized")
	}
	d.Handle("undo", "")
	if d.Buffer.Text() != original {
		t.Fatal("byte undo")
	}
	d.Handle("redo", "")
	if !strings.Contains(d.Buffer.Text(), "가\r\n나") {
		t.Fatal("byte redo")
	}
	d.Buffer.State.ReadOnly = true
	raw := d.Buffer.Text()
	d.Buffer.ReplaceBytes(0, 0, "bad")
	if d.Buffer.Text() != raw {
		t.Fatal("readonly byte edit")
	}
	d.Buffer.Secret = true
	d.SetSearchMatches([]ui.TextRange{{Start: 0, End: 1}})
	d.RefreshSyntax()
	if len(d.Syntax) != 0 {
		t.Fatal("secret analysis")
	}
	if strings.Contains(fmt.Sprintf("%+v", d), "SELECT") {
		t.Fatal("secret diagnostic")
	}
	if strings.Contains(fmt.Sprintf("%#v", *d), "SELECT") {
		t.Fatal("secret value diagnostic")
	}
}
func TestSQLSyntaxRendering(t *testing.T) {
	for _, theme := range []string{"dark", "light", "blackwhite"} {
		for _, profile := range []string{"8", "16", "256", "truecolor"} {
			tokens, _ := ui.CandidateTokens()
			raw, _ := tokens.Palette(theme, profile)
			palette, _ := ui.Resolve(raw)
			doc := ui.NewEditor("SELECT '한글😀' FROM 표 WHERE id=:id")
			doc.LineNumbers = false
			doc.Buffer.Select(0, 0)
			doc.SetSyntaxAnalyzer(ui.NewSQLAnalyzer(), ui.SyntaxRequest{})
			screen := ui.NewSimulationScreen("UTF-8")
			screen.Init()
			screen.SetSize(40, 5)
			view, e := ui.NewEditorView(doc, palette, nil)
			if e != nil {
				t.Fatal(e)
			}
			view.SetRect(0, 0, 40, 5)
			view.Draw(screen)
			screen.Show()
			cells, _, _ := screen.GetContents()
			_, bg, _ := cells[1].Style.Decompose()
			if bg != palette["surface"].BG || cells[0].Runes[0] != 'S' {
				t.Fatal("syntax surface/output")
			}
			doc.SetSearchMatches([]ui.TextRange{{Start: 0, End: 6}})
			view.Draw(screen)
			screen.Show()
			cells, _, _ = screen.GetContents()
			_, bg, _ = cells[1].Style.Decompose()
			if bg != palette["edited"].BG {
				t.Fatal("search lost to syntax")
			}
			doc.Buffer.Select(0, 6)
			view.Draw(screen)
			screen.Show()
			cells, _, _ = screen.GetContents()
			_, bg, _ = cells[1].Style.Decompose()
			if bg != palette["selection"].BG {
				t.Fatal("selection lost to syntax")
			}
			doc.Buffer.State.Disabled = true
			view.Draw(screen)
			screen.Show()
			cells, _, _ = screen.GetContents()
			fg, _, _ := cells[1].Style.Decompose()
			want, _ := ui.TextOnSurface(palette, "disabled", "surface")
			wfg, _, _ := want.Decompose()
			if fg != wfg {
				t.Fatal("disabled lost to syntax")
			}
			screen.Fini()
		}
	}
}
func BenchmarkSQLSyntaxLongDocument(b *testing.B) {
	source := strings.Repeat("SELECT NVL(:id, '한글😀'), 1e3 FROM 표; -- comment\n", 10000)
	a := ui.NewSQLAnalyzer()
	b.SetBytes(int64(len(source)))
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		if _, e := a.AnalyzeSyntax(source, ui.SyntaxRequest{}); e != nil {
			b.Fatal(e)
		}
	}
}

func TestSQLLongDocumentAndLegacyColors(t *testing.T) {
	source := strings.Repeat("SELECT NVL(:id, '한글😀'), 1e3 FROM 표; -- comment\n", 10000)
	doc := ui.NewEditor(source)
	if e := doc.SetSyntaxAnalyzer(ui.NewSQLAnalyzer(), ui.SyntaxRequest{}); e != nil {
		t.Fatal(e)
	}
	if len(doc.Syntax) < 100000 {
		t.Fatal("missing large-document analysis")
	}
	doc.ScrollY = 9990
	doc.Buffer.Select(0, 0)
	doc.Layout(80, 20)
	if doc.Buffer.Text() != source {
		t.Fatal("analysis changed original")
	}
	kinds := map[string]ui.SyntaxKind{"keyword": ui.SyntaxKeyword, "function": ui.SyntaxFunction, "type": ui.SyntaxType, "string": ui.SyntaxString, "number": ui.SyntaxNumber, "comment": ui.SyntaxComment, "parameter": ui.SyntaxParameter}
	for _, theme := range []string{"dark", "light", "blackwhite"} {
		for _, profile := range []string{"8", "16", "256", "truecolor"} {
			styles, e := ui.NewStyles(theme, profile)
			if e != nil {
				t.Fatal(e)
			}
			hook := ui.SyntaxStyleFunc(styles)
			base := styles.EditorStyle()
			for role, kind := range kinds {
				if hook("syntax."+role, base) != styles.SyntaxStyle(kind, base) {
					t.Fatal("legacy syntax colors changed")
				}
			}
		}
	}
}
