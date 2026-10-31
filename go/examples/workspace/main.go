// A host application connecting public components without database logic.
package main

import (
	"flag"
	"fmt"
	ui "github.com/leechis7/tuivory/go"

	"log"
	"strings"
)

func main() {
	lang := flag.String("lang", "ko", "ko or en")
	theme := flag.String("theme", "dark", "theme")
	profile := flag.String("colors", "256", "8,16,256,truecolor")
	layout := flag.String("layout", "columns", "host layout: columns/rows")
	focusOrder := flag.String("focus-order", "tabs,tree,content", "host Tab order: permutation of tabs,tree,content")
	quitKey := flag.String("quit-key", "ctrl-q", "host quit shortcut: ctrl-q/ctrl-x")
	ascii := flag.Bool("ascii", false, "ordinary ASCII borders/icons")
	flag.Parse()
	if *lang != "ko" && *lang != "en" {
		log.Fatal("--lang requires ko or en")
	}
	text := func(ko, en string) string {
		if *lang == "en" {
			return en
		}
		return ko
	}
	// These choices belong to this example app, not the component package.
	if *layout != "columns" && *layout != "rows" {
		log.Fatal("--layout requires columns or rows")
	}
	if *quitKey != "ctrl-q" && *quitKey != "ctrl-x" {
		log.Fatal("--quit-key requires ctrl-q or ctrl-x")
	}
	order := strings.Split(*focusOrder, ",")
	seen := map[string]bool{}
	for _, name := range order {
		if (name != "tabs" && name != "tree" && name != "content") || seen[name] {
			log.Fatal("--focus-order requires tabs,tree,content exactly once")
		}
		seen[name] = true
	}
	if len(order) != 3 {
		log.Fatal("--focus-order requires tabs,tree,content exactly once")
	}
	quit := ui.KeyCtrlQ
	quitLabel := "Ctrl+Q"
	if *quitKey == "ctrl-x" {
		quit = ui.KeyCtrlX
		quitLabel = "Ctrl+X"
	}
	doc, _ := ui.CandidateTokens()
	palette := func() ui.Palette {
		raw, e := doc.Palette(*theme, *profile)
		if e != nil {
			log.Fatal(e)
		}
		p, e := ui.Resolve(raw)
		if e != nil {
			log.Fatal(e)
		}
		return p
	}
	nodes := []ui.TreeNode{{ID: "root", Name: text("프로젝트", "Project"), Icon: "◇", ASCIIIcon: "R"}, {ID: "src", Parent: "root", Name: text("예제", "Examples"), Icon: "□", ASCIIIcon: "D"}, {ID: "go", Parent: "src", Name: "Go", Secondary: text("공개 패키지", "Public package")}, {ID: "rust", Parent: "src", Name: "Rust", Secondary: text("공개 crate", "Public crate")}, {ID: "notes", Parent: "root", Name: text("긴 한글 경로와 이름 예시", "A long path and name example"), Secondary: "[red] literal"}}
	tree, _ := ui.NewTree(nodes)
	treeState := &ui.TreeState{Expanded: map[string]bool{"root": true, "src": true}}
	items := []ui.TabItem{{ID: "overview", Title: text("개요", "Overview")}, {ID: "draft", Title: text("변경된 한글 문서와 긴 제목", "Edited document with a long title"), Edited: true, Closable: true}, {ID: "logs", Title: text("로그", "Logs"), Closable: true}, {ID: "disabled", Title: text("비활성", "Disabled"), Disabled: true}}
	tabs, _ := ui.NewTabs(items)
	tabState := &ui.TabState{}
	tabView, err := ui.NewTabView(tabs, tabState, palette())
	if err != nil {
		log.Fatal(err)
	}
	treeView, _ := ui.NewTreeView(tree, treeState, palette())
	treeView.SetBorder(false)
	content := ui.NewWidgetTextView().SetDynamicColors(false).SetScrollable(true)
	left, _ := ui.NewPanelView(treeView, palette())
	right, _ := ui.NewPanelView(content, palette())
	left.SetTitle(text("탐색", "Explorer"))
	right.SetTitle(text("내용", "Content"))
	columns := &ui.SplitState{Preferred: 32}
	rows := &ui.SplitState{Preferred: 8}
	split, _ := ui.NewSplitView(left, right, columns, ui.SplitSpec{FirstMin: 20, SecondMin: 24}, palette())
	if *layout == "rows" {
		split.Rows = true
		split.State = rows
		split.Spec = ui.SplitSpec{FirstMin: 4, SecondMin: 4}
	}
	path, _ := ui.NewBreadcrumbView([]ui.PathItem{{ID: "root", Label: text("작업 공간", "Workspace")}, {ID: "project", Label: "Tuivory"}, {ID: "folder", Label: text("공통 컴포넌트 예제", "Shared component examples")}, {ID: "current", Label: text("현재 문서.md", "Current document.md")}}, palette())
	status, _ := ui.NewStatusView(nil, palette())
	header := ui.NewWidgetTextView().SetDynamicColors(false)
	hints := ui.NewWidgetTextView().SetDynamicColors(false)
	app := ui.NewApplication()
	message := text("상태·포커스·분할 크기는 테마와 독립적입니다.", "State, focus and split sizes are independent of the theme.")
	var refresh func()
	refresh = func() {
		p := palette()
		for _, e := range []error{tabView.SetPalette(p), treeView.SetPalette(p), left.SetPalette(p), right.SetPalette(p), split.SetPalette(p), path.SetPalette(p), status.SetPalette(p)} {
			if e != nil {
				log.Fatal(e)
			}
		}
		treeView.ASCII = *ascii
		left.ASCII = *ascii
		right.ASCII = *ascii
		split.ASCII = *ascii
		header.SetText(fmt.Sprintf("TUIVORY Workspace · %s / %s · %s", *theme, *profile, text("이름·보조 설명·개수", "Name · Secondary · Count"))).SetTextColor(p["body"].FG).SetBackgroundColor(p["surface"].BG)
		contentText := fmt.Sprintf("%s: %s\n\n%s\n\n%s\n\n%s", text("활성 탭", "Active tab"), tabState.Active, text("DB 없는 공통 컴포넌트 견본", "Database-free shared component example"), text("탭에서 방향키는 포커스만 옮기고 Enter는 활성화합니다.\n수정된 문서의 닫기 요청은 앱이 보류합니다.", "Tab arrows move focus; Enter activates.\nThe host retains edited documents on close requests."), text("Ctrl+방향키 또는 분할선 드래그로 크기를 조절하세요.\n좁은 화면에서는 마지막으로 선택한 패널만 보입니다.\n테마 변경 후에도 트리·탭·분할 상태를 유지합니다.", "Resize with Ctrl+arrows or drag the divider.\nNarrow screens show the last selected panel.\nTree, tab, and split state survive theme changes."))
		if content.GetText(false) != contentText {
			content.SetText(contentText)
		}
		content.SetTextColor(p["body"].FG).SetBackgroundColor(p["surface"].BG)
		if e := status.SetItems([]ui.StatusItem{{ID: "message", Text: message, Role: "info", Priority: 100}, {ID: "changed", Text: text("변경 표시 * / 닫기 x", "Edited * / close x"), Role: "edited", Priority: 20}, {ID: "help", Text: "F1 Help", Role: "hint", Priority: 1}}); e != nil {
			log.Fatal(e)
		}
		hints.SetText(text("Tab 이동 · F2 테마 · F3 색상 · F4 ASCII · F5 변경 · F6 분할 방향 · "+quitLabel+" 종료", "Tab focus · F2 theme · F3 colors · F4 ASCII · F5 edited · F6 split axis · "+quitLabel+" quit")).SetTextColor(p["hint"].FG).SetBackgroundColor(p["surface"].BG)
	}
	tabView.OnEvent = func(event ui.TabEvent) {
		message = fmt.Sprintf("%s: %s", event.Kind, event.ID)
		if event.Kind == "close" {
			for i, item := range items {
				if item.ID == event.ID {
					if item.Edited {
						message = text("변경된 문서: 앱이 닫기를 보류했습니다.", "Edited document: the host retained the tab.")
					} else {
						items = append(items[:i], items[i+1:]...)
						tabs, _ = ui.NewTabs(items)
						if e := tabView.SetTabs(tabs); e != nil {
							log.Fatal(e)
						}
					}
					break
				}
			}
		}
		refresh()
	}
	treeView.OnEvent = func(event ui.TreeEvent) { message = fmt.Sprintf("%s: %s", event.Kind, event.ID); refresh() }
	path.OnNavigate = func(id string) {
		message = fmt.Sprintf("%s: %s", text("경로 이동 요청", "Navigation request"), id)
		refresh()
	}
	root := ui.NewFlex().SetDirection(ui.FlexRow).AddItem(header, 1, 0, false).AddItem(path, 1, 0, false).AddItem(tabView, 1, 0, true).AddItem(split, 0, 1, false).AddItem(status, 1, 0, false).AddItem(hints, 1, 0, false)
	// The host supplies screen composition, cross-component focus, and global keys.
	controls := map[string]ui.Primitive{"tabs": tabView, "tree": treeView, "content": content}
	focus := []ui.Primitive{controls[order[0]], controls[order[1]], controls[order[2]]}
	split.ActiveSecond = focus[0] == content
	cycle := func(value *string, values []string) {
		for i, s := range values {
			if *value == s {
				*value = values[(i+1)%len(values)]
				return
			}
		}
	}
	app.SetInputCapture(func(e *ui.EventKey) *ui.EventKey {
		if split.ResizeKey(e) {
			return nil
		}
		switch e.Key() {
		case quit:
			app.Stop()
			return nil
		case ui.KeyTab, ui.KeyBacktab:
			current := 0
			for i, p := range focus {
				if p.HasFocus() {
					current = i
				}
			}
			delta := 1
			if e.Key() == ui.KeyBacktab {
				delta = 2
			}
			next := (current + delta) % 3
			if focus[next] != tabView {
				split.ActiveSecond = focus[next] == content
			}
			app.SetFocus(focus[next])
			return nil
		case ui.KeyF1:
			message = text("탭: ←/→·Enter·x / 트리: 방향키·Space·Enter / Ctrl+방향키 크기 조절", "Tabs: Left/Right, Enter, x / Tree: arrows, Space, Enter / Ctrl+arrows resize")
			refresh()
			return nil
		case ui.KeyF2:
			cycle(theme, []string{"dark", "light", "blackwhite"})
			refresh()
			return nil
		case ui.KeyF3:
			cycle(profile, []string{"8", "16", "256", "truecolor"})
			refresh()
			return nil
		case ui.KeyF4:
			*ascii = !*ascii
			refresh()
			return nil
		case ui.KeyF5:
			for i := range items {
				if items[i].ID == tabState.Active {
					items[i].Edited = !items[i].Edited
				}
			}
			tabs, _ = ui.NewTabs(items)
			_ = tabView.SetTabs(tabs)
			refresh()
			return nil
		case ui.KeyF6:
			split.Rows = !split.Rows
			if split.Rows {
				split.State = rows
				split.Spec = ui.SplitSpec{FirstMin: 4, SecondMin: 4}
			} else {
				split.State = columns
				split.Spec = ui.SplitSpec{FirstMin: 20, SecondMin: 24}
			}
			return nil
		}
		return e
	})
	tabs.Reconcile(tabState)
	refresh()
	if e := app.SetRoot(root, true).SetFocus(focus[0]).EnableMouse(true).Run(); e != nil {
		log.Fatal(e)
	}
}
