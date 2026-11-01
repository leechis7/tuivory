package tuivory

import "testing"

func TestComparisonHeadersAndSeparatorsRemainVisible(t *testing.T) {
	for _, theme := range []string{"dark", "light", "blackwhite"} {
		for _, profile := range []string{"8", "16", "256", "truecolor"} {
			t.Run(theme+"/"+profile, func(t *testing.T) {
				styler, err := New(theme, profile)
				if err != nil {
					t.Fatal(err)
				}
				screen := NewSimulationScreen("UTF-8")
				if err := screen.Init(); err != nil {
					t.Fatal(err)
				}
				t.Cleanup(screen.Fini)
				screen.SetSize(70, 12)
				table := NewTable().SetSeparator('│').SetSelectable(true, true)
				for row, cells := range [][]string{{"한글 항목", "Go", "Rust"}, {"전체 선택", "Ctrl+A", "Ctrl+A"}, {"구분", "공통", "공통"}} {
					for col, text := range cells {
						table.SetCell(row, col, NewTableCell(text))
					}
				}
				table.SetRect(2, 1, 60, 8)
				for _, selected := range [][2]int{{1, 1}, {1, 2}, {1, 1}} {
					table.Select(selected[0], selected[1])
					styler.Comparison(table, 1, func(row int) bool { return row == 2 })
					table.Draw(WideSafeScreen(screen))
					screen.Show()
					cells, _, _ := screen.GetContents()
					dividers := 0
					for _, cell := range cells {
						if string(cell.Runes) != "│" {
							continue
						}
						dividers++
						fg, bg, _ := cell.Style.Decompose()
						if ratio := surfaceContrast(fg, bg); ratio < 3 {
							t.Errorf("divider reference contrast %.3f < 3:1 (%v/%v)", ratio, fg, bg)
						}
					}
					if dividers < 6 {
						t.Fatalf("missing dividers: %d", dividers)
					}
					screen.Sync()
				}
				for _, current := range []bool{false, true} {
					fg, bg, _ := styler.Styles.ComparisonHeaderStyle(current).Decompose()
					if ratio := surfaceContrast(fg, bg); ratio < 4.5 {
						t.Errorf("header contrast %.3f < 4.5:1", ratio)
					}
				}
			})
		}
	}
}
