// Database-free Oracle SQL highlighting using one Tuivory import.
package syntax

import (
	"flag"
	"fmt"
	ui "github.com/leechis7/tuivory/go"
	"log"
)

func Run(args []string) {
	flags := flag.NewFlagSet("syntax", flag.ExitOnError)
	lang := flags.String("lang", "ko", "ko/en")
	theme := flags.String("theme", "dark", "dark/light/blackwhite")
	profile := flags.String("colors", "256", "8/16/256/truecolor")
	ascii := flags.Bool("ascii", false, "ASCII decorations")
	_ = flags.Parse(args)
	if *lang != "ko" && *lang != "en" {
		log.Fatal("invalid language")
	}
	tr := func(ko, en string) string {
		if *lang == "en" {
			return en
		}
		return ko
	}
	source := tr("-- Oracle SQL / PL/SQL 강조 예제\nSELECT NVL(:이름, q'[한글 😀 é]') AS \"결과\",\n       COUNT(*), 1.25e2 FROM 예제\nWHERE id = :id;\n\nBEGIN\n  NULL; -- SQL 실행은 앱이 결정합니다.\nEND;", "-- Oracle SQL / PL/SQL highlighting\nSELECT NVL(:name, q'[Unicode]') AS \"result\",\n       COUNT(*), 1.25e2 FROM example\nWHERE id = :id;\n\nBEGIN\n  NULL; -- The host decides whether to execute SQL.\nEND;")
	doc := ui.NewEditor(source)
	doc.Buffer.Select(0, 0)
	if err := doc.SetSyntaxAnalyzer(ui.NewSQLAnalyzer(), ui.SyntaxRequest{Language: "sql", Dialect: "oracle"}); err != nil {
		log.Fatal(err)
	}
	palette := func() ui.Palette {
		tokens, e := ui.CandidateTokens()
		if e != nil {
			log.Fatal(e)
		}
		raw, e := tokens.Palette(*theme, *profile)
		if e != nil {
			log.Fatal(e)
		}
		p, e := ui.Resolve(raw)
		if e != nil {
			log.Fatal(e)
		}
		return p
	}
	p := palette()
	status := tr("강조만 수행하며 DB에 연결하지 않습니다.", "Highlighting only; no database connection.")
	editor, _ := ui.NewEditorView(doc, p, func(e ui.TextEvent) { status = e.Kind })
	panel, _ := ui.NewPanelView(editor, p)
	panel.SetTitle(tr("SQL 문법 강조", "SQL syntax highlighting"))
	panel.ASCII = *ascii
	footer, _ := ui.NewRowsView(func(w, h int) []ui.ComponentLine {
		return []ui.ComponentLine{{Text: status, Role: "hint"}, {Text: tr("F2 테마 · F3 색상 · 선택/붙여넣기/Undo · Ctrl+Q 종료", "F2 theme / F3 colors / select/paste/undo / Ctrl+Q quit"), Role: "hint"}}
	}, p)
	root, _ := ui.NewColumn([]ui.ContainerChild{{Item: ui.LayoutItem{ID: "editor", Track: ui.Track{Weight: 1}}, Child: panel}, {Item: ui.LayoutItem{ID: "footer", Disabled: true, Track: ui.Track{Fixed: 2}}, Child: footer}}, p)
	app := ui.NewApplication()
	app.SetInputCapture(func(key *ui.EventKey) *ui.EventKey {
		switch key.Key() {
		case ui.KeyCtrlQ:
			app.Stop()
			return nil
		case ui.KeyCtrlC:
			return ui.NewEventKey(key.Key(), key.Rune(), key.Modifiers())
		case ui.KeyF2:
			if *theme == "dark" {
				*theme = "light"
			} else if *theme == "light" {
				*theme = "blackwhite"
			} else {
				*theme = "dark"
			}
		case ui.KeyF3:
			values := []string{"8", "16", "256", "truecolor"}
			for i, v := range values {
				if v == *profile {
					*profile = values[(i+1)%len(values)]
					break
				}
			}
		default:
			return key
		}
		p = palette()
		panel.SetPalette(p)
		editor.SetPalette(p)
		footer.SetPalette(p)
		root.SetPalette(p)
		status = fmt.Sprintf("%s / %s", *theme, *profile)
		return nil
	})
	if err := app.SetRoot(root, true).EnableMouse(true).EnablePaste(true).SetFocus(root).Run(); err != nil {
		log.Fatal(err)
	}
}
