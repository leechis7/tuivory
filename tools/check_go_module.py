#!/usr/bin/env python3
"""Verify that go/ works without the repository's shared design directory."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from check_static_elf import inspect

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--static-output', type=Path, help='also export a static x86_64 external test host')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='tuivory-go-module-') as temporary:
        base = Path(temporary)
        module = base / 'module'
        shutil.copytree(ROOT / 'go', module, ignore=shutil.ignore_patterns('bin', '__pycache__'))
        # No shared design/ directory is copied. All required runtime assets
        # must be inside the distributable Go module.
        env = dict(os.environ, GOWORK='off')
        subprocess.run(['go', 'test', './...'], cwd=module, env=env, check=True)
        consumer = base / 'consumer'
        consumer.mkdir()
        (consumer / 'go.mod').write_text(
            'module example.com/tuivory-isolated-consumer\n\ngo 1.24.0\n\n'
            'require github.com/leechis7/tuivory/go v0.0.0\n'
            'replace github.com/leechis7/tuivory/go => {}\n'.format(module))
        # Keep dependency checksum verification using the module's checked-in
        # sums, without requiring an unnecessary network lookup for known deps.
        shutil.copyfile(module / 'go.sum', consumer / 'go.sum')
        (consumer / 'consumer_test.go').write_text('''package consumer_test
import (
    "testing"
    "github.com/gdamore/tcell/v2"
    "github.com/leechis7/tuivory/go"
)
func TestIsolatedModule(t *testing.T) {
    controlState := tuivory.ControlState{ReadOnly:true,Invalid:true,Edited:true}
    if controlState.Visual().Editable || controlState.Visual().Role!="error" || controlState.Visual().Markers!="!*=" { t.Fatal("control states") }
    focus, err := tuivory.NewFocusStack("root",[]tuivory.FocusTarget{{ID:"open"}})
    if err != nil { t.Fatal(err) }
    if err:=focus.Open("dialog",[]tuivory.FocusTarget{{ID:"close"}},"",true); err!=nil { t.Fatal(err) }
    if !focus.Route("root").Blocked || focus.RequestClose().ID!="dialog" { t.Fatal("popup scope") }
    if err:=focus.Close("dialog");err!=nil || focus.Focused()!="open" { t.Fatal("focus restore") }
    form, formErr := tuivory.NewForm([]tuivory.FormField{{ID:"name",Kind:"text",Required:true}})
    if formErr!=nil || form.Handle("submit","").Kind!="invalid" { t.Fatal("external form") }
    form.Handle("insert","External")
    if form.Handle("submit","").Kind!="submit" { t.Fatal("external submit") }
    picker, pickerErr := tuivory.NewSearchPicker([]tuivory.ListItem{{ID:"rust",Label:"Rust"}})
    if pickerErr!=nil { t.Fatal(pickerErr) };picker.Handle("open","",4);picker.Handle("insert","Rust",4)
    if picker.Handle("activate","",4).ID!="rust" { t.Fatal("external picker") }
    gridRows,_:=tuivory.NewMemoryRows([]tuivory.GridRecord{{ID:"row",Cells:map[string]string{"name":"External"}}})
    grid,_:=tuivory.NewGrid([]tuivory.GridColumn{{ID:"name",Width:12,Editable:true}},gridRows)
    if grid.Handle("copy",4).Text!="External" || grid.Handle("activate",4).Kind!="edit" {t.Fatal("external grid")}
    gridOptions,_:=tuivory.GridPreset("data");if err:=grid.SetOptions(gridOptions);err!=nil{t.Fatal(err)}
    grid.SetCellInfo(func(r tuivory.GridRecord,c tuivory.GridColumn)tuivory.GridCellInfo{return tuivory.GridCellInfo{Display:"formatted",HasDisplay:true,Metadata:"TEXT"}})
    if !grid.SelectRange(tuivory.GridRange{AnchorRow:"row",EndRow:"row",AnchorColumn:"name",EndColumn:"name"})||grid.Handle("copy_range",4).Text!="External" {t.Fatal("external options/raw range")}
    grid.RequestFilter("old");oldRevision:=grid.Revision();grid.RequestFilter("new");if grid.ApplySource(oldRevision,gridRows){t.Fatal("stale source")}
    menu,menuErr:=tuivory.NewMenu([]tuivory.MenuItem{{ID:"root",Label:"Root"},{ID:"copy",Parent:"root",Label:"Copy",Mnemonic:"c",Icon:"◇",ASCIIIcon:"*"}});if menuErr!=nil{t.Fatal(menuErr)}
    menu.Open("root","editor");if e:=menu.Handle("mnemonic","c",4);e.Kind!="activate"||e.ReturnID!="editor"{t.Fatal("external menu caller")};menu.Open("root","editor")
    notices,_:=tuivory.NewNoticeQueue(2);_ = notices.Push(tuivory.Notice{ID:"err",Severity:"error",ExpiresAt:1})
    if len(notices.Visible(100))!=1 { t.Fatal("external notice lifetime") }
    operation:=tuivory.Progress{ID:"load",Status:"loading",Cancellable:true};if operation.RequestCancel().Kind!="cancel"{t.Fatal("external cancel")}
    spacing,spacingErr:=tuivory.ResolveSpacing(tuivory.DensityAuto,40);if spacingErr!=nil||spacing.Padding!=0{t.Fatal("external spacing")}
    layout,layoutErr:=tuivory.StackLayout([]tuivory.StackItem{{ID:"main",Min:10,Preferred:20,Weight:1}},30,1);if layoutErr!=nil||layout.Slots[0].Size!=30{t.Fatal("external stack")}
    if (tuivory.Chip{ID:"filter",Removable:true}).RequestRemove().Kind!="remove"{t.Fatal("external chip")}
    theme, err := tuivory.New("dark", "256")
    if err != nil { t.Fatal(err) }
    if theme.Styles.Profile() != "256" { t.Fatal("profile missing") }
    document, err := tuivory.CandidateTokens()
    if err != nil { t.Fatal(err) }
    palette, err := document.Palette("light", "16")
    if err != nil { t.Fatal(err) }
    if _, err := tuivory.Resolve(palette); err != nil { t.Fatal(err) }
    colors, _ := tuivory.Resolve(palette)
    if _,err:=tuivory.ControlStyle(colors,controlState,true);err!=nil { t.Fatal(err) }
    surfaceText, surfaceErr := tuivory.TextOnSurface(colors,"success","surface")
    fg,bg,_ := surfaceText.Decompose()
    if surfaceErr!=nil || fg!=colors["surface"].FG || bg!=colors["surface"].BG {t.Fatal("external surface style/contrast")}
    selectedStyle,_:=tuivory.ControlStyleOnSurface(colors,tuivory.ControlState{Selected:true},true,"surface")
    _,selectedBG,_:=selectedStyle.Decompose();if selectedBG!=colors["selection"].BG{t.Fatal("explicit background lost")}
    tree, err := tuivory.NewTree([]tuivory.TreeNode{{ID:"root",Name:"External"},{ID:"child",Parent:"root",Name:"Child"}})
    if err != nil { t.Fatal(err) }
    state := &tuivory.TreeState{}
    if tree.Handle(state,tuivory.TreeRight,4).Kind != "expand" { t.Fatal("tree expansion failed") }
    view, err := tuivory.NewTreeView(tree,state,colors)
    if err != nil { t.Fatal(err) }
    screen := tcell.NewSimulationScreen("UTF-8")
    if err := screen.Init(); err != nil { t.Fatal(err) }
    defer screen.Fini()
    screen.SetSize(30,6)
    safe := tuivory.WideSafeScreen(screen)
    screen.Put(2,2,"한",tcell.StyleDefault);screen.Put(9,2,"Z",tcell.StyleDefault);screen.Put(8,2,"界",tcell.StyleDefault);screen.Show()
    safe.Put(3,2,"|",tcell.StyleDefault);safe.Put(8,2,"|",tcell.StyleDefault)
    screen.Show();physical,cols,_:=screen.GetContents()
    if string(physical[2*cols+3].Bytes)!="|" || string(physical[2*cols+9].Bytes)!=" " {t.Fatal("wide overlay physical output")}
    screen.Put(2,3,"한",tcell.StyleDefault);screen.Put(7,3,"界",tcell.StyleDefault);screen.Show()
    tuivory.DimRegion(screen,tuivory.CellRect{X:3,Y:3,Width:5,Height:1});screen.Show()
    physical,cols,_=screen.GetContents()
    if string(physical[3*cols+2].Bytes)!=" " || string(physical[3*cols+8].Bytes)!=" " {t.Fatal("shadow boundary output")}

    gridView,gridErr:=tuivory.NewGridView(grid,colors,nil);if gridErr!=nil{t.Fatal(gridErr)}
    gridView.SetRect(0,0,30,6);gridView.Draw(screen);screen.Show()
    physical,cols,_=screen.GetContents();if string(physical[grid.Geometry(30,6).Gutter-1].Bytes)!="│"{t.Fatal("external grid physical header")}
    view.SetRect(0,0,30,6)
    view.Draw(screen)
    marker,_,_,_ := screen.GetContent(1,1)
    if marker != '>' { t.Fatal("external tree did not render") }
    tabs, err := tuivory.NewTabs([]tuivory.TabItem{{ID:"a",Title:"Overview"},{ID:"b",Title:"Draft",Edited:true,Closable:true}})
    if err != nil { t.Fatal(err) }
    tabState := &tuivory.TabState{}
    tabs.Handle(tabState,tuivory.TabNext)
    if tabState.Active != "a" || tabState.Focused != "b" { t.Fatal("tab focus activated content") }
    tabView, err := tuivory.NewTabView(tabs,tabState,colors)
    if err != nil { t.Fatal(err) }
    tabView.SetRect(0,0,30,1)
    tabView.Draw(screen)
    panel, err := tuivory.NewPanelView(view,colors)
    if err != nil { t.Fatal(err) }
    panel.SetRect(0,0,30,6)
    panel.Draw(screen)
    if layout := (tuivory.SplitSpec{FirstMin:5,SecondMin:5}).Layout(&tuivory.SplitState{Preferred:8},30); layout.First!=8 { t.Fatal(layout) }
    crumbs, err := tuivory.NewBreadcrumbView([]tuivory.PathItem{{ID:"root",Label:"Workspace"},{ID:"current",Label:"Current"}},colors)
    if err != nil { t.Fatal(err) }
    crumbs.SetRect(0,0,20,1); crumbs.Draw(screen)
    status, err := tuivory.NewStatusView([]tuivory.StatusItem{{ID:"e",Text:"Failure",Role:"error",Priority:10}},colors)
    if err != nil { t.Fatal(err) }
    status.SetRect(0,0,20,1); status.Draw(screen)
    menuView,menuErr:=tuivory.NewMenuView(menu,colors,true,nil);if menuErr!=nil{t.Fatal(menuErr)};popup,menuErr:=tuivory.NewPanelView(menuView,colors);if menuErr!=nil{t.Fatal(menuErr)};popup.ASCII=true;popup.SetRect(0,0,30,6);popup.Draw(screen);screen.Show();physical,cols,_=screen.GetContents();if string(physical[0].Bytes)!="+"||string(physical[2*cols+2].Bytes)!=">"{t.Fatal("external menu physical output")}
    if _,err:=tuivory.NewMenuBarView(menu,colors,nil);err!=nil{t.Fatal(err)}
}
''')
        subprocess.run(['go', 'test', '-mod=mod', './...'], cwd=consumer, env=env, check=True)
        if args.static_output:
            output = args.static_output.resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(['go', 'test', '-c', '-mod=mod', '-o', str(output)], cwd=consumer,
                           env=dict(env, CGO_ENABLED='0', GOOS='linux', GOARCH='amd64'), check=True)
            inspect(output, 'x86_64')
    print('Go module and single-import consumer passed without repository design assets.')


if __name__ == '__main__':
    main()
