package tuivory_test

import (
	ui "github.com/leechis7/tuivory/go"
	"testing"
)

func TestSuppliedSyntaxAndSearchExpiration(t *testing.T) {
	doc := ui.NewEditor("SELECT 1")
	analysis, err := ui.NewSQLAnalyzer().AnalyzeSyntax(doc.Buffer.Text(), ui.SyntaxRequest{})
	if err != nil {
		t.Fatal(err)
	}
	if err = doc.SetSyntaxAnalysis(analysis); err != nil {
		t.Fatal(err)
	}
	doc.SetSearchMatches([]ui.TextRange{{Start: 0, End: 6}})
	doc.Buffer.Select(0, 0)
	rows := doc.Layout(40, 3)
	found := false
	for _, span := range rows[0].Spans {
		if span.Start == 2 && span.Role == "edited" {
			found = true
		}
	}
	if !found {
		t.Fatal("search precedence")
	}
	doc.Handle("insert", "X")
	if len(doc.Syntax) != 0 {
		t.Fatal("supplied syntax stale after edit")
	}
	rows = doc.Layout(40, 3)
	for _, span := range rows[0].Spans {
		if span.Role == "edited" {
			t.Fatal("search did not expire")
		}
	}
	if err = doc.SetSyntaxAnalysis(analysis); err == nil {
		t.Fatal("stale supplied result accepted")
	}
	if err = doc.SetSearchMatches([]ui.TextRange{{Start: 10, End: 9}}); err == nil {
		t.Fatal("invalid search accepted")
	}
}
