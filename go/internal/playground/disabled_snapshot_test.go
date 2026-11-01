package playground

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/gdamore/tcell/v2"
	"github.com/leechis7/tuivory/go"
	"github.com/rivo/tview"
)

// The matrix uses actual Go widget rendering and copies the playground token
// sample from the post-Show buffer. SVG Dim is a documented visual approximation.
func TestDisabledSnapshots(t *testing.T) {
	dir := os.Getenv("TUIVORY_DISABLED_SNAPSHOT_DIR")
	if dir == "" {
		t.Skip("set TUIVORY_DISABLED_SNAPSHOT_DIR for the Go disabled matrix")
	}
	if err := os.MkdirAll(dir, 0755); err != nil {
		t.Fatal(err)
	}
	for _, lang := range []string{"ko", "en"} {
		matrix := tcell.NewSimulationScreen("UTF-8")
		if err := matrix.Init(); err != nil {
			t.Fatal(err)
		}
		matrix.SetSize(120, 28)
		u, source := testUIOptions(t, Options{Lang: lang})
		tr := func(ko, en string) string {
			if lang == "en" {
				return en
			}
			return ko
		}
		for row, profile := range profileNames[1:] {
			for column, theme := range themeNames {
				styler, _ := tuivory.New(theme, profile)
				x, y := column*40, row*7
				style := styler.Styles.DisabledStyle()
				_, bg, _ := style.Decompose()
				for dy := 0; dy < 7; dy++ {
					for dx := 0; dx < 40; dx++ {
						matrix.SetContent(x+dx, y+dy, ' ', nil, tcell.StyleDefault.Background(bg))
					}
				}
				tview.Print(matrix, theme+" / "+profile, x+1, y, 38, tview.AlignLeft, styler.Styles.Text)
				for i, disabled := range []bool{false, true} {
					label := tr("활성 버튼", "Enabled button")
					if disabled {
						label = tr("비활성 버튼", "Disabled button")
					}
					button := tview.NewButton(label).SetDisabled(disabled)
					styler.Button(button)
					button.SetRect(x+1, y+1+i, 36, 1)
					button.Draw(matrix)
				}
				drop := tview.NewDropDown().SetOptions([]string{tr("비활성 선택값", "Disabled choice")}, nil).SetCurrentOption(0).SetFieldWidth(36)
				drop.SetDisabled(true)
				styler.DropDown(drop)
				drop.SetRect(x+1, y+3, 36, 1)
				drop.Draw(matrix)
				tview.Print(matrix, tr("토큰 표 견본:", "Token table sample:"), x+1, y+4, 38, tview.AlignLeft, styler.Styles.Text)
				u.theme.SetCurrentOption(column)
				u.profile.SetCurrentOption(row + 1)
				u.showPage(1)
				drawUI(u, source)
				for i, role := range roleNames {
					if role != "disabled" {
						continue
					}
					sx, sy, w := u.tokens.GetCell(i+1, 3).GetLastPosition()
					cells, cols, _ := source.GetContents()
					for dx := 0; dx < min(w, 36); dx++ {
						cell := cells[sy*cols+sx+dx]
						if len(cell.Runes) > 0 {
							matrix.SetContent(x+1+dx, y+5, cell.Runes[0], cell.Runes[1:], cell.Style)
						}
					}
				}
			}
		}
		matrix.Show()
		suffix := ""
		if lang == "en" {
			suffix = "-en"
		}
		if err := writeSVG(filepath.Join(dir, "go-disabled-states"+suffix+".svg"), matrix); err != nil {
			t.Fatal(err)
		}
		matrix.Fini()
	}
}
